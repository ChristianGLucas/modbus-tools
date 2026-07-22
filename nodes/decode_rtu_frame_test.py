from gen.messages_pb2 import DecodeRtuFrameInput
from nodes.decode_rtu_frame import decode_rtu_frame
from nodes._test_helpers import FakeAxiomContext, oracle_crc16_wire_bytes

# Classic Modbus reference-guide example (Modicon PI-MBUS-300): slave 17,
# ReadHoldingRegisters (fc 3), start address 0x006B, quantity 3.
_REQUEST = bytes.fromhex("1103006B00037687")
# Its response: byte count 6, registers 0x022B=555, 0x0000=0, 0x0064=100.
_RESPONSE = bytes.fromhex("110306022B00000064C8BA")


def test_decode_rtu_request_known_vector():
    ax = FakeAxiomContext()
    result = decode_rtu_frame(ax, DecodeRtuFrameInput(data=_REQUEST, is_response=False))
    assert result.error == ""
    assert result.crc_valid is True
    assert result.frame.function_code == 3
    assert result.frame.device_id == 17
    assert result.frame.address == 0x6B
    assert result.frame.count == 3


def test_decode_rtu_response_known_vector():
    ax = FakeAxiomContext()
    result = decode_rtu_frame(ax, DecodeRtuFrameInput(data=_RESPONSE, is_response=True))
    assert result.error == ""
    assert result.crc_valid is True
    assert result.frame.function_code == 3
    assert result.frame.device_id == 17
    assert list(result.frame.registers) == [555, 0, 100]
    assert result.frame.count == 3


def test_decode_rtu_crc_mismatch_is_independently_verified():
    # Flip the last CRC byte; oracle confirms the original was correct.
    assert oracle_crc16_wire_bytes(_REQUEST[:-2]) == _REQUEST[-2:]
    tampered = _REQUEST[:-1] + bytes([_REQUEST[-1] ^ 0xFF])
    ax = FakeAxiomContext()
    result = decode_rtu_frame(ax, DecodeRtuFrameInput(data=tampered, is_response=False))
    assert result.crc_valid is False
    assert result.error != ""
    assert not result.HasField("frame") or result.frame.function_code == 0


def test_decode_rtu_too_short_returns_structured_error():
    ax = FakeAxiomContext()
    result = decode_rtu_frame(ax, DecodeRtuFrameInput(data=b"\x01\x02", is_response=False))
    assert result.error != ""
    assert result.crc_valid is False


def test_decode_rtu_exception_response():
    # slave 17, fc 0x83 (fc3 | 0x80), exception code 2 (illegal data address)
    payload = bytes([0x11, 0x83, 0x02])
    frame = payload + oracle_crc16_wire_bytes(payload)
    ax = FakeAxiomContext()
    result = decode_rtu_frame(ax, DecodeRtuFrameInput(data=frame, is_response=True))
    assert result.error == ""
    assert result.crc_valid is True
    assert result.frame.is_exception is True
    assert result.frame.exception_code == 2
    assert result.frame.function_code == 3
