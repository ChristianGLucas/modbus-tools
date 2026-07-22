from gen.messages_pb2 import ComputeCrc16Input
from nodes.compute_crc16 import compute_crc16
from nodes._test_helpers import FakeAxiomContext, oracle_crc16_wire_bytes

_DATA = bytes.fromhex("1103006B0003")  # classic reference-guide example


def test_compute_crc16_matches_independent_oracle():
    ax = FakeAxiomContext()
    result = compute_crc16(ax, ComputeCrc16Input(data=_DATA))
    assert result.error == ""
    assert result.crc16_bytes == oracle_crc16_wire_bytes(_DATA)
    assert result.crc16_bytes == bytes.fromhex("7687")
    # self-consistency between the two output fields
    assert int.from_bytes(result.crc16_bytes, "big") == result.crc16


def test_compute_crc16_validate_true_match():
    ax = FakeAxiomContext()
    expected = int.from_bytes(oracle_crc16_wire_bytes(_DATA), "big")
    result = compute_crc16(ax, ComputeCrc16Input(data=_DATA, validate=True, expected_crc16=expected))
    assert result.matches is True


def test_compute_crc16_validate_true_mismatch():
    ax = FakeAxiomContext()
    result = compute_crc16(ax, ComputeCrc16Input(data=_DATA, validate=True, expected_crc16=0))
    assert result.matches is False


def test_compute_crc16_validate_false_ignores_expected():
    ax = FakeAxiomContext()
    result = compute_crc16(ax, ComputeCrc16Input(data=_DATA, validate=False, expected_crc16=0))
    assert result.matches is False  # not evaluated when validate=False


def test_compute_crc16_too_large_is_structured_error():
    ax = FakeAxiomContext()
    result = compute_crc16(ax, ComputeCrc16Input(data=b"\x00" * 70000))
    assert result.error != ""
