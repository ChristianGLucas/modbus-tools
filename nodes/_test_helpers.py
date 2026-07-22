"""Shared test scaffolding — a minimal AxiomContext double, plus a from-scratch
(independent of pymodbus) Modbus CRC16/LRC implementation used as the
oracle in several nodes' tests.
"""
from gen.axiom_context import SecretStatus


class FakeAxiomContext:
    """Minimal AxiomContext implementation for unit tests."""

    class _Logger:
        def debug(self, msg: str, **attrs) -> None: pass
        def info(self, msg: str, **attrs) -> None: pass
        def warn(self, msg: str, **attrs) -> None: pass
        def error(self, msg: str, **attrs) -> None: pass

    class _Secrets:
        def __init__(self, m: dict, revoked: set) -> None:
            self._m = m or {}
            self._revoked = revoked or set()

        def get(self, name: str):
            v = self._m.get(name)
            return (v, True) if v is not None else ("", False)

        def status(self, name: str) -> SecretStatus:
            if name in self._m:
                return SecretStatus.AVAILABLE
            if name in self._revoked:
                return SecretStatus.REVOKED
            return SecretStatus.UNSET

    def __init__(self, secrets_map: dict | None = None, revoked_names: set | None = None) -> None:
        self.log = self._Logger()
        self.secrets = self._Secrets(secrets_map or {}, revoked_names)
        self.execution_id = "test-execution-id"
        self.flow_id = "test-flow-id"
        self.tenant_id = "test-tenant-id"


def oracle_crc16(data: bytes) -> int:
    """Textbook Modbus CRC16 (init 0xFFFF, poly 0xA001), implemented from the
    published algorithm — independently of pymodbus's FramerRTU — as the test
    oracle. Returns the "natural" (unswapped) integer; the wire bytes are
    low-byte-first: bytes([crc & 0xFF, (crc >> 8) & 0xFF]).
    """
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def oracle_crc16_wire_bytes(data: bytes) -> bytes:
    crc = oracle_crc16(data)
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def oracle_lrc(data: bytes) -> int:
    """Textbook Modbus ASCII LRC — two's complement of the byte sum, mod 256 —
    implemented from the published algorithm, independently of pymodbus.
    """
    lrc = sum(data) & 0xFF
    lrc = (lrc ^ 0xFF) + 1
    return lrc & 0xFF
