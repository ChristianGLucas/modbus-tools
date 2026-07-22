from pymodbus.framer.ascii import FramerAscii

from gen.messages_pb2 import EncodeAsciiFrameInput, EncodeAsciiFrameOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import ModbusCodecError, frame_to_pdu, new_decoder


def encode_ascii_frame(ax: AxiomContext, input: EncodeAsciiFrameInput) -> EncodeAsciiFrameOutput:
    """Build a Modbus ASCII frame (':' + uppercase hex-encoded device
    id/function code/data/LRC + CRLF) from a structured function-code +
    fields description. The LRC is computed and appended automatically.
    Malformed input returns a structured error, never a crash.
    """
    if not input.HasField("frame"):
        return EncodeAsciiFrameOutput(error="frame is required")

    try:
        decoder = new_decoder(input.is_response)
        pdu = frame_to_pdu(input.frame, input.is_response)
        framer = FramerAscii(decoder)
        data = framer.buildFrame(pdu)
    except (ModbusCodecError, ValueError) as exc:
        return EncodeAsciiFrameOutput(error=str(exc))

    return EncodeAsciiFrameOutput(frame=data.decode("ascii"))
