from pymodbus.framer.ascii import FramerAscii

from gen.messages_pb2 import ComputeLrcInput, ComputeLrcOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import MAX_CHECKSUM_BYTES


def compute_lrc(ax: AxiomContext, input: ComputeLrcInput) -> ComputeLrcOutput:
    """Compute the Modbus ASCII LRC (two's complement of the sum of bytes,
    masked to 8 bits) over arbitrary bytes — typically a frame's device id +
    function code + data. Optionally validates an expected LRC in the same
    call.
    """
    data = input.data
    if len(data) > MAX_CHECKSUM_BYTES:
        return ComputeLrcOutput(error=f"data exceeds {MAX_CHECKSUM_BYTES} bytes")

    lrc = FramerAscii.compute_LRC(bytes(data))
    matches = (lrc == input.expected_lrc) if input.validate else False
    return ComputeLrcOutput(lrc=lrc, matches=matches)
