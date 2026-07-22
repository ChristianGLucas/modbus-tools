from pymodbus.framer.socket import FramerSocket

from gen.messages_pb2 import EncodeTcpFrameInput, EncodeTcpFrameOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import ENCODE_ERROR_TYPES, frame_to_pdu, new_decoder


def encode_tcp_frame(ax: AxiomContext, input: EncodeTcpFrameInput) -> EncodeTcpFrameOutput:
    """Build a raw Modbus TCP/MBAP application data unit (MBAP header +
    function code + data) from a structured function-code + fields
    description, using the frame's transaction_id and device_id (as the MBAP
    unit id). Malformed input returns a structured error, never a crash.
    """
    if not input.HasField("frame"):
        return EncodeTcpFrameOutput(error="frame is required")

    try:
        decoder = new_decoder(input.is_response)
        pdu = frame_to_pdu(input.frame, input.is_response)
        framer = FramerSocket(decoder)
        data = framer.buildFrame(pdu)
    except ENCODE_ERROR_TYPES as exc:
        return EncodeTcpFrameOutput(error=f"{type(exc).__name__}: {exc}")

    return EncodeTcpFrameOutput(data=data)
