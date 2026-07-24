from gen.messages_pb2 import DecodeRegisterBlockInput, DecodeRegisterBlockOutput, TypedValue
from gen.axiom_context import AxiomContext
from nodes._modbus_common import ModbusCodecError, decode_typed_values


def decode_register_block(ax: AxiomContext, input: DecodeRegisterBlockInput) -> DecodeRegisterBlockOutput:
    """Decode a block of raw 16-bit Modbus registers into a list of typed
    values (int16/uint16/int32/uint32/int64/uint64/float32/float64), with
    configurable byte order (within each register) and word order (across
    registers, for multi-register types). Malformed input (wrong register
    count for the type, unknown type/order) returns a structured error, never
    a crash.
    """
    registers = list(input.registers)

    try:
        for r in registers:
            if not 0 <= r <= 0xFFFF:
                raise ModbusCodecError(f"register value out of range 0-65535: {r}")
        values = decode_typed_values(
            registers,
            input.value_type,
            input.byte_order or "big",
            input.word_order or "big",
        )
    except ModbusCodecError as exc:
        return DecodeRegisterBlockOutput(error=str(exc))

    out = [TypedValue(as_double=float(v), as_string=str(v)) for v in values]
    return DecodeRegisterBlockOutput(values=out)
