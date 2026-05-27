from app import create_app
from app.utils import video_utils
import os


def setup_video_env(tmp_path):
    video_root = tmp_path / "vids"
    video_root.mkdir()
    (video_root / "a.mp4").write_text("data")
    sub = video_root / "folder"
    sub.mkdir()
    (sub / "b.mp4").write_text("data")
    assets = tmp_path / "assets"
    assets.mkdir()
    return video_root, assets


def create_test_app(tmp_path, monkeypatch):
    video_root, assets = setup_video_env(tmp_path)
    cfg = {
        "directories": {"videos": str(video_root), "web_assets": str(assets)},
        "video": {"extensions": [".mp4"], "per_page": 1},
        "cache": {"ttl_seconds": 1},
        "server": {"host": "localhost", "port": 0, "debug": False},
    }
    app = create_app({"TESTING": True, "VOD_CONFIG": cfg})
    monkeypatch.setattr(video_utils, "generate_thumbnail", lambda *a, **k: "t.jpg")
    from app import routes
    monkeypatch.setattr(routes, "generate_thumbnail", lambda *a, **k: "t.jpg")
    from app.utils import cache_manager
    monkeypatch.setattr(cache_manager, "generate_thumbnail", lambda *a, **k: "t.jpg")
    return app


def test_index_and_search_routes(tmp_path, monkeypatch):
    app = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()
    res = client.get("/")
    assert res.status_code == 200
    assert b"a.mp4" in res.data
    res = client.get("/folder/folder")
    assert res.status_code == 200
    assert b"b.mp4" in res.data
    res = client.get("/search?q=a")
    assert res.status_code == 200
    assert b"a.mp4" in res.data


def test_api_info_route(tmp_path, monkeypatch):
    app = create_test_app(tmp_path, monkeypatch)
    client = app.test_client()
    res = client.get("/api/info")
    assert res.status_code == 200
    data = res.get_json()
    assert data["video"]["per_page"] == 1
    assert "directories" in data

