import os
from app.utils import cache_manager
from app.utils import video_utils


def setup_tmp_videos(tmp_path):
    root = tmp_path
    (root / "video1.mp4").write_text("data")
    sub = root / "folder"
    sub.mkdir()
    (sub / "video2.mp4").write_text("data")
    return root


def test_find_and_paginate_videos(tmp_path, monkeypatch):
    root = setup_tmp_videos(tmp_path)
    config = {"cache": {"ttl_seconds": 60}}
    cache_manager.init_cache(config)
    cache_manager.VIDEOS_CACHE.update({"videos": [], "folders": [], "last_updated": 0})

    monkeypatch.setattr(video_utils, "generate_thumbnail", lambda *a, **k: "thumb.jpg")
    monkeypatch.setattr(cache_manager, "generate_thumbnail", lambda *a, **k: "thumb.jpg")

    videos = cache_manager.find_videos(str(root), (".mp4",))
    assert len(videos) == 2
    assert any(v["rel_path"] == "video1.mp4" for v in videos)
    folders = cache_manager.get_folders(str(root))
    assert "folder" in folders

    data = cache_manager.get_paginated_videos(str(root), str(root), 1, (".mp4",))
    assert data["total_videos"] == 2
    assert data["total_pages"] == 2

