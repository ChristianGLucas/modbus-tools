from gen.messages_pb2 import DecodeRegisterBlockInput
from nodes.decode_register_block import decode_register_block
from nodes._test_helpers import FakeAxiomContext


def test_decode_uint16_known_value():
    # 0x1234 = 4660 — trivial hex-to-decimal, hand-verified.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0x1234], value_type="uint16")
    )
    assert result.error == ""
    assert len(result.values) == 1
    assert result.values[0].as_string == "4660"
    assert result.values[0].as_double == 4660.0


def test_decode_int16_known_value():
    # 0xFFFF is -1 in two's complement — universally known fact.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0xFFFF], value_type="int16")
    )
    assert result.values[0].as_string == "-1"


def test_decode_int32_known_value_big_word_order():
    # 0xFFFF0000 == -65536 in two's complement (hand-verified: unsigned
    # 4294901760 - 2**32 = -65536).
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax,
        DecodeRegisterBlockInput(
            registers=[0xFFFF, 0x0000], value_type="int32", word_order="big"
        ),
    )
    assert result.values[0].as_string == "-65536"


def test_decode_int32_little_word_order_swaps_registers():
    # same bit pattern as above but with the two registers swapped, so
    # word_order="little" must recover the same value.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax,
        DecodeRegisterBlockInput(
            registers=[0x0000, 0xFFFF], value_type="int32", word_order="little"
        ),
    )
    assert result.values[0].as_string == "-65536"


def test_decode_int64_all_ones_is_minus_one():
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax,
        DecodeRegisterBlockInput(
            registers=[0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF], value_type="int64"
        ),
    )
    assert result.values[0].as_string == "-1"


def test_decode_uint64_known_value():
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0, 0, 0, 1], value_type="uint64")
    )
    assert result.values[0].as_string == "1"


def test_decode_float32_known_ieee754_value():
    # 0x42280000 is the well-known IEEE-754 single-precision bit pattern for 42.0.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0x4228, 0x0000], value_type="float32")
    )
    assert result.values[0].as_double == 42.0


def test_decode_float32_negative_known_value():
    # 0xBFC00000 is the known IEEE-754 single-precision bit pattern for -1.5.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0xBFC0, 0x0000], value_type="float32")
    )
    assert result.values[0].as_double == -1.5


def test_decode_float64_known_ieee754_value():
    # 0x4045000000000000 is the well-known IEEE-754 double-precision bit pattern for 42.0.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax,
        DecodeRegisterBlockInput(
            registers=[0x4045, 0x0000, 0x0000, 0x0000], value_type="float64"
        ),
    )
    assert result.values[0].as_double == 42.0


def test_decode_byte_order_little_swaps_bytes_within_register():
    # 0x3412 byte-swapped is 0x1234 == 4660, matching test_decode_uint16_known_value.
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax,
        DecodeRegisterBlockInput(registers=[0x3412], value_type="uint16", byte_order="little"),
    )
    assert result.values[0].as_string == "4660"


def test_decode_multiple_values_in_one_block():
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0x1234, 0xFFFF], value_type="uint16")
    )
    assert [v.as_string for v in result.values] == ["4660", "65535"]


def test_decode_register_count_not_multiple_of_width_is_structured_error():
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0x0001], value_type="int32")
    )
    assert result.error != ""
    assert len(result.values) == 0


def test_decode_unknown_value_type_is_structured_error():
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[0x0001], value_type="int128")
    )
    assert result.error != ""


def test_decode_out_of_range_register_is_structured_error():
    ax = FakeAxiomContext()
    result = decode_register_block(
        ax, DecodeRegisterBlockInput(registers=[70000], value_type="uint16")
    )
    assert result.error != ""
