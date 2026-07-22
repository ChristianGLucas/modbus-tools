from gen.messages_pb2 import UnpackCoilsInput, UnpackCoilsOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import MAX_BITS, ModbusCodecError, unpack_coils as _unpack_coils


def unpack_coils(ax: AxiomContext, input: UnpackCoilsInput) -> UnpackCoilsOutput:
    """Unpack bytes into a list of coil/discrete-input bit values, LSB-first —
    the inverse of PackCoils. `count` (if nonzero) trims the trailing
    zero-padding bits from the final byte; 0 returns all 8*len(data) bits.
    """
    data = bytes(input.data)
    if len(data) * 8 > MAX_BITS:
        return UnpackCoilsOutput(error=f"data unpacks to more than {MAX_BITS} bits")

    try:
        bits = _unpack_coils(data, input.count)
    except ModbusCodecError as exc:
        return UnpackCoilsOutput(error=str(exc))

    return UnpackCoilsOutput(bits=bits)
