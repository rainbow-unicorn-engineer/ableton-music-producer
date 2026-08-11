"""Unit tests for XLNT Studio's own tools: param_dump, the UDP sweep
smoke test, and the vendored als injectors' pure functions.

These run anywhere — no Ableton needed. The TCP test spins up a fake
Remote Script server on a random localhost port.
"""
import gzip
import json
import os
import socket
import sys
import threading

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools import param_dump  # noqa: E402
from tools import als_warp_injector as warp  # noqa: E402
from udp.sweep_smoke_test import sweep_values, make_packet  # noqa: E402


# ---------------------------------------------------------------------------
# param_dump
# ---------------------------------------------------------------------------

FAKE_RESULT = {
    "device_name": "Serum 2",
    "device_class": "PluginDevice",
    "parameter_count": 3,
    "parameters": [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0,
         "display_value": "On", "is_enabled": True, "is_quantized": True,
         "value_items": ["Off", "On"]},
        {"index": 1, "name": "Filter Cutoff", "value": 0.4, "min": 0.0, "max": 1.0,
         "display_value": "412 Hz", "is_enabled": True, "is_quantized": False,
         "value_items": []},
        {"index": 2, "name": "Resonance", "value": 0.1, "min": 0.0, "max": 1.0,
         "display_value": "10%", "is_enabled": True, "is_quantized": False,
         "value_items": []},
    ],
}


class FakeRemoteScript:
    """Minimal stand-in for the AbletonMCP TCP listener."""

    def __init__(self, response=None):
        self.response = response or {"status": "success", "result": FAKE_RESULT}
        self.received = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("localhost", 0))
        self.sock.listen(1)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        conn, _ = self.sock.accept()
        with conn:
            self.received = json.loads(conn.recv(65536).decode("utf-8"))
            conn.sendall(json.dumps(self.response).encode("utf-8"))
        self.sock.close()


def test_param_dump_round_trip():
    server = FakeRemoteScript()
    result = param_dump.send_command(
        "get_device_parameters",
        {"track_index": 0, "device_index": 0, "show_all": True},
        port=server.port)
    server.thread.join(timeout=2)
    assert server.received["type"] == "get_device_parameters"
    assert server.received["params"]["show_all"] is True
    assert result["device_name"] == "Serum 2"


def test_param_dump_error_response():
    server = FakeRemoteScript(response={"status": "error", "message": "no such track"})
    with pytest.raises(RuntimeError, match="no such track"):
        param_dump.send_command("get_device_parameters", {}, port=server.port)


def test_format_dump_matches_plan_schema():
    dump = param_dump.format_dump(FAKE_RESULT)
    assert dump["parameter_count"] == 3
    cutoff = dump["parameters"][1]
    # the plan's required keys: index, name, min, max, current_value
    assert {"index", "name", "min", "max", "current_value"} <= set(cutoff)
    assert cutoff["current_value"] == 0.4
    assert cutoff["name"] == "Filter Cutoff"


def test_param_dump_cli_writes_json(tmp_path):
    server = FakeRemoteScript()
    rc = param_dump.main([
        "--track", "0", "--device", "0", "--name", "serum2",
        "--out-dir", str(tmp_path), "--port", str(server.port),
    ])
    assert rc == 0
    out = json.loads((tmp_path / "serum2.params.json").read_text())
    assert out["device_name"] == "Serum 2"
    assert out["parameters"][2]["name"] == "Resonance"


# ---------------------------------------------------------------------------
# UDP sweep smoke test (pure parts)
# ---------------------------------------------------------------------------

def test_sweep_values_shape():
    pts = list(sweep_values(duration_s=2.0, rate_hz=30, cycles=1.0))
    assert len(pts) == 61  # n_steps + 1
    values = [v for _, v in pts]
    assert all(0.0 <= v <= 1.0 for v in values)
    assert values[0] == pytest.approx(0.0, abs=1e-6)   # starts at bottom
    assert values[-1] == pytest.approx(0.0, abs=1e-6)  # full cycle returns
    assert max(values) == pytest.approx(1.0, abs=1e-3)  # reaches the top


def test_udp_packet_format():
    pkt = json.loads(make_packet(1, 2, 3, 0.75).decode("utf-8"))
    assert pkt["type"] == "set_device_parameter"
    assert pkt["params"] == {"track_index": 1, "device_index": 2,
                             "parameter_index": 3, "value": 0.75}


# ---------------------------------------------------------------------------
# als injectors (vendored) — pure-function sanity checks
# ---------------------------------------------------------------------------

MINIMAL_ALS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton MajorVersion="5" MinorVersion="12.0_12049">
  <LiveSet>
    <Tracks>
      <AudioTrack Id="10">
        <Name><EffectiveName Value="Vocals" /></Name>
        <DeviceChain>
          <MainSequencer>
            <Sample>
              <ArrangerAutomation>
                <Events>
                  <AudioClip Id="0" Time="8">
                    <CurrentStart Value="8" />
                    <CurrentEnd Value="16" />
                    <Name Value="vox_take3" />
                    <Loop><LoopStart Value="0" /></Loop>
                    <WarpMarkers>
                      <WarpMarker Id="1" SecTime="0" BeatTime="0" />
                      <WarpMarker Id="2" SecTime="1" BeatTime="2" />
                    </WarpMarkers>
                  </AudioClip>
                </Events>
              </ArrangerAutomation>
            </Sample>
          </MainSequencer>
        </DeviceChain>
      </AudioTrack>
    </Tracks>
  </LiveSet>
</Ableton>
"""


def test_als_gzip_round_trip(tmp_path):
    als = tmp_path / "test.als"
    with gzip.open(als, "wt", encoding="utf-8") as fh:
        fh.write(MINIMAL_ALS_XML)
    xml = warp.decompress_als(str(als))
    assert "<Ableton" in xml and "vox_take3" in xml
    out = tmp_path / "out.als"
    warp.compress_als(xml, str(out))
    with gzip.open(out, "rt", encoding="utf-8") as fh:
        assert fh.read() == xml


def test_find_audio_clips_and_clip_info():
    import xml.etree.ElementTree as ET
    root = ET.fromstring(MINIMAL_ALS_XML)
    clips = warp.find_audio_clips(root, "vocal")
    assert len(clips) == 1
    info = warp.get_clip_info(clips[0])
    assert info["name"] == "vox_take3"
    assert info["start"] == 8.0 and info["end"] == 16.0
    assert info["length"] == 8.0


def test_generate_warp_marker_xml():
    import xml.etree.ElementTree as ET
    root = ET.fromstring(MINIMAL_ALS_XML)
    clip = warp.find_audio_clips(root, "vocal")[0]
    info = warp.get_clip_info(clip)
    markers = [
        {"original_beat": 8.0, "target_beat": 8.0, "original_seconds": 0.0},
        {"original_beat": 9.0, "target_beat": 9.05, "original_seconds": 0.68},
    ]
    xml = warp.generate_warp_marker_xml(markers, info, bpm=88.0)
    assert "WarpMarker" in xml
    assert 'SecTime="0' in xml
