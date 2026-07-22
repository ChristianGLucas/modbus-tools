from gen.messages_pb2 import DecodeTcpFrameInput
from nodes.decode_tcp_frame import decode_tcp_frame
from nodes._test_helpers import FakeAxiomContext

# Hand-built MBAP ADU (transaction 1, unit 17, ReadHoldingRegisters fc3,
# address 0x006B, quantity 3): tid|pid|len|uid|pdu.
_REQUEST = bytes.fromhex("0001000000061103006b0003")
# Its response: byte count 6, registers 555, 0, 100.
_RESPONSE = bytes.fromhex("000100000009110306022b00000064")


def test_decode_tcp_request():
    ax = FakeAxiomContext()
    result = decode_tcp_frame(ax, DecodeTcpFrameInput(data=_REQUEST, is_response=False))
    assert result.error == ""
    assert result.frame.function_code == 3
    assert result.frame.device_id == 17
    assert result.frame.transaction_id == 1
    assert result.frame.address == 0x6B
    assert result.frame.count == 3


def test_decode_tcp_response():
    ax = FakeAxiomContext()
    result = decode_tcp_frame(ax, DecodeTcpFrameInput(data=_RESPONSE, is_response=True))
    assert result.error == ""
    assert result.frame.function_code == 3
    assert result.frame.transaction_id == 1
    assert list(result.frame.registers) == [555, 0, 100]


def test_decode_tcp_bad_protocol_id_is_structured_error():
    # protocol id must be 0x0000; set it to 0x0001.
    tampered = bytearray(_REQUEST)
    tampered[2] = 0x00
    tampered[3] = 0x01
    ax = FakeAxiomContext()
    result = decode_tcp_frame(ax, DecodeTcpFrameInput(data=bytes(tampered), is_response=False))
    assert result.error != ""
    assert result.frame.function_code == 0


def test_decode_tcp_too_short_is_structured_error():
    ax = FakeAxiomContext()
    result = decode_tcp_frame(ax, DecodeTcpFrameInput(data=b"\x00\x01\x00\x00", is_response=False))
    assert result.error != ""


def test_decode_tcp_length_mismatch_is_structured_error():
    # claim a length far larger than the bytes actually present.
    tampered = bytearray(_REQUEST)
    tampered[4] = 0x00
    tampered[5] = 0x20
    ax = FakeAxiomContext()
    result = decode_tcp_frame(ax, DecodeTcpFrameInput(data=bytes(tampered), is_response=False))
    assert result.error != ""
