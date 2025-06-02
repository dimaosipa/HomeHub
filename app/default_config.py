"""
Default configuration for the Homehub.
These values will be used if not overridden by the instance config.
"""

# Default VOD configuration
DEFAULT_VOD_CONFIG = {
    "server": {
        "port": 8080,
        "host": "0.0.0.0",
        "debug": False,
        "name": "HomeHub"  # Service name for discovery
    },
    "directories": {
        "videos": "../vids",
        "web_assets": "../www"
    },
    "video": {
        "extensions": [".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv"],
        "per_page": 10
    },
    "cache": {
        "ttl_seconds": 300
    },
    "discovery": {
        "enabled": True,
        "service_name": "HomeHub"
    }
}
