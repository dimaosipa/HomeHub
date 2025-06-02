#!/usr/bin/env python3
"""
Homehub - Main entry point
"""
import os
import argparse
import sys
import shutil
import signal
import atexit
from app import create_app

# Global service discovery instance
_service_discovery = None

def cleanup_service():
    """Cleanup function for service discovery"""
    global _service_discovery
    if _service_discovery:
        from app.utils.service_discovery import stop_service_discovery
        stop_service_discovery()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down HomeHub server...")
    cleanup_service()
    sys.exit(0)

def main():
    """Main entry point for the application"""
    global _service_discovery
    
    # Check for ffmpeg
    if shutil.which('ffmpeg') is None:
        print("ERROR: ffmpeg is not installed or not found in PATH. Please install ffmpeg to use this server.", file=sys.stderr)
        sys.exit(1)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Homehub')
    parser.add_argument('-e', '--env', help='Environment (development, production)', default='production')
    parser.add_argument('--no-discovery', action='store_true', help='Disable service discovery')
    args = parser.parse_args()

    # Set Flask environment
    if args.env:
        os.environ['FLASK_ENV'] = args.env

    # Register cleanup handlers
    atexit.register(cleanup_service)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create Flask application
    app = create_app()

    # Use application context to access config
    with app.app_context():
        from app.config import get_config
        config = get_config()

        # Create necessary directories
        root_dir = os.path.abspath(config['directories']['videos'])
        web_assets_dir = os.path.abspath(config['directories']['web_assets'])
        thumb_dir = os.path.join(web_assets_dir, "thumbnails")

        os.makedirs(root_dir, exist_ok=True)
        os.makedirs(web_assets_dir, exist_ok=True)
        os.makedirs(thumb_dir, exist_ok=True)

        # Print server information
        print(f"🏠 Homehub Configuration:")
        print(f"- Environment: {os.environ.get('FLASK_ENV', 'production')}")
        print(f"- Videos directory: {root_dir}")
        print(f"- Web assets directory: {web_assets_dir}")
        print(f"- Supported extensions: {', '.join(config['video']['extensions'])}")
        print(f"- Videos per page: {config['video']['per_page']}")

        # Start service discovery
        if not args.no_discovery and config.get('discovery', {}).get('enabled', True):
            try:
                from app.utils.service_discovery import start_service_discovery
                service_name = config.get('discovery', {}).get('service_name', config['server'].get('name', 'HomeHub'))
                _service_discovery = start_service_discovery(
                    config['server']['host'],
                    config['server']['port'],
                    service_name
                )
            except ImportError:
                print("⚠️  Service discovery not available. Install 'zeroconf' package for network discovery.")
            except Exception as e:
                print(f"⚠️  Service discovery failed: {e}")

        print(f"\n🚀 Starting HomeHub server on {config['server']['host']}:{config['server']['port']}")
        
        # Start the server
        try:
            app.run(
                host=config['server']['host'],
                port=config['server']['port'],
                debug=config['server']['debug']
            )
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        finally:
            cleanup_service()

if __name__ == "__main__":
    main()
