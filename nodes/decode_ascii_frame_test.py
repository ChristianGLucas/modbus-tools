from gen.messages_pb2 import DecodeAsciiFrameInput
from nodes.decode_ascii_frame import decode_ascii_frame
from nodes._test_helpers import FakeAxiomContext, oracle_lrc

# Same classic Modbus example as the RTU tests, framed as Modbus ASCII:
# ':' + hex(device id 0x11, fc 0x03, address 0x006B, quantity 0x0003, LRC) + CRLF.
_PAYLOAD = bytes.fromhex("1103006B0003")
_LRC = oracle_lrc(_PAYLOAD)
assert _LRC == 0x7E  # independently known value for this exact classic vector
_REQUEST = ":1103006B00037E\r\n"


def test_decode_ascii_request_known_vector():
    ax = FakeAxiomContext()
    result = decode_ascii_frame(ax, DecodeAsciiFrameInput(frame=_REQUEST, is_response=False))
    assert result.error == ""
    assert result.lrc_valid is True
    assert result.frame.function_code == 3
    assert result.frame.device_id == 17
    assert result.frame.address == 0x6B
    assert result.frame.count == 3


def test_decode_ascii_lrc_mismatch_is_structured_error():
    tampered = ":1103006B00037F\r\n"  # last LRC byte flipped
    ax = FakeAxiomContext()
    result = decode_ascii_frame(ax, DecodeAsciiFrameInput(frame=tampered, is_response=False))
    assert result.lrc_valid is False
    assert result.error != ""


def test_decode_ascii_missing_colon_is_structured_error():
    ax = FakeAxiomContext()
    result = decode_ascii_frame(ax, DecodeAsciiFrameInput(frame="1103006B00037E\r\n", is_response=False))
    assert result.error != ""


def test_decode_ascii_invalid_hex_is_structured_error():
    ax = FakeAxiomContext()
    result = decode_ascii_frame(ax, DecodeAsciiFrameInput(frame=":ZZZZ\r\n", is_response=False))
    assert result.error != ""


def test_decode_ascii_tolerates_surrounding_whitespace():
    ax = FakeAxiomContext()
    result = decode_ascii_frame(ax, DecodeAsciiFrameInput(frame="  " + _REQUEST + "  ", is_response=False))
    assert result.error == ""
    assert result.frame.function_code == 3
