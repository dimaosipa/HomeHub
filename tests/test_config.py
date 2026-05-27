import os
from app import create_app
from app.config import deep_merge, get_config as get_app_config


def test_deep_merge():
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 20}, "e": 5}
    result = deep_merge(base, override)
    assert result == {"a": 1, "b": {"c": 20, "d": 3}, "e": 5}
    # ensure originals unchanged
    assert base == {"a": 1, "b": {"c": 2, "d": 3}}


def test_get_config_override(tmp_path):
    video_dir = tmp_path / "vids"
    video_dir.mkdir()
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    app = create_app({
        "TESTING": True,
        "VOD_CONFIG": {
            "directories": {
                "videos": str(video_dir),
                "web_assets": str(assets_dir)
            },
            "video": {"per_page": 5},
            "cache": {"ttl_seconds": 1},
        }
    })
    with app.app_context():
        cfg = get_app_config()
    assert cfg["video"]["per_page"] == 5
    assert cfg["directories"]["videos"] == str(video_dir)

