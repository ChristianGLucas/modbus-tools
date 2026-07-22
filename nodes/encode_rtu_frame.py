from pymodbus.framer.rtu import FramerRTU

from gen.messages_pb2 import EncodeRtuFrameInput, EncodeRtuFrameOutput
from gen.axiom_context import AxiomContext
from nodes._modbus_common import ENCODE_ERROR_TYPES, frame_to_pdu, new_decoder


def encode_rtu_frame(ax: AxiomContext, input: EncodeRtuFrameInput) -> EncodeRtuFrameOutput:
    """Build a raw Modbus RTU frame (device id + function code + data + CRC16)
    from a structured function-code + fields description. The CRC16 is
    computed and appended automatically. Malformed input (e.g. an address,
    quantity, or device_id out of its protocol-defined range) returns a
    structured error, never a crash.
    """
    if not input.HasField("frame"):
        return EncodeRtuFrameOutput(error="frame is required")

    try:
        decoder = new_decoder(input.is_response)
        pdu = frame_to_pdu(input.frame, input.is_response)
        framer = FramerRTU(decoder)
        data = framer.buildFrame(pdu)
    except ENCODE_ERROR_TYPES as exc:
        return EncodeRtuFrameOutput(error=f"{type(exc).__name__}: {exc}")

    return EncodeRtuFrameOutput(data=data)
