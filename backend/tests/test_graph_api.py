def test_graph_data_route_returns_starry_story_payload(client, monkeypatch):
    payload = {
        "graph_id": "graph-1",
        "nodes": [
            {
                "uuid": "node-1",
                "presentation": {"kind": "star-node"},
                "story_card": {
                    "title": "Childhood",
                    "description": "A remembered fragment",
                },
            }
        ],
        "edges": [],
        "scene": {"motion": {"reduced_motion_supported": True}},
    }

    class FakeBuilder:
        def __init__(self, api_key=None):
            pass

        def get_graph_data(self, graph_id):
            return payload

    monkeypatch.setattr("app.api.graph.GraphBuilderService", FakeBuilder)
    response = client.get("/api/graph/data/graph-1")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["nodes"][0]["story_card"]["title"] == "Childhood"
