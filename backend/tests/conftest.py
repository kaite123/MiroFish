import os
import sys
import types
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("ZEP_API_KEY", "test-key")


try:
    import zep_cloud  # noqa: F401
except ModuleNotFoundError:
    zep_cloud = types.ModuleType("zep_cloud")
    zep_cloud_client = types.ModuleType("zep_cloud.client")

    class DummyZep:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.graph = types.SimpleNamespace(
                create=lambda **kwargs: None,
                set_ontology=lambda **kwargs: None,
                add_batch=lambda **kwargs: [],
                delete=lambda **kwargs: None,
                episode=types.SimpleNamespace(get=lambda **kwargs: types.SimpleNamespace(processed=True)),
            )

    class DummyEpisodeData:
        def __init__(self, data, type):
            self.data = data
            self.type = type

    class DummyEntityEdgeSourceTarget:
        def __init__(self, source, target):
            self.source = source
            self.target = target

    class DummyInternalServerError(Exception):
        pass

    zep_cloud.EpisodeData = DummyEpisodeData
    zep_cloud.EntityEdgeSourceTarget = DummyEntityEdgeSourceTarget
    zep_cloud.InternalServerError = DummyInternalServerError
    zep_cloud_client.Zep = DummyZep

    sys.modules["zep_cloud"] = zep_cloud
    sys.modules["zep_cloud.client"] = zep_cloud_client


@pytest.fixture()
def app():
    from app import create_app

    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture()
def client(app):
    return app.test_client()
