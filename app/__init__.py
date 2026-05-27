"""
Video on Demand (VOD) application package initialization.
"""
from flask import Flask
from flask import send_from_directory, render_template, abort, request
import os
import sys
from app.default_config import DEFAULT_VOD_CONFIG

def create_app(test_config=None):
    """
    Create and configure the Flask application instance.
    
    Args:
        test_config: Test configuration to override default configuration
        
    Returns:
        The configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__, instance_relative_config=True)
    
    # Load default configuration
    app.config.from_mapping(
        SECRET_KEY='dev',
        VOD_CONFIG=DEFAULT_VOD_CONFIG
    )

    # Load instance configuration if it exists
    if test_config is None:
        config_path = os.path.join(app.instance_path, 'config.py')
        if os.path.exists(config_path):
            try:
                app.config.from_pyfile('config.py', silent=False)
            except Exception as e:
                print(f"ERROR: Failed to load {config_path}: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Support for environment-specific config
    env = os.environ.get('FLASK_ENV', 'production')
    if env != 'production':
        env_config = os.path.join(app.instance_path, f'config.{env}.py')
        if os.path.exists(env_config):
            try:
                app.config.from_pyfile(f'config.{env}.py', silent=False)
            except Exception as e:
                print(f"ERROR: Failed to load {env_config}: {e}", file=sys.stderr)
                sys.exit(1)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Import and register blueprints/routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
