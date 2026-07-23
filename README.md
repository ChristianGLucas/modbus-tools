# modbus-tools

Composable [Axiom](https://axiomide.com) nodes for Modbus industrial-protocol frame
encode/decode — pure, stateless codec logic wrapping
[pymodbus](https://github.com/pymodbus-dev/pymodbus) (BSD-3-Clause). No socket
or bus I/O: every node is a single-input → single-output function over bytes.

## Nodes

All nodes share one canonical `ModbusFrame` envelope (function code + address /
count / registers / coils / value / masks / exception code) for the function
codes most Modbus integrations actually use: read/write coils and discrete
inputs (1, 2, 5, 15), read/write holding and input registers (3, 4, 6, 16),
mask-write register (22), read/write-multiple registers (23), and exception
responses.

- **DecodeRtuFrame** / **EncodeRtuFrame** — Modbus RTU (device id + PDU +
  CRC16), the serial-line framing. Decode independently verifies the CRC16.
- **DecodeTcpFrame** / **EncodeTcpFrame** — Modbus TCP / MBAP (transaction id +
  unit id + PDU), the Ethernet framing.
- **DecodeAsciiFrame** / **EncodeAsciiFrame** — Modbus ASCII (`:` + hex + LRC +
  CRLF). Decode independently verifies the LRC.
- **ComputeCrc16** / **ComputeLrc** — standalone checksum utilities over
  arbitrary bytes, with optional validation against an expected value.
- **DecodeRegisterBlock** / **EncodeRegisterBlock** — typed register values
  (int16/uint16/int32/uint32/int64/uint64/float32/float64) with configurable
  byte order (within a register) and word order (across registers).
- **PackCoils** / **UnpackCoils** — coil/discrete-input bit ↔ byte packing,
  LSB-first (the same convention function codes 1/2/15 use on the wire).

## Scope

This package covers frame **encode/decode only** — it never opens a socket or
serial port. Diagnostics (function code 8), comm-event/device-id messages (7,
11, 0x0B, 0x0C), and MEI/device-identification (0x2B) are intentionally out of
scope; see the project retrospective for why.

## License

MIT. Wraps [pymodbus](https://github.com/pymodbus-dev/pymodbus) (BSD-3-Clause,
no mandatory transitive dependencies for the codec surface this package uses).

Built for the Axiom marketplace.
