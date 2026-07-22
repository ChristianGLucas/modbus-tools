from gen.messages_pb2 import EncodeRtuFrameInput, ModbusFrame
from nodes.encode_rtu_frame import encode_rtu_frame
from nodes._test_helpers import FakeAxiomContext

# Same classic Modbus reference-guide vectors as decode_rtu_frame_test.py —
# used here as an independent, from-a-published-reference oracle (not just a
# round trip through our own decoder).
_REQUEST = bytes.fromhex("1103006B00037687")
_RESPONSE = bytes.fromhex("110306022B00000064C8BA")


def test_encode_rtu_request_matches_known_vector():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, address=0x6B, count=3)
    result = encode_rtu_frame(ax, EncodeRtuFrameInput(frame=frame, is_response=False))
    assert result.error == ""
    assert result.data == _REQUEST


def test_encode_rtu_response_matches_known_vector():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, registers=[555, 0, 100])
    result = encode_rtu_frame(ax, EncodeRtuFrameInput(frame=frame, is_response=True))
    assert result.error == ""
    assert result.data == _RESPONSE


def test_encode_rtu_exception_response():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, is_exception=True, exception_code=2)
    result = encode_rtu_frame(ax, EncodeRtuFrameInput(frame=frame, is_response=True))
    assert result.error == ""
    assert result.data[0] == 0x11
    assert result.data[1] == 0x83
    assert result.data[2] == 2


def test_encode_rtu_out_of_range_address_is_structured_error():
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=17, address=70000, count=3)
    result = encode_rtu_frame(ax, EncodeRtuFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert result.data == b""


def test_encode_rtu_missing_frame_is_structured_error():
    ax = FakeAxiomContext()
    result = encode_rtu_frame(ax, EncodeRtuFrameInput())
    assert result.error != ""


def test_encode_rtu_device_id_out_of_range_is_structured_error_not_a_traceback():
    # A device_id > 255 used to escape the except clause (pymodbus raises
    # ModbusIOException, not ValueError) and leak a raw Python traceback into
    # the error field. Regression test for that.
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=300, address=0, count=1)
    result = encode_rtu_frame(ax, EncodeRtuFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert result.data == b""
    assert "Traceback" not in result.error
    assert "device_id" in result.error


def test_encode_rtu_negative_device_id_is_structured_error_not_a_traceback():
    # A negative device_id used to raise OverflowError from int.to_bytes(),
    # also escaping the except clause. Regression test for that.
    ax = FakeAxiomContext()
    frame = ModbusFrame(function_code=3, device_id=-1, address=0, count=1)
    result = encode_rtu_frame(ax, EncodeRtuFrameInput(frame=frame, is_response=False))
    assert result.error != ""
    assert "Traceback" not in result.error
