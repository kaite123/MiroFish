from app.services.graph_builder import GraphBuilderService


def test_get_graph_data_exposes_story_card_fields(monkeypatch):
    service = GraphBuilderService(api_key="test-key")

    class FakeNode:
        uuid_ = "node-1"
        name = "Childhood"
        labels = ["Memory"]
        summary = "A short remembered scene"
        attributes = {"time_hint": "summer"}
        created_at = None

    class FakeEdge:
        uuid_ = "edge-1"
        name = "RELATES_TO"
        fact = "Connected"
        fact_type = "RELATES_TO"
        source_node_uuid = "node-1"
        target_node_uuid = "node-1"
        attributes = {}
        created_at = valid_at = invalid_at = expired_at = None
        episodes = []

    monkeypatch.setattr("app.services.graph_builder.fetch_all_nodes", lambda client, graph_id: [FakeNode()])
    monkeypatch.setattr("app.services.graph_builder.fetch_all_edges", lambda client, graph_id: [FakeEdge()])

    payload = service.get_graph_data("graph-1")
    node = payload["nodes"][0]

    assert "presentation" in node
    assert node["presentation"]["kind"] == "star-node"
    assert node["story_card"]["title"] == "Childhood"
    assert "description" in node["story_card"]


def test_get_graph_data_exposes_scene_guardrails(monkeypatch):
    service = GraphBuilderService(api_key="test-key")
    monkeypatch.setattr("app.services.graph_builder.fetch_all_nodes", lambda client, graph_id: [])
    monkeypatch.setattr("app.services.graph_builder.fetch_all_edges", lambda client, graph_id: [])

    payload = service.get_graph_data("graph-1")

    assert payload["scene"]["motion"]["reduced_motion_supported"] is True
    assert payload["scene"]["limits"]["max_particles"] >= 0
    assert payload["scene"]["contrast"]["card_text_min_ratio"] >= 4.5
