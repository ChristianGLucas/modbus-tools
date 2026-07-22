from gen.messages_pb2 import EncodeAsciiFrameInput, ModbusFrame
from nodes.encode_ascii_frame import encode_ascii_frame
from nodes._test_helpers import FakeAxiomContext

_REQUEST = ":1103006B00037E\r\n"


def test_encode_ascii_request_matches_known_vector():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, address=0x6B, count=3)
    result = encode_ascii_frame(ax, EncodeAsciiFrameInput(frame=frame, is_response=False))
    assert result.error == ""
    assert result.frame == _REQUEST


def test_encode_ascii_missing_frame_is_structured_error():
    ax = FakeAxiomContext()
    result = encode_ascii_frame(ax, EncodeAsciiFrameInput())
    assert result.error != ""


def test_encode_ascii_out_of_range_is_structured_error():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, address=99999, count=3)
    result = encode_ascii_frame(ax, EncodeAsciiFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert result.frame == ""
