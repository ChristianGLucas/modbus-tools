from gen.messages_pb2 import EncodeTcpFrameInput, ModbusFrame
from nodes.encode_tcp_frame import encode_tcp_frame
from nodes._test_helpers import FakeAxiomContext

_REQUEST = bytes.fromhex("0001000000061103006b0003")
_RESPONSE = bytes.fromhex("000100000009110306022b00000064")


def test_encode_tcp_request_matches_known_vector():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, transaction_id=1, address=0x6B, count=3)
    result = encode_tcp_frame(ax, EncodeTcpFrameInput(frame=frame, is_response=False))
    assert result.error == ""
    assert result.data == _REQUEST


def test_encode_tcp_response_matches_known_vector():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, transaction_id=1, registers=[555, 0, 100])
    result = encode_tcp_frame(ax, EncodeTcpFrameInput(frame=frame, is_response=True))
    assert result.error == ""
    assert result.data == _RESPONSE


def test_encode_tcp_out_of_range_count_is_structured_error():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, transaction_id=1, address=0, count=9999)
    result = encode_tcp_frame(ax, EncodeTcpFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert result.data == b""


def test_encode_tcp_missing_frame_is_structured_error():
    ax = FakeAxiomContext()
    result = encode_tcp_frame(ax, EncodeTcpFrameInput())
    assert result.error != ""


def test_encode_tcp_device_id_out_of_range_is_structured_error_not_a_traceback():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=300, transaction_id=1, address=0, count=1)
    result = encode_tcp_frame(ax, EncodeTcpFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert "Traceback" not in result.error


def test_encode_tcp_negative_device_id_is_structured_error_not_a_traceback():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=-1, transaction_id=1, address=0, count=1)
    result = encode_tcp_frame(ax, EncodeTcpFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert "Traceback" not in result.error
