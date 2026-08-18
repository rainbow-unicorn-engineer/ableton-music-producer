"""Unit tests for the merged UDP performance plane in the full
AbletonMCP Remote Script (the TCP+UDP merge the roadmap called for).

Stubs Live's _Framework exactly like test_remote_script_helpers, builds
the script object without starting sockets, and drives
_process_udp_command directly — proving the fast path routes to
_set_device_parameter with the full script's (name-or-index, chain-aware)
signature, batches fan out per parameter, one bad batch entry can't kill
its neighbours, and unknown commands are ignored instead of crashing the
listener.
"""

import os
import sys
import types


class _StubControlSurface:
    def __init__(self, c_instance):
        pass

    def log_message(self, msg):
        pass


_framework = types.ModuleType("_Framework")
_cs_module = types.ModuleType("_Framework.ControlSurface")
_cs_module.ControlSurface = _StubControlSurface
sys.modules.setdefault("_Framework", _framework)
sys.modules.setdefault("_Framework.ControlSurface", _cs_module)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from remote_script.AbletonMCP import AbletonMCP, UDP_PORT  # noqa: E402


def make_script():
    """Bare script object: no __init__, no sockets, calls recorded."""
    script = AbletonMCP.__new__(AbletonMCP)
    script.running = True
    script.calls = []

    def fake_set(track_index, device_index, chain_index=None,
                 parameter_name=None, parameter_index=None, value=0.0):
        if parameter_index == 666:          # poison pill for batch test
            raise ValueError("boom")
        script.calls.append({
            "track": track_index, "device": device_index,
            "chain": chain_index, "name": parameter_name,
            "index": parameter_index, "value": value,
        })
        return {"parameter_name": parameter_name or str(parameter_index)}

    script._set_device_parameter = fake_set
    # schedule_message runs main-thread tasks; tests run them inline
    script.schedule_message = lambda delay, task: task()
    script.log_message = lambda msg: None
    return script


def test_udp_port_constant():
    assert UDP_PORT == 9878          # performance plane, per the plan


def test_single_parameter_move_routes_through_full_signature():
    s = make_script()
    s._process_udp_command({
        "type": "set_device_parameter",
        "params": {"track_index": 3, "device_index": 1,
                   "parameter_index": 7, "value": 0.42},
    })
    assert s.calls == [{"track": 3, "device": 1, "chain": None,
                        "name": None, "index": 7, "value": 0.42}]


def test_parameter_by_name_and_chain_pass_through():
    s = make_script()
    s._process_udp_command({
        "type": "set_device_parameter",
        "params": {"track_index": 0, "device_index": 2, "chain_index": 1,
                   "parameter_name": "Filter Freq", "value": 1.0},
    })
    call = s.calls[0]
    assert call["name"] == "Filter Freq" and call["chain"] == 1


def test_batch_fans_out_and_survives_bad_entry():
    s = make_script()
    s._process_udp_command({
        "type": "batch_set_device_parameters",
        "params": {"track_index": 1, "device_index": 0,
                   "parameter_indices": [2, 666, 5],
                   "values": [0.1, 0.2, 0.3]},
    })
    # 666 raised inside the loop; the others still landed
    assert [(c["index"], c["value"]) for c in s.calls] == [(2, 0.1), (5, 0.3)]


def test_unknown_command_is_ignored_not_fatal():
    s = make_script()
    s._process_udp_command({"type": "create_midi_track", "params": {}})
    assert s.calls == []


def test_schedule_message_assertion_falls_back_to_direct_call():
    """Outside Live's main loop schedule_message asserts — the fast path
    must run the task directly instead of dropping the knob move."""
    s = make_script()

    def asserting_schedule(delay, task):
        raise AssertionError("not on main thread")

    s.schedule_message = asserting_schedule
    s._process_udp_command({
        "type": "set_device_parameter",
        "params": {"track_index": 0, "device_index": 0,
                   "parameter_index": 1, "value": 0.5},
    })
    assert len(s.calls) == 1
