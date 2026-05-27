#!/usr/bin/env python3
"""
Homehub - Main entry point
"""
import os
import logging
from logging.handlers import RotatingFileHandler
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
        _service_discovery = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info("\n🛑 Shutting down HomeHub server...")
    cleanup_service()
    sys.exit(0)

def main():
    """Main entry point for the application"""
    global _service_discovery

    # Setup logging: unique log file per instance with rotation
    log_dir = os.path.abspath('logs')
    os.makedirs(log_dir, exist_ok=True)
    logfile = os.path.join(log_dir, f'homehub_{os.getpid()}.log')

    # Parse command line arguments early to check for debug mode
    parser = argparse.ArgumentParser(description='Homehub')
    parser.add_argument('-e', '--env', help='Environment (development, production)', default='production')
    parser.add_argument('--no-discovery', action='store_true', help='Disable service discovery')
    args, unknown = parser.parse_known_args()

    # Set Flask debug environment variable for Flask 2.3+
    if args.env:
        if args.env.lower() == 'development':
            os.environ['FLASK_DEBUG'] = '1'
        else:
            os.environ['FLASK_DEBUG'] = '0'

    # Create Flask application (needed to get config)
    app = create_app()
    with app.app_context():
        from app.config import get_config
        config = get_config()
        debug_mode = config['server'].get('debug', False)

    # Set logging level based on debug mode
    log_level = logging.DEBUG if debug_mode else logging.INFO
    file_handler = RotatingFileHandler(logfile, maxBytes=5_000_000, backupCount=5)
    handlers = [file_handler]
    if debug_mode:
        console_handler = logging.StreamHandler(sys.__stdout__)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        handlers.append(console_handler)
    logging.basicConfig(
        handlers=handlers,
        level=log_level,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

    # Redirect all print output (stdout/stderr) to the same rotating log file
    log_print_file = open(logfile, 'a')
    sys.stdout = log_print_file
    sys.stderr = log_print_file

    # Re-create app and config in the correct context for the rest of the function
    app = create_app()
    with app.app_context():
        from app.config import get_config
        config = get_config()

    # Check for ffmpeg
    if shutil.which('ffmpeg') is None:
        logging.error("ERROR: ffmpeg is not installed or not found in PATH. Please install ffmpeg to use this server.")
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

        # Log server information
        logging.info("🏠 Homehub Configuration:")
        logging.info(f"- Environment: {os.environ.get('FLASK_ENV', 'production')}")
        logging.info(f"- Videos directory: {root_dir}")
        logging.info(f"- Web assets directory: {web_assets_dir}")
        logging.info(f"- Supported extensions: {', '.join(config['video']['extensions'])}")
        logging.info(f"- Videos per page: {config['video']['per_page']}")

        # Start service discovery (skip werkzeug reloader parent to avoid duplicate ads)
        discovery_enabled = (
            not args.no_discovery
            and config.get('discovery', {}).get('enabled', True)
            and (not debug_mode or os.environ.get('WERKZEUG_RUN_MAIN') == 'true')
        )
        if discovery_enabled:
            try:
                from app.utils.service_discovery import start_service_discovery
                service_name = config.get('discovery', {}).get(
                    'service_name', config['server'].get('name', 'HomeHub')
                )
                _service_discovery = start_service_discovery(
                    config['server']['host'],
                    config['server']['port'],
                    service_name,
                )
            except ImportError:
                logging.warning(
                    "Service discovery not available. Install the 'zeroconf' package for network discovery."
                )
            except Exception as e:
                logging.warning("Service discovery failed: %s", e)

        logging.info(f"\n🚀 Starting HomeHub server on {config['server']['host']}:{config['server']['port']}")
        
        # Start the server
        try:
            app.run(
                host=config['server']['host'],
                port=config['server']['port'],
                debug=config['server']['debug']
            )
        except KeyboardInterrupt:
            logging.info("\n🛑 Server stopped by user")
        finally:
            cleanup_service()

if __name__ == "__main__":
    main()
