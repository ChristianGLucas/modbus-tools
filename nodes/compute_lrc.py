from pymodbus.framer.ascii import FramerAscii

from gen.messages_pb2 import ComputeLrcInput, ComputeLrcOutput
from gen.axiom_context import AxiomContext
def compute_lrc(ax: AxiomContext, input: ComputeLrcInput) -> ComputeLrcOutput:
    """Compute the Modbus ASCII LRC (two's complement of the sum of bytes,
    masked to 8 bits) over arbitrary bytes — typically a frame's device id +
    function code + data. Optionally validates an expected LRC in the same
    call.
    """
    data = input.data
    lrc = FramerAscii.compute_LRC(bytes(data))
    matches = (lrc == input.expected_lrc) if input.validate else False
    return ComputeLrcOutput(lrc=lrc, matches=matches)
