"""Shared Modbus PDU <-> ModbusFrame conversion helpers, used by every node.

All the protocol-hard parts (PDU field layouts, function-code semantics,
CRC16/LRC math, MBAP framing) are delegated to pymodbus (BSD-3-Clause). This
module only adapts pymodbus's PDU object model to/from our flat ModbusFrame
envelope, plus small struct-based glue for typed register values.
"""
from __future__ import annotations

import struct

from pymodbus.pdu.bit_message import (
    ReadCoilsRequest,
    ReadCoilsResponse,
    ReadDiscreteInputsRequest,
    ReadDiscreteInputsResponse,
    WriteMultipleCoilsRequest,
    WriteMultipleCoilsResponse,
    WriteSingleCoilRequest,
    WriteSingleCoilResponse,
)
from pymodbus.pdu.decoders import DecodePDU
from pymodbus.pdu.exceptionresponse import ExceptionResponse
from pymodbus.pdu.utils import pack_bitstring, unpack_bitstring
from pymodbus.exceptions import ModbusException
from pymodbus.pdu.register_message import (
    MaskWriteRegisterRequest,
    MaskWriteRegisterResponse,
    ReadHoldingRegistersRequest,
    ReadHoldingRegistersResponse,
    ReadInputRegistersRequest,
    ReadInputRegistersResponse,
    ReadWriteMultipleRegistersRequest,
    ReadWriteMultipleRegistersResponse,
    WriteMultipleRegistersRequest,
    WriteMultipleRegistersResponse,
    WriteSingleRegisterRequest,
    WriteSingleRegisterResponse,
)

# Function codes this package covers (register/coil data-access + mask-write +
# read/write-multiple). Diagnostics (0x08), device-id/comm-event messages
# (0x07/0x0B/0x0C/0x11), and MEI/device-identification (0x2B) are deliberately
# out of scope — see the retrospective for why.
SUPPORTED_FUNCTION_CODES = (1, 2, 3, 4, 5, 6, 15, 16, 22, 23)

MAX_FRAME_BYTES = 260  # generous ceiling; real Modbus PDUs are <= 253 bytes
MAX_REGISTERS = 4096  # bounds DecodeRegisterBlock/EncodeRegisterBlock input size
MAX_BITS = 65536  # bounds PackCoils/UnpackCoils input size
MAX_CHECKSUM_BYTES = 65536  # bounds the standalone ComputeCrc16/ComputeLrc utilities


class ModbusCodecError(ValueError):
    """Raised for any malformed input; callers turn this into a structured error field."""


# Every exception type an encode node's try/except should catch and turn into
# a structured `error` string rather than letting a raw traceback leak out.
# ModbusCodecError/ValueError cover our own and pymodbus's validation checks
# (verifyAddress/verifyCount); OverflowError covers a negative device_id/tid
# reaching int.to_bytes(); struct.error covers a field (and_mask/or_mask/
# exception_code/register value) that overflows the wire width pymodbus packs
# it into (e.g. struct.pack(">H", ...) with a value > 65535); ModbusException
# is pymodbus's own exception base (e.g. ModbusIOException on an out-of-range
# device id). frame_to_pdu now validates every field it can up front, so these
# are kept as a defensive backstop for anything that validation doesn't cover.
ENCODE_ERROR_TYPES = (ModbusCodecError, ValueError, OverflowError, struct.error, ModbusException)


def new_decoder(is_response: bool) -> DecodePDU:
    """A DecodePDU configured to decode requests (is_response=False) or responses."""
    return DecodePDU(is_server=not is_response)


def pdu_to_frame_kwargs(pdu) -> dict:
    """Convert a decoded pymodbus PDU object into ModbusFrame constructor kwargs."""
    if isinstance(pdu, ExceptionResponse):
        return dict(
            function_code=pdu.function_code & 0x7F,
            device_id=pdu.dev_id,
            transaction_id=pdu.transaction_id,
            is_exception=True,
            exception_code=pdu.exception_code,
        )

    fc = pdu.function_code
    base = dict(function_code=fc, device_id=pdu.dev_id, transaction_id=pdu.transaction_id)

    if fc in (1, 2):
        if pdu.bits:
            base["coils"] = list(pdu.bits)
            base["count"] = len(pdu.bits)
        else:
            base["address"] = pdu.address
            base["count"] = pdu.count
        return base
    if fc in (3, 4):
        if pdu.registers:
            base["registers"] = list(pdu.registers)
            base["count"] = len(pdu.registers)
        else:
            base["address"] = pdu.address
            base["count"] = pdu.count
        return base
    if fc == 5:
        base["address"] = pdu.address
        base["value"] = 1 if pdu.bits[0] else 0
        return base
    if fc == 6:
        base["address"] = pdu.address
        base["value"] = pdu.registers[0]
        return base
    if fc == 15:
        if pdu.bits:
            base["address"] = pdu.address
            base["coils"] = list(pdu.bits)
            base["count"] = len(pdu.bits)
        else:
            base["address"] = pdu.address
            base["count"] = pdu.count
        return base
    if fc == 16:
        if pdu.registers:
            base["address"] = pdu.address
            base["registers"] = list(pdu.registers)
            base["count"] = len(pdu.registers)
        else:
            base["address"] = pdu.address
            base["count"] = pdu.count
        return base
    if fc == 22:
        base["address"] = pdu.address
        base["and_mask"] = pdu.and_mask
        base["or_mask"] = pdu.or_mask
        return base
    if fc == 23:
        if pdu.registers:
            base["registers"] = list(pdu.registers)
            base["count"] = len(pdu.registers)
        else:
            base["read_address"] = pdu.read_address
            base["read_count"] = pdu.read_count
            base["write_address"] = pdu.write_address
            base["write_registers"] = list(pdu.write_registers)
        return base
    raise ModbusCodecError(f"unsupported function code {fc}")


def frame_to_pdu(frame, is_response: bool):
    """Build a pymodbus PDU object from a ModbusFrame."""
    fc = frame.function_code
    dev_id = frame.device_id
    tid = frame.transaction_id

    if not 0 <= dev_id <= 255:
        raise ModbusCodecError(f"device_id out of range 0-255: {dev_id}")
    if not 0 <= tid <= 0xFFFF:
        raise ModbusCodecError(f"transaction_id out of range 0-65535: {tid}")

    if frame.is_exception:
        if not 0 <= frame.exception_code <= 0xFF:
            raise ModbusCodecError(f"exception_code out of range 0-255: {frame.exception_code}")
        return ExceptionResponse(fc, frame.exception_code, device_id=dev_id, transaction=tid)

    if fc in (1, 2):
        req_cls, resp_cls = (
            (ReadCoilsRequest, ReadCoilsResponse)
            if fc == 1
            else (ReadDiscreteInputsRequest, ReadDiscreteInputsResponse)
        )
        if is_response:
            return resp_cls(dev_id=dev_id, transaction_id=tid, bits=list(frame.coils))
        return req_cls(dev_id=dev_id, transaction_id=tid, address=frame.address, count=frame.count)

    if fc in (3, 4):
        req_cls, resp_cls = (
            (ReadHoldingRegistersRequest, ReadHoldingRegistersResponse)
            if fc == 3
            else (ReadInputRegistersRequest, ReadInputRegistersResponse)
        )
        if is_response:
            return resp_cls(dev_id=dev_id, transaction_id=tid, registers=list(frame.registers))
        return req_cls(dev_id=dev_id, transaction_id=tid, address=frame.address, count=frame.count)

    if fc == 5:
        cls = WriteSingleCoilResponse if is_response else WriteSingleCoilRequest
        return cls(dev_id=dev_id, transaction_id=tid, address=frame.address, bits=[bool(frame.value)])

    if fc == 6:
        if not 0 <= frame.value <= 0xFFFF:
            raise ModbusCodecError(f"value out of range 0-65535: {frame.value}")
        cls = WriteSingleRegisterResponse if is_response else WriteSingleRegisterRequest
        return cls(dev_id=dev_id, transaction_id=tid, address=frame.address, registers=[frame.value])

    if fc == 15:
        if is_response:
            count = frame.count or len(frame.coils)
            return WriteMultipleCoilsResponse(
                dev_id=dev_id, transaction_id=tid, address=frame.address, count=count
            )
        return WriteMultipleCoilsRequest(
            dev_id=dev_id, transaction_id=tid, address=frame.address, bits=list(frame.coils)
        )

    if fc == 16:
        if is_response:
            count = frame.count or len(frame.registers)
            return WriteMultipleRegistersResponse(
                dev_id=dev_id, transaction_id=tid, address=frame.address, count=count
            )
        regs = list(frame.registers)
        return WriteMultipleRegistersRequest(
            dev_id=dev_id,
            transaction_id=tid,
            address=frame.address,
            registers=regs,
            count=frame.count or len(regs),
        )

    if fc == 22:
        if not 0 <= frame.and_mask <= 0xFFFF:
            raise ModbusCodecError(f"and_mask out of range 0-65535: {frame.and_mask}")
        if not 0 <= frame.or_mask <= 0xFFFF:
            raise ModbusCodecError(f"or_mask out of range 0-65535: {frame.or_mask}")
        cls = MaskWriteRegisterResponse if is_response else MaskWriteRegisterRequest
        return cls(
            address=frame.address,
            and_mask=frame.and_mask,
            or_mask=frame.or_mask,
            dev_id=dev_id,
            transaction_id=tid,
        )

    if fc == 23:
        if is_response:
            return ReadWriteMultipleRegistersResponse(
                dev_id=dev_id, transaction_id=tid, registers=list(frame.registers)
            )
        return ReadWriteMultipleRegistersRequest(
            read_address=frame.read_address,
            read_count=frame.read_count,
            write_address=frame.write_address,
            write_registers=list(frame.write_registers),
            dev_id=dev_id,
            transaction_id=tid,
        )

    raise ModbusCodecError(
        f"unsupported function_code {fc} (supported: {SUPPORTED_FUNCTION_CODES})"
    )


# --- Typed register block codec (struct-based glue; the "hard part" here is
# just byte/word ordering, which struct.pack/unpack handles exactly) ---------

_TYPE_FORMATS = {
    "int16": ("h", 1),
    "uint16": ("H", 1),
    "int32": ("i", 2),
    "uint32": ("I", 2),
    "int64": ("q", 4),
    "uint64": ("Q", 4),
    "float32": ("f", 2),
    "float64": ("d", 4),
}


def _check_order(name: str, value: str) -> str:
    value = value or "big"
    if value not in ("big", "little"):
        raise ModbusCodecError(f"{name} must be 'big' or 'little', got {value!r}")
    return value


def registers_to_value_bytes(registers: list[int], byte_order: str, word_order: str) -> bytes:
    """Concatenate registers into one big-endian byte buffer honoring byte/word order."""
    for r in registers:
        if not 0 <= r <= 0xFFFF:
            raise ModbusCodecError(f"register value out of range 0-65535: {r}")
    ordered = list(reversed(registers)) if word_order == "little" else list(registers)
    out = bytearray()
    for r in ordered:
        rb = struct.pack(">H", r)
        if byte_order == "little":
            rb = rb[::-1]
        out += rb
    return bytes(out)


def value_bytes_to_registers(raw: bytes, byte_order: str, word_order: str) -> list[int]:
    """Inverse of registers_to_value_bytes: split a big-endian byte buffer into registers."""
    regs = []
    for i in range(0, len(raw), 2):
        chunk = raw[i : i + 2]
        if byte_order == "little":
            chunk = chunk[::-1]
        regs.append(int.from_bytes(chunk, "big"))
    if word_order == "little":
        regs = list(reversed(regs))
    return regs


def decode_typed_values(
    registers: list[int], value_type: str, byte_order: str, word_order: str
):
    """Decode a flat register list into a list of Python numeric values."""
    if value_type not in _TYPE_FORMATS:
        raise ModbusCodecError(
            f"unknown value_type {value_type!r} (expected one of {sorted(_TYPE_FORMATS)})"
        )
    byte_order = _check_order("byte_order", byte_order)
    word_order = _check_order("word_order", word_order)
    fmt, width = _TYPE_FORMATS[value_type]
    if len(registers) % width != 0:
        raise ModbusCodecError(
            f"registers length {len(registers)} is not a multiple of {width} "
            f"(required for value_type {value_type!r})"
        )
    values = []
    for i in range(0, len(registers), width):
        chunk = registers[i : i + width]
        raw = registers_to_value_bytes(chunk, byte_order, word_order)
        (val,) = struct.unpack(">" + fmt, raw)
        values.append(val)
    return values


def pack_coils(bits: list) -> bytes:
    """Pack coil/discrete-input bits into bytes, LSB-first (Modbus wire order).
    Thin pass-through to pymodbus's own PDU bit-packing so this matches the
    exact packing the frame-codec nodes use for function codes 1/2/15.
    """
    return pack_bitstring(list(bits))


def unpack_coils(data: bytes, count: int) -> list:
    """Inverse of pack_coils. count=0 returns every bit (including padding)."""
    if count < 0:
        raise ModbusCodecError(f"count must be >= 0, got {count}")
    bits = unpack_bitstring(bytes(data))
    if count:
        if count > len(bits):
            raise ModbusCodecError(
                f"count {count} exceeds {len(bits)} bits available in {len(data)} byte(s)"
            )
        bits = bits[:count]
    return bits


def encode_typed_values(
    values: list[str], value_type: str, byte_order: str, word_order: str
) -> list[int]:
    """Encode a list of decimal-string values into a flat register list."""
    if value_type not in _TYPE_FORMATS:
        raise ModbusCodecError(
            f"unknown value_type {value_type!r} (expected one of {sorted(_TYPE_FORMATS)})"
        )
    byte_order = _check_order("byte_order", byte_order)
    word_order = _check_order("word_order", word_order)
    fmt, _width = _TYPE_FORMATS[value_type]
    is_float = value_type in ("float32", "float64")
    registers: list[int] = []
    for s in values:
        try:
            parsed = float(s) if is_float else int(s)
        except ValueError as exc:
            raise ModbusCodecError(f"cannot parse {s!r} as {value_type}") from exc
        try:
            raw = struct.pack(">" + fmt, parsed)
        except struct.error as exc:
            raise ModbusCodecError(f"value {s!r} out of range for {value_type}: {exc}") from exc
        registers.extend(value_bytes_to_registers(raw, byte_order, word_order))
    return registers
