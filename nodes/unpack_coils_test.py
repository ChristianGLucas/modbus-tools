from gen.messages_pb2 import UnpackCoilsInput
from nodes.unpack_coils import unpack_coils
from nodes._test_helpers import FakeAxiomContext


def test_unpack_coils_known_value():
    # inverse of test_pack_coils_known_value: 0x81 -> bit0=1, bits1-6=0, bit7=1
    ax = FakeAxiomContext()
    result = unpack_coils(ax, UnpackCoilsInput(data=bytes([0x81]), count=8))
    assert result.error == ""
    assert list(result.bits) == [True, False, False, False, False, False, False, True]


def test_unpack_coils_count_trims_padding():
    ax = FakeAxiomContext()
    result = unpack_coils(ax, UnpackCoilsInput(data=bytes([0x05]), count=3))
    assert list(result.bits) == [True, False, True]


def test_unpack_coils_count_zero_returns_all_bits():
    ax = FakeAxiomContext()
    result = unpack_coils(ax, UnpackCoilsInput(data=bytes([0x05]), count=0))
    assert len(result.bits) == 8


def test_unpack_coils_count_exceeds_available_is_structured_error():
    ax = FakeAxiomContext()
    result = unpack_coils(ax, UnpackCoilsInput(data=bytes([0x05]), count=100))
    assert result.error != ""


def test_pack_then_unpack_round_trips():
    from gen.messages_pb2 import PackCoilsInput
    from nodes.pack_coils import pack_coils

    ax = FakeAxiomContext()
    bits = [True, False, True, True, False, False, True, False, True, True, False]
    packed = pack_coils(ax, PackCoilsInput(bits=bits))
    unpacked = unpack_coils(ax, UnpackCoilsInput(data=packed.data, count=len(bits)))
    assert list(unpacked.bits) == bits
