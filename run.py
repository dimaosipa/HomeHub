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

    log_dir = os.path.abspath('logs')
    os.makedirs(log_dir, exist_ok=True)
    logfile = os.path.join(log_dir, f'homehub_{os.getpid()}.log')

    parser = argparse.ArgumentParser(description='Homehub')
    parser.add_argument('-e', '--env', help='Environment (development, production)', default='production')
    parser.add_argument('--no-discovery', action='store_true', help='Disable service discovery')
    args = parser.parse_args()

    if args.env:
        os.environ['FLASK_ENV'] = args.env
        if args.env.lower() == 'development':
            os.environ['FLASK_DEBUG'] = '1'
        else:
            os.environ['FLASK_DEBUG'] = '0'

    app = create_app()
    with app.app_context():
        from app.config import get_config
        config = get_config()
        debug_mode = config['server'].get('debug', False)

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
        format='%(asctime)s %(levelname)s: %(message)s',
    )

    if shutil.which('ffmpeg') is None:
        logging.error(
            "ERROR: ffmpeg is not installed or not found in PATH. "
            "Please install ffmpeg to use this server."
        )
        sys.exit(1)

    atexit.register(cleanup_service)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    with app.app_context():
        from app.config import get_config
        config = get_config()

        root_dir = os.path.abspath(config['directories']['videos'])
        web_assets_dir = os.path.abspath(config['directories']['web_assets'])
        thumb_dir = os.path.join(web_assets_dir, "thumbnails")

        try:
            os.makedirs(root_dir, exist_ok=True)
            os.makedirs(web_assets_dir, exist_ok=True)
            os.makedirs(thumb_dir, exist_ok=True)
        except OSError as e:
            logging.error("ERROR: Unable to create required directories: %s", e)
            sys.exit(1)

        for path in (root_dir, web_assets_dir, thumb_dir):
            if not (os.access(path, os.R_OK) and os.access(path, os.W_OK)):
                logging.error("ERROR: Insufficient permissions for directory %s", path)
                sys.exit(1)

        logging.info("🏠 Homehub Configuration:")
        logging.info("- Environment: %s", os.environ.get('FLASK_ENV', 'production'))
        logging.info("- Videos directory: %s", root_dir)
        logging.info("- Web assets directory: %s", web_assets_dir)
        logging.info("- Supported extensions: %s", ', '.join(config['video']['extensions']))
        logging.info("- Videos per page: %s", config['video']['per_page'])

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
                    "Service discovery not available. Install the 'zeroconf' package "
                    "for network discovery."
                )
            except Exception as e:
                logging.warning("Service discovery failed: %s", e)

        logging.info(
            "\n🚀 Starting HomeHub server on %s:%s",
            config['server']['host'],
            config['server']['port'],
        )

        try:
            app.run(
                host=config['server']['host'],
                port=config['server']['port'],
                debug=config['server']['debug'],
            )
        except KeyboardInterrupt:
            logging.info("\n🛑 Server stopped by user")
        finally:
            cleanup_service()


if __name__ == "__main__":
    main()
