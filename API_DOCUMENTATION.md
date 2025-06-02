# HomeHub VOD Server API Documentation

## Overview

The HomeHub VOD Server provides a RESTful API for browsing, searching, and streaming video files. The API supports both JSON and HTML responses, with JSON responses available by adding `?format=json` parameter or setting the `Accept: application/json` header.

**Base URL:** `http://127.0.0.1:5000`

## Authentication

Currently, no authentication is required for API access.

## Content Negotiation

All endpoints that return HTML by default can return JSON by:

- Adding `?format=json` query parameter
- Setting `Accept: application/json` header

## Endpoints

### 1. Server Information

```http
GET /api/info
```

Get server configuration and available endpoints.

**Response:**

```json
{
  "server": {
    "name": "HomeHub VOD Server",
    "version": "1.0.0",
    "video_extensions": [".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".flv", ".wmv"],
    "videos_per_page": 10
  },
  "endpoints": {
    "videos": "/?format=json",
    "search": "/search?format=json",
    "folders": "/folders",
    "refresh_cache": "/refresh"
  }
}
```

### 2. List Videos

```http
GET /?format=json
GET /?format=json&page={page_number}
```

Get paginated list of all videos.

**Parameters:**

- `format` (optional): Set to "json" for JSON response
- `page` (optional): Page number for pagination (default: 1)

**Response:**

```json
{
  "videos": [
    {
      "id": "folder/video.mp4",
      "name": "video.mp4",
      "path": "folder/video.mp4",
      "size": 0,
      "duration": "Unknown",
      "thumbnail_url": "/thumb/folder_video.mp4.jpg",
      "stream_url": "/video/folder/video.mp4",
      "folder": "folder",
      "modified_time": null
    }
  ],
  "folders": [
    {
      "name": "folder_name",
      "path": "folder_name"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 38,
    "total_videos": 372,
    "per_page": 10
  },
  "current_folder": ""
}
```

### 3. Browse Folder

```http
GET /folder/{folder_path}?format=json
GET /folder/{folder_path}?format=json&page={page_number}
```

Get videos within a specific folder.

**Parameters:**

- `folder_path`: URL-encoded path to the folder
- `format` (optional): Set to "json" for JSON response
- `page` (optional): Page number for pagination (default: 1)

**Response:**

Same structure as List Videos, but filtered to the specified folder.

### 4. List Folders

```http
GET /folders
```

Get list of all available folders (JSON only endpoint).

**Response:**

```json
{
  "folders": [
    {
      "name": "folder1",
      "path": "folder1"
    },
    {
      "name": "folder2",
      "path": "folder2"
    }
  ],
  "total_folders": 16
}
```

### 5. Search Videos

```http
GET /search?format=json&q={query}
GET /search?format=json&q={query}&page={page_number}
```

Search videos and folders by name.

**Parameters:**

- `q`: Search query string
- `format` (optional): Set to "json" for JSON response
- `page` (optional): Page number for pagination (default: 1)

**Response:**

```json
{
  "query": "search_term",
  "results": {
    "videos": [
      {
        "id": "folder/matching_video.mp4",
        "name": "matching_video.mp4",
        "path": "folder/matching_video.mp4",
        "size": 0,
        "duration": "Unknown",
        "thumbnail_url": "/thumb/folder_matching_video.mp4.jpg",
        "stream_url": "/video/folder/matching_video.mp4",
        "folder": "folder",
        "modified_time": null
      }
    ],
    "folders": [
      {
        "name": "matching_folder",
        "path": "matching_folder"
      }
    ]
  },
  "pagination": {
    "current_page": 1,
    "total_pages": 15,
    "total_videos": 142,
    "per_page": 10
  },
  "total_results": 144
}
```

### 6. Stream Video

```http
GET /video/{video_path}
```

Stream a video file.

**Parameters:**

- `video_path`: URL-encoded relative path to the video file

**Response:**

- Binary video stream
- Content-Type set based on file extension
- Supports HTTP range requests for seeking

### 7. Get Thumbnail

```http
GET /thumb/{thumbnail_filename}
```

Get thumbnail image for a video.

**Parameters:**

- `thumbnail_filename`: Generated thumbnail filename

**Response:**

- Binary image data (typically JPEG)

### 8. Refresh Cache

```http
GET /refresh
```

Refresh the video cache (scans for new/deleted files).

**Response:**

```json
{
  "success": true,
  "message": "Video cache refreshed successfully!"
}
```

## Video Object Schema

Each video object in API responses contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (relative path) |
| `name` | string | Filename |
| `path` | string | Relative path from videos root |
| `size` | number | File size in bytes |
| `duration` | string | Video duration (currently "Unknown") |
| `thumbnail_url` | string\|null | URL to thumbnail image |
| `stream_url` | string | URL to stream the video |
| `folder` | string\|null | Parent folder name |
| `modified_time` | string\|null | Last modified timestamp |

## Pagination Schema

Pagination information is included in list responses:

| Field | Type | Description |
|-------|------|-------------|
| `current_page` | number | Current page number |
| `total_pages` | number | Total number of pages |
| `total_videos` | number | Total number of videos |
| `per_page` | number | Videos per page (default: 10) |

## Error Responses

### 404 Not Found

Returned when requesting non-existent endpoints or files.

```html
<!doctype html>
<html lang=en>
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server.</p>
```

## Example Usage

### cURL Examples

```bash
# Get server info
curl "http://127.0.0.1:5000/api/info"

# List all videos (first page)
curl "http://127.0.0.1:5000/?format=json"

# Get second page of videos
curl "http://127.0.0.1:5000/?format=json&page=2"

# Browse specific folder
curl "http://127.0.0.1:5000/folder/angelsetfree?format=json"

# Search for videos containing "angel"
curl "http://127.0.0.1:5000/search?format=json&q=angel"

# Get all folders
curl "http://127.0.0.1:5000/folders"

# Refresh cache
curl "http://127.0.0.1:5000/refresh"

# Stream a video
curl "http://127.0.0.1:5000/video/folder/video.mp4" -o video.mp4
```

### JavaScript Fetch Examples

```javascript
// Get server info
const serverInfo = await fetch('/api/info').then(r => r.json());

// List videos with pagination
const videos = await fetch('/?format=json&page=1').then(r => r.json());

// Search videos
const searchResults = await fetch('/search?format=json&q=angel').then(r => r.json());

// Get folders
const folders = await fetch('/folders').then(r => r.json());

// Refresh cache
const refreshResult = await fetch('/refresh').then(r => r.json());
```

## Rate Limiting

Currently, no rate limiting is implemented.

## CORS

Cross-Origin Resource Sharing (CORS) headers are not explicitly set. The server accepts requests from any origin when running in development mode.

## Notes

- Video duration extraction is not currently implemented (always returns "Unknown")
- File sizes are not populated (always return 0)
- Thumbnail generation requires ffmpeg to be installed
- The server supports common video formats: MP4, MOV, MKV, AVI, M4V, WebM, FLV, WMV
