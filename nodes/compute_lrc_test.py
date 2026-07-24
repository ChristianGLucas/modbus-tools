from gen.messages_pb2 import ComputeLrcInput
from nodes.compute_lrc import compute_lrc
from nodes._test_helpers import FakeAxiomContext, oracle_lrc

_DATA = bytes.fromhex("1103006B0003")  # classic reference-guide example


def test_compute_lrc_matches_independent_oracle():
    ax = FakeAxiomContext()
    result = compute_lrc(ax, ComputeLrcInput(data=_DATA))
    assert result.error == ""
    assert result.lrc == oracle_lrc(_DATA)
    assert result.lrc == 0x7E


def test_compute_lrc_validate_true_match():
    ax = FakeAxiomContext()
    result = compute_lrc(ax, ComputeLrcInput(data=_DATA, validate=True, expected_lrc=0x7E))
    assert result.matches is True


def test_compute_lrc_validate_true_mismatch():
    ax = FakeAxiomContext()
    result = compute_lrc(ax, ComputeLrcInput(data=_DATA, validate=True, expected_lrc=0))
    assert result.matches is False


def test_compute_lrc_large_input_no_crash():
    # Input size is the platform's concern, not this node's.
    ax = FakeAxiomContext()
    result = compute_lrc(ax, ComputeLrcInput(data=b"\x00" * 70000))
    assert result.error == ""
