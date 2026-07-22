from gen.messages_pb2 import EncodeRegisterBlockInput
from nodes.encode_register_block import encode_register_block
from nodes._test_helpers import FakeAxiomContext


def test_encode_uint16_known_value():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["4660"], value_type="uint16")
    )
    assert result.error == ""
    assert list(result.registers) == [0x1234]


def test_encode_int16_known_value():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["-1"], value_type="int16")
    )
    assert list(result.registers) == [0xFFFF]


def test_encode_int32_known_value():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["-65536"], value_type="int32", word_order="big")
    )
    assert list(result.registers) == [0xFFFF, 0x0000]


def test_encode_float32_known_ieee754_value():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["42.0"], value_type="float32")
    )
    assert list(result.registers) == [0x4228, 0x0000]


def test_encode_float64_known_ieee754_value():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["42.0"], value_type="float64")
    )
    assert list(result.registers) == [0x4045, 0x0000, 0x0000, 0x0000]


def test_encode_round_trips_through_decode():
    from gen.messages_pb2 import DecodeRegisterBlockInput
    from nodes.decode_register_block import decode_register_block

    ax = FakeAxiomContext()
    enc = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["1234", "-5678"], value_type="int32")
    )
    assert enc.error == ""
    dec = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=list(enc.registers), value_type="int32")
    )
    assert [v.as_string for v in dec.values] == ["1234", "-5678"]


def test_encode_value_out_of_range_is_structured_error():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["99999"], value_type="int16")
    )
    assert result.error != ""
    assert len(result.registers) == 0


def test_encode_unparseable_value_is_structured_error():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["not-a-number"], value_type="int32")
    )
    assert result.error != ""


def test_encode_unknown_value_type_is_structured_error():
    ax = FakeAxiomContext()
    result = encode_register_block(
        ax, EncodeRegisterBlockInput(values=["1"], value_type="int128")
    )
    assert result.error != ""
