# Homehub

<img src="app/static/homehub.png" alt="HomeHub Logo" width="200" height="100" />

A Flask-based Video-on-Demand server with mobile-friendly responsive UI, folder navigation, pagination, and flexible configuration.

![Demo](https://bomjkolyadun.github.io/HomeHub/demo.gif)

## Features

- Responsive mobile-friendly UI
- Video pagination with configurable items per page
- Folder navigation with sidebar
- URL-encoded video streaming
- Thumbnail generation
- Configuration system with defaults and overrides
- Warning system for problematic filenames
- Caching mechanism for directory scanning

## Requirements

- Python 3.7+
- Flask and dependencies (see `requirements.txt`)
- **FFmpeg** - Required for thumbnail generation and video processing

### Installing FFmpeg

**macOS (with Homebrew):**

```bash
brew install ffmpeg
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**

Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) or use package managers like Chocolatey:

```bash
choco install ffmpeg
```

**Verify Installation:**

```bash
ffmpeg -version
```

## Configuration System

The server uses Flask's configuration system with support for defaults and environment-specific overrides.

### Default Configuration

The default configuration is defined in `app/default_config.py`:

```python
DEFAULT_VOD_CONFIG = {
    "server": {
        "port": 8080,
        "host": "0.0.0.0",
        "debug": False
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
    }
}
```

### Instance Configuration

Following Flask best practices, instance-specific configurations are stored in the `instance/` folder:

1. **Base Instance Configuration** - `instance/config.py`:

   ```python
   # Flask configuration
   SECRET_KEY = "your-secret-key-here"  # Change this in production!
   
   # Homehub Configuration
   VOD_CONFIG = {
       "server": {
           "port": 8082,
           "host": "0.0.0.0",
           "debug": False
       },
       # Only include settings you want to override
   }
   ```

2. **Environment-specific Configuration** - `instance/config.development.py`:

   ```python
   # Development configuration
   SECRET_KEY = "dev-secret-key"
   
   VOD_CONFIG = {
       "server": {
           "port": 5000,
           "host": "127.0.0.1",
           "debug": True
       },
       "cache": {
           "ttl_seconds": 30  # Short cache for development
       }
   }
   ```

Only settings you want to override need to be included. Any settings not specified will fall back to the defaults.

## Usage

### Starting the server

With default configuration (production):

```bash
python run.py
```

With development configuration (loads `instance/config.development.py`):

```bash
python run.py -e development
```

You can create or edit `instance/config.py` and `instance/config.development.py` to override any settings for your environment.

## Architecture

The server follows a standard Flask application structure:

- `run.py`: Application entry point
- `app/`: Main application package
  - `__init__.py`: Flask app initialization
  - `routes.py`: Route definitions and handlers
  - `config.py`: Configuration management
  - `utils/`: Utility modules
    - `video_utils.py`: Video processing utilities
    - `cache_manager.py`: Cache management and video listing
  - `templates/`: HTML templates
  - `static/`: Static assets (CSS, JS, etc.)
- `instance/`: Instance-specific config (excluded from version control)

## Browser Access

Once running, access the server in your web browser:

- Default URL: `http://localhost:8082/`
- Replace 8082 with your configured port

## API Endpoints

### `/api/info`

Returns JSON describing the running server configuration. Useful for quick
diagnostics or to confirm the active settings.

Example:

```bash
curl http://localhost:8082/api/info
```

## Running Tests

To run the automated test suite install the dependencies and execute `pytest`:

```bash
pip install -r requirements.txt
pip install pytest
pytest -q
```
