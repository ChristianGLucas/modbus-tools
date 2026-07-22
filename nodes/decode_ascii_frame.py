import binascii

from pymodbus.framer.ascii import FramerAscii

from gen.messages_pb2 import DecodeAsciiFrameInput, DecodeAsciiFrameOutput, ModbusFrame
from gen.axiom_context import AxiomContext
from nodes._modbus_common import DECODE_ERROR_TYPES, MAX_FRAME_BYTES, new_decoder, pdu_to_frame_kwargs


def decode_ascii_frame(ax: AxiomContext, input: DecodeAsciiFrameInput) -> DecodeAsciiFrameOutput:
    """Decode a Modbus ASCII frame (':' + hex-encoded device id/function
    code/data/LRC + CRLF) into its function code and fields. Verifies the
    trailing LRC independently of structural decoding. Malformed input (no
    ':' start, odd/invalid hex, too short) returns a structured error, never a
    crash.
    """
    text = input.frame.strip()
    if not text.startswith(":"):
        return DecodeAsciiFrameOutput(error="frame must start with ':'")
    hex_body = text[1:].rstrip("\r\n")
    try:
        content = binascii.a2b_hex(hex_body)
    except (binascii.Error, ValueError) as exc:
        return DecodeAsciiFrameOutput(error=f"invalid hex body: {exc}")

    if len(content) > MAX_FRAME_BYTES:
        return DecodeAsciiFrameOutput(error=f"frame exceeds {MAX_FRAME_BYTES} bytes")
    if len(content) < 3:
        return DecodeAsciiFrameOutput(
            error="frame too short: need at least 3 bytes (device id + function code + LRC)"
        )

    payload, wire_lrc = content[:-1], content[-1]
    computed_lrc = FramerAscii.compute_LRC(payload)
    lrc_valid = computed_lrc == wire_lrc
    if not lrc_valid:
        return DecodeAsciiFrameOutput(lrc_valid=False, error="LRC mismatch")

    device_id = payload[0]
    pdu_bytes = payload[1:]
    if not pdu_bytes:
        return DecodeAsciiFrameOutput(lrc_valid=True, error="frame has no function code")

    decoder = new_decoder(input.is_response)
    try:
        pdu = decoder.decode(pdu_bytes)
        if pdu is None:
            return DecodeAsciiFrameOutput(
                lrc_valid=True,
                error=f"unrecognized or unsupported function code {pdu_bytes[0]}",
            )
        pdu.dev_id = device_id
        pdu.transaction_id = 0
        kwargs = pdu_to_frame_kwargs(pdu)
    except DECODE_ERROR_TYPES as exc:
        return DecodeAsciiFrameOutput(lrc_valid=True, error=f"{type(exc).__name__}: {exc}")

    return DecodeAsciiFrameOutput(frame=ModbusFrame(**kwargs), lrc_valid=True)
