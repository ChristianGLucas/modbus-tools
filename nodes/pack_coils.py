from gen.messages_pb2 import PackCoilsInput, PackCoilsOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import pack_coils as _pack_coils


def pack_coils(ax: AxiomContext, input: PackCoilsInput) -> PackCoilsOutput:
    """Pack a list of coil/discrete-input bit values into bytes, LSB-first —
    the same wire encoding Modbus function codes 1/2/15 use for coil data.
    Zero-pads the final byte if the bit count isn't a multiple of 8.
    """
    bits = list(input.bits)
    data = _pack_coils(bits)
    return PackCoilsOutput(data=data)
