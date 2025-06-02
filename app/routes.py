"""
Route definitions for the VOD application.
"""
from flask import Blueprint, render_template, send_from_directory, request, abort, jsonify
import os
import urllib.parse
import math

from app.utils.video_utils import decode_filename
from app.utils.cache_manager import get_paginated_videos, get_folders, find_videos, init_cache
from app.utils.video_utils import generate_thumbnail

# Create blueprint
main_bp = Blueprint('main', __name__)

# Helper function to detect JSON requests
def wants_json():
    """Check if the request wants JSON response"""
    # Check for explicit format parameter
    if request.args.get('format') == 'json':
        return True
    
    # Check Accept header
    return (request.headers.get('Accept', '').find('application/json') > 
            request.headers.get('Accept', '').find('text/html'))

# Helper function to format video data for JSON
def format_video_for_json(video, base_url=''):
    """Format video data for JSON response"""
    return {
        'id': video['rel_path'],  # Use relative path as ID
        'name': video['filename'],
        'path': video['rel_path'],
        'size': video.get('size', 0),
        'duration': video.get('duration', 'Unknown'),
        'thumbnail_url': f"/thumb/{video['thumb']}" if video.get('thumb') else None,
        'stream_url': f"/video/{urllib.parse.quote(video['rel_path'])}",
        'folder': os.path.dirname(video['rel_path']) or None,
        'modified_time': video.get('modified_time')
    }

# Helper function to format folders for JSON
def format_folders_for_json(folders):
    """Format folder data for JSON response"""
    return [{'name': folder, 'path': folder} for folder in folders]

# Access app config
def get_config():
    """Get the application configuration"""
    from app.config import get_config as get_app_config
    return get_app_config()

# Cache initialization flag
_cache_initialized = False

@main_bp.before_app_request
def setup_app_before_first_request():
    """Initialize app settings before the first request"""
    global _cache_initialized
    
    # Only run once
    if _cache_initialized:
        return
    
    # Get configuration from our new helper
    config = get_config()
    
    # Initialize cache with config
    init_cache(config)
    
    # Initial cache population
    root_dir = os.path.abspath(config['directories']['videos'])
    video_extensions = tuple(config['video']['extensions'])
    find_videos(root_dir, video_extensions, force_refresh=True)
    get_folders(root_dir, force_refresh=True)
    
    # Mark as initialized
    _cache_initialized = True

@main_bp.route("/")
@main_bp.route("/folder/<path:folder>")
def index(folder=''):
    """Main page route handling folder navigation with JSON support"""
    from flask import current_app
    config = current_app.config.get('VOD_CONFIG', {})
    
    # Get configuration values
    root_dir = os.path.abspath(config['directories']['videos'])
    web_assets_dir = os.path.abspath(config['directories']['web_assets'])
    thumb_dir = os.path.join(web_assets_dir, "thumbnails")
    videos_per_page = config['video']['per_page']
    video_extensions = tuple(config['video']['extensions'])
    
    # Get pagination data
    page = request.args.get('page', 1, type=int)
    pagination_data = get_paginated_videos(
        root_dir, thumb_dir, videos_per_page, video_extensions, page, folder
    )
    folders = get_folders(root_dir)
    
    # Return JSON if requested
    if wants_json():
        return jsonify({
            'videos': [format_video_for_json(video) for video in pagination_data['videos']],
            'folders': format_folders_for_json(folders),
            'pagination': {
                'current_page': pagination_data['current_page'],
                'total_pages': pagination_data['total_pages'],
                'total_videos': pagination_data['total_videos'],
                'per_page': videos_per_page
            },
            'current_folder': pagination_data['current_folder']
        })
    
    # Return HTML template for browser requests
    return render_template(
        "video_template.html",
        videos=pagination_data['videos'],
        current_page=pagination_data['current_page'],
        total_pages=pagination_data['total_pages'],
        total_videos=pagination_data['total_videos'],
        current_folder=pagination_data['current_folder'],
        folders=folders
    )

@main_bp.route("/video/<path:filename>")
def stream_video(filename):
    """Stream video file"""
    from flask import current_app
    config = current_app.config.get('VOD_CONFIG', {})
    root_dir = os.path.abspath(config['directories']['videos'])
    
    # Handle both URL-encoded and normal filenames
    try:
        # First try with the filename as-is
        return send_from_directory(root_dir, filename)
    except:
        try:
            # Try with URL decoding in case it's double-encoded
            decoded_filename = decode_filename(filename)
            return send_from_directory(root_dir, decoded_filename)
        except Exception as e:
            print(f"Error accessing file: {filename}, Error: {str(e)}")
            abort(404)

@main_bp.route("/thumb/<path:filename>")
def get_thumb(filename):
    """Get thumbnail for video"""
    from flask import current_app
    config = current_app.config.get('VOD_CONFIG', {})
    web_assets_dir = os.path.abspath(config['directories']['web_assets'])
    thumb_dir = os.path.join(web_assets_dir, "thumbnails")
    
    return send_from_directory(thumb_dir, filename)

@main_bp.route("/refresh")
def refresh_cache():
    """Refresh the video cache"""
    from flask import current_app, jsonify
    config = current_app.config.get('VOD_CONFIG', {})
    
    root_dir = os.path.abspath(config['directories']['videos'])
    video_extensions = tuple(config['video']['extensions'])
    
    find_videos(root_dir, video_extensions, force_refresh=True)
    get_folders(root_dir, force_refresh=True)
    
    return jsonify({
        'success': True,
        'message': 'Video cache refreshed successfully!'
    })

@main_bp.route("/search")
def search():
    """Search videos and folders by name with JSON support"""
    from flask import current_app
    config = current_app.config.get('VOD_CONFIG', {})
    root_dir = os.path.abspath(config['directories']['videos'])
    web_assets_dir = os.path.abspath(config['directories']['web_assets'])
    thumb_dir = os.path.join(web_assets_dir, "thumbnails")
    videos_per_page = config['video']['per_page']
    video_extensions = tuple(config['video']['extensions'])

    query = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    
    # Search videos
    all_videos = find_videos(root_dir, video_extensions, folder='')
    matched_videos = [v for v in all_videos if query in v['filename'].lower() or query in v['rel_path'].lower()]

    # Paginate
    total_videos = len(matched_videos)
    total_pages = max(1, math.ceil(total_videos / videos_per_page))
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * videos_per_page
    end_idx = min(start_idx + videos_per_page, total_videos)
    paginated_videos = matched_videos[start_idx:end_idx]
    for video in paginated_videos:
        video['thumb'] = generate_thumbnail(video['rel_path'], root_dir, thumb_dir)

    # Search folders
    folders = get_folders(root_dir)
    matched_folders = [f for f in folders if query in f.lower()]

    # Return JSON if requested
    if wants_json():
        return jsonify({
            'query': query,
            'results': {
                'videos': [format_video_for_json(video) for video in paginated_videos],
                'folders': [{'name': folder, 'path': folder} for folder in matched_folders]
            },
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_videos': total_videos,
                'per_page': videos_per_page
            },
            'total_results': len(matched_videos) + len(matched_folders)
        })

    # Return HTML template for browser requests
    return render_template(
        "video_template.html",
        videos=paginated_videos,
        current_page=page,
        total_pages=total_pages,
        total_videos=total_videos,
        current_folder='',
        folders=folders,
        search_query=query,
        matched_folders=matched_folders
    )

@main_bp.route("/folders")
def list_folders():
    """Get list of all folders (JSON only endpoint)"""
    from flask import current_app
    config = current_app.config.get('VOD_CONFIG', {})
    root_dir = os.path.abspath(config['directories']['videos'])
    
    folders = get_folders(root_dir)
    
    return jsonify({
        'folders': format_folders_for_json(folders),
        'total_folders': len(folders)
    })

@main_bp.route("/api/info")
def server_info():
    """Get server information (JSON only endpoint)"""
    from flask import current_app
    import socket
    
    # Log the request for debugging
    print(f"API Info request from: {request.remote_addr}, User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    config = current_app.config.get('VOD_CONFIG', {})
    
    # Get server IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
        s.close()
    except:
        server_ip = "localhost"
    
    response_data = {
        'server': {
            'name': config.get('server', {}).get('name', 'HomeHub'),
            'version': '1.0.0',
            'host': server_ip,
            'port': config.get('server', {}).get('port', 8080),
            'video_extensions': config['video']['extensions'],
            'videos_per_page': config['video']['per_page']
        },
        'discovery': {
            'bonjour_service': f"{config.get('discovery', {}).get('service_name', 'HomeHub')}.local",
            'service_type': '_homehub._tcp.local.'
        },
        'endpoints': {
            'videos': '/?format=json',
            'search': '/search?format=json',
            'folders': '/folders',
            'refresh_cache': '/refresh'
        }
    }
    
    # Create response with CORS headers
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    return response

@main_bp.route("/api/info", methods=['OPTIONS'])
def server_info_options():
    """Handle preflight OPTIONS requests for CORS"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response
