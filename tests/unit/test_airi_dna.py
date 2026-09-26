from security.airi_dna import ContributionLineage, build_dna


def _dna(**overrides):
    kwargs = dict(
        artifact_id="art-1",
        creator="creator-1",
        version="1.0.0",
        timestamp="2026-09-25T00:00:00Z",
        provenance={"source": "unit-test"},
        lineage=[ContributionLineage(None, "authored", "creator-1")],
        policy_state="APPROVED",
        content=b"hello world",
    )
    kwargs.update(overrides)
    return build_dna(**kwargs)


def test_same_input_same_fingerprint():
    assert _dna().fingerprint() == _dna().fingerprint()


def test_changed_content_changes_fingerprint():
    assert _dna(content=b"a").fingerprint() != _dna(content=b"b").fingerprint()


def test_changed_provenance_changes_fingerprint():
    a = _dna(provenance={"source": "unit-test"})
    b = _dna(provenance={"source": "other"})
    assert a.fingerprint() != b.fingerprint()


def test_changed_version_changes_fingerprint():
    assert _dna(version="1.0.0").fingerprint() != _dna(version="1.0.1").fingerprint()


def test_canonical_serialization_deterministic():
    a = _dna(provenance={"b": 2, "a": 1})
    b = _dna(provenance={"a": 1, "b": 2})
    assert a.canonical_bytes() == b.canonical_bytes()
    assert a.fingerprint() == b.fingerprint()


def test_changed_lineage_changes_fingerprint():
    a = _dna(lineage=[ContributionLineage(None, "authored", "creator-1")])
    b = _dna(lineage=[ContributionLineage(None, "authored", "creator-2")])
    assert a.fingerprint() != b.fingerprint()


def test_missing_provenance_raises():
    import pytest
    with pytest.raises(ValueError):
        build_dna(
            artifact_id="art-1",
            creator="creator-1",
            version="1.0.0",
            timestamp="2026-09-25T00:00:00Z",
            provenance=None,
            content=b"x",
        )


def test_fingerprint_is_sha256_hex():
    fp = _dna().fingerprint()
    assert isinstance(fp, str)
    assert len(fp) == 64
    int(fp, 16)  # must be valid hex
