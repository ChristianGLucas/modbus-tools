from pymodbus.framer.socket import FramerSocket

from gen.messages_pb2 import DecodeTcpFrameInput, DecodeTcpFrameOutput, ModbusFrame
from gen.axiom_context import AxiomContext
from nodes._modbus_common import DECODE_ERROR_TYPES, MAX_FRAME_BYTES, new_decoder, pdu_to_frame_kwargs


def decode_tcp_frame(ax: AxiomContext, input: DecodeTcpFrameInput) -> DecodeTcpFrameOutput:
    """Decode a raw Modbus TCP/MBAP application data unit (MBAP header +
    function code + data) into its transaction id, unit id, function code, and
    fields. Modbus TCP has no CRC — the MBAP length field is validated instead.
    Malformed input (too short, wrong protocol id, length mismatch, unknown
    function code) returns a structured error, never a crash.
    """
    data = input.data
    if len(data) > MAX_FRAME_BYTES:
        return DecodeTcpFrameOutput(error=f"frame exceeds {MAX_FRAME_BYTES} bytes")

    decoder = new_decoder(input.is_response)
    framer = FramerSocket(decoder)
    msg_len, dev_id, tid, pdu_bytes = framer.decode(bytes(data))
    if not msg_len or not pdu_bytes:
        return DecodeTcpFrameOutput(
            error="malformed MBAP frame: too short, wrong protocol id, or length mismatch"
        )

    try:
        pdu = decoder.decode(pdu_bytes)
        if pdu is None:
            return DecodeTcpFrameOutput(
                error=f"unrecognized or unsupported function code {pdu_bytes[0]}"
            )
        pdu.dev_id = dev_id
        pdu.transaction_id = tid
        kwargs = pdu_to_frame_kwargs(pdu)
    except DECODE_ERROR_TYPES as exc:
        return DecodeTcpFrameOutput(error=f"{type(exc).__name__}: {exc}")

    return DecodeTcpFrameOutput(frame=ModbusFrame(**kwargs))
