from gen.messages_pb2 import PackCoilsInput
from nodes.pack_coils import pack_coils
from nodes._test_helpers import FakeAxiomContext


def test_pack_coils_known_value():
    # LSB-first packing (the Modbus wire convention: coil 0 is bit 0 of byte 0):
    # bit0=1,bit1..6=0,bit7=1 -> byte = 0b10000001 = 0x81, hand-verified.
    ax = FakeAxiomContext()
    bits = [True, False, False, False, False, False, False, True]
    result = pack_coils(ax, PackCoilsInput(bits=bits))
    assert result.error == ""
    assert result.data == bytes([0x81])


def test_pack_coils_pads_partial_byte_with_zeros():
    ax = FakeAxiomContext()
    result = pack_coils(ax, PackCoilsInput(bits=[True, False, True]))
    # bits 0,2 set -> 0b00000101 = 0x05, padded to a full byte
    assert result.data == bytes([0x05])


def test_pack_coils_empty_is_empty():
    ax = FakeAxiomContext()
    result = pack_coils(ax, PackCoilsInput(bits=[]))
    assert result.error == ""
    assert result.data == b""


def test_pack_coils_multi_byte():
    ax = FakeAxiomContext()
    bits = [True] * 10  # 10 bits -> 2 bytes, second byte only has 2 real bits set
    result = pack_coils(ax, PackCoilsInput(bits=bits))
    assert result.data == bytes([0xFF, 0x03])
