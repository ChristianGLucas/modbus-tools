from pymodbus.framer.rtu import FramerRTU

from gen.messages_pb2 import DecodeRtuFrameInput, DecodeRtuFrameOutput, ModbusFrame
from gen.axiom_context import AxiomContext
from nodes._modbus_common import (
    MAX_FRAME_BYTES,
    ModbusCodecError,
    new_decoder,
    pdu_to_frame_kwargs,
)


def decode_rtu_frame(ax: AxiomContext, input: DecodeRtuFrameInput) -> DecodeRtuFrameOutput:
    """Decode a raw Modbus RTU frame (device id + function code + data + CRC16)
    into its function code and fields — register/coil addresses, quantities,
    values, or an exception code. Verifies the trailing CRC16 independently of
    structural decoding, so a CRC failure is reported even when the PDU shape
    would otherwise parse. Malformed input returns a structured error, never a
    crash.
    """
    data = input.data
    if len(data) > MAX_FRAME_BYTES:
        return DecodeRtuFrameOutput(error=f"frame exceeds {MAX_FRAME_BYTES} bytes")
    if len(data) < 4:
        return DecodeRtuFrameOutput(
            error="frame too short: need at least 4 bytes (device id + function code + CRC16)"
        )

    payload, wire_crc = data[:-2], data[-2:]
    computed_crc = FramerRTU.compute_CRC(payload).to_bytes(2, "big")
    crc_valid = computed_crc == wire_crc
    if not crc_valid:
        return DecodeRtuFrameOutput(crc_valid=False, error="CRC16 mismatch")

    device_id = payload[0]
    pdu_bytes = payload[1:]
    if not pdu_bytes:
        return DecodeRtuFrameOutput(crc_valid=True, error="frame has no function code")

    decoder = new_decoder(input.is_response)
    pdu = decoder.decode(pdu_bytes)
    if pdu is None:
        return DecodeRtuFrameOutput(
            crc_valid=True,
            error=f"unrecognized or unsupported function code {pdu_bytes[0]}",
        )
    pdu.dev_id = device_id
    pdu.transaction_id = 0

    try:
        kwargs = pdu_to_frame_kwargs(pdu)
    except ModbusCodecError as exc:
        return DecodeRtuFrameOutput(crc_valid=True, error=str(exc))

    return DecodeRtuFrameOutput(frame=ModbusFrame(**kwargs), crc_valid=True)
