import pytest

from security.correction_propagation import (
    CorrectionRegistry,
    CorrectionState,
    LineageGraph,
)


def build_graph():
    graph = LineageGraph()
    graph.add_edge("dataset", "modelA", material=True)
    graph.add_edge("modelA", "agentC", material=True)
    graph.add_edge("agentC", "systemD", material=True)
    graph.add_edge("modelA", "testOnly", material=False)
    return graph


def test_descendants_returns_material_forward_closure():
    assert build_graph().descendants("dataset") == [
        "modelA", "agentC", "systemD"
    ]


def test_descendants_excludes_origin():
    assert "dataset" not in build_graph().descendants("dataset")


def test_non_material_edge_does_not_leak_through_intermediary():
    graph = LineageGraph()
    graph.add_edge("dataset", "testOnly", material=False)
    graph.add_edge("testOnly", "production", material=True)
    assert graph.descendants("dataset") == []


def test_cycles_do_not_create_infinite_traversal():
    graph = LineageGraph()
    graph.add_edge("root", "nodeA")
    graph.add_edge("nodeA", "root")
    graph.add_edge("nodeA", "nodeB")
    assert graph.descendants("root") == ["nodeA", "nodeB"]


def test_closure_can_return_false_on_first_check():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    closed, open_nodes = registry.verify_closure(correction.correction_id)
    assert closed is False
    assert len(open_nodes) == 3
    assert all(
        state == CorrectionState.DISCOVERED
        for _, state in open_nodes
    )


def test_propagation_reaches_reassessment_and_is_idempotent():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    registry.propagate(correction.correction_id)
    first = correction.dispositions
    assert all(
        state == CorrectionState.REASSESSMENT_REQUIRED
        for state in first.values()
    )
    registry.propagate(correction.correction_id)
    assert correction.dispositions == first


def test_closure_true_when_all_nodes_are_terminal():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    registry.propagate(correction.correction_id)

    registry.set_disposition(
        correction.correction_id, "modelA", CorrectionState.REPAIRED
    )
    registry.set_disposition(
        correction.correction_id, "agentC", CorrectionState.REPAIRED
    )
    registry.set_disposition(
        correction.correction_id, "systemD", CorrectionState.EXEMPT
    )

    closed, open_nodes = registry.verify_closure(correction.correction_id)
    assert closed is True
    assert open_nodes == []


def test_partial_resolution_keeps_closure_open():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    registry.propagate(correction.correction_id)
    registry.set_disposition(
        correction.correction_id, "modelA", CorrectionState.REPAIRED
    )
    closed, open_nodes = registry.verify_closure(correction.correction_id)
    assert closed is False
    assert len(open_nodes) == 2


def test_set_disposition_rejects_unknown_node():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    registry.propagate(correction.correction_id)
    with pytest.raises(ValueError):
        registry.set_disposition(
            correction.correction_id,
            "notInGraph",
            CorrectionState.REPAIRED,
        )


def test_disposition_rejected_before_reassessment():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    with pytest.raises(ValueError):
        registry.set_disposition(
            correction.correction_id,
            "modelA",
            CorrectionState.REPAIRED,
        )


def test_duplicate_correction_id_rejected():
    registry = CorrectionRegistry()
    graph = build_graph()
    registry.register(
        graph, "dataset", "first correction", correction_id="fixed-id"
    )
    with pytest.raises(ValueError):
        registry.register(
            graph,
            "dataset",
            "second correction",
            correction_id="fixed-id",
        )


def test_graph_hash_is_independent_of_insertion_order():
    graph_a = LineageGraph()
    graph_a.add_edge("a", "b")
    graph_a.add_edge("b", "c")

    graph_b = LineageGraph()
    graph_b.add_edge("b", "c")
    graph_b.add_edge("a", "b")

    assert graph_a.snapshot_sha256 == graph_b.snapshot_sha256


def test_record_snapshot_hash_is_deterministic_and_state_sensitive():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(),
        "dataset",
        "label leakage",
        correction_id="fixed-id",
    )
    first = correction.to_record()
    second = correction.to_record()

    assert first["snapshot_sha256"] == second["snapshot_sha256"]
    assert len(first["snapshot_sha256"]) == 64

    registry.propagate(correction.correction_id)
    third = correction.to_record()

    assert third["snapshot_sha256"] != first["snapshot_sha256"]


def test_unresolved_node_can_be_explicitly_reopened():
    registry = CorrectionRegistry()
    correction = registry.register(
        build_graph(), "dataset", "label leakage"
    )
    registry.propagate(correction.correction_id)
    registry.set_disposition(
        correction.correction_id, "modelA", CorrectionState.UNRESOLVED
    )
    registry.reopen_unresolved(correction.correction_id, "modelA")

    assert (
        correction.dispositions["modelA"]
        == CorrectionState.REASSESSMENT_REQUIRED
    )


def test_empty_graph_has_no_open_descendant_obligations():
    registry = CorrectionRegistry()
    correction = registry.register(
        LineageGraph(), "isolated-origin", "test correction"
    )
    closed, open_nodes = registry.verify_closure(correction.correction_id)
    assert closed is True
    assert open_nodes == []
