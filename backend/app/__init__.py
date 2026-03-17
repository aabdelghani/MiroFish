"""
MiroFish Backend - Flask application factory.
MiroFish backend Flask application factory.
"""

import os
import warnings

# Suppress multiprocessing resource_tracker warnings (from third-party libs e.g. transformers).
# Must be set before any other imports.
# Suppress multiprocessing resource_tracker warnings from third-party libraries.
# This needs to run before the rest of the imports.
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # JSON: ensure Unicode is not escaped (e.g. for non-ASCII)
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    logger = setup_logger('mirofish')

    # Log startup only in reloader child (avoid duplicate in debug)
    """Create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Keep JSON responses readable instead of forcing Unicode escapes.
    # Flask >= 2.3 uses app.json.ensure_ascii; older versions use JSON_AS_ASCII.
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Configure logging.
    logger = setup_logger('mirofish')
    
    # Only print startup logs in the reloader subprocess to avoid duplicates.
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend starting...")
        logger.info("=" * 50)

    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": config_class.CORS_ORIGINS}})

    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Simulation process cleanup registered")

        logger.info("Starting MiroFish backend...")
        logger.info("=" * 50)
        logger.info("Simulation process cleanup handler registered")
    
    # Enable CORS.
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register simulation-process cleanup so all child processes stop on shutdown.
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Registered simulation process cleanup")
    
        logger.info("Starting MiroFish backend...")
        logger.info("=" * 50)
    
    # Enable CORS.
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register simulation-process cleanup so all child processes stop on shutdown.
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Registered simulation process cleanup")
    
    # Request logging middleware.
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"响应: {response.status_code}")
        logger.debug(f"Response: {response.status_code}")
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

            logger.debug(f"Request body: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
            logger.debug(f"Request body: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Response: {response.status_code}")
        return response
    
    # Register blueprints.
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}

    # 根路由 - 返回服务信息和可用端点
    @app.route('/')
    def index():
        return {
            'service': 'MiroFish Backend',
            'status': 'running',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'api': {
                    'graph': '/api/graph',
                    'simulation': '/api/simulation',
                    'report': '/api/report'
                }
            }
        }

    if should_log_startup:
        logger.info("MiroFish Backend started")

    
    # Health check.
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    if should_log_startup:
        logger.info("MiroFish backend startup complete")
        logger.info("MiroFish Backend started")
    
    return app
