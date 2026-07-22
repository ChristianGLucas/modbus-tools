from gen.messages_pb2 import EncodeRegisterBlockInput, EncodeRegisterBlockOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import MAX_REGISTERS, ModbusCodecError, encode_typed_values


def encode_register_block(ax: AxiomContext, input: EncodeRegisterBlockInput) -> EncodeRegisterBlockOutput:
    """Encode a list of decimal-string values (int16/uint16/int32/uint32/
    int64/uint64/float32/float64) into a block of raw 16-bit Modbus registers,
    with configurable byte order (within each register) and word order
    (across registers, for multi-register types) — the inverse of
    DecodeRegisterBlock. Malformed input (unparseable value, value out of
    range for the type, unknown type/order) returns a structured error, never
    a crash.
    """
    values = list(input.values)
    if len(values) > MAX_REGISTERS:
        return EncodeRegisterBlockOutput(error=f"values exceeds {MAX_REGISTERS} entries")

    try:
        registers = encode_typed_values(
            values,
            input.value_type,
            input.byte_order or "big",
            input.word_order or "big",
        )
    except ModbusCodecError as exc:
        return EncodeRegisterBlockOutput(error=str(exc))

    return EncodeRegisterBlockOutput(registers=registers)
