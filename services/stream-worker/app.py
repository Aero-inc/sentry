"""
Stream Worker - Main Application Entry Point
Provides REST API for video stream processing with ML inference
"""
from typing import Optional

from flask import Flask
from flask_cors import CORS

from src.api.routes import api_bp, init_routes
from src.core.config import Config
from src.services.aws_services import S3Service, CloudWatchService
from src.services.stream_processor import StreamProcessor


def create_app(config: Optional[Config] = None):
    """Application factory
    
    Args:
        config: Configuration object. If None, loads from environment.
        
    Returns:
        Configured Flask application
    """
    print("Starting Stream Worker")
    
    # Load configuration
    cfg = config or Config.from_env()
    print(f"Environment: {cfg.environment}")
    
    # Initialize AWS services
    s3_service = S3Service(cfg.s3_artifacts_bucket, cfg.aws_region)
    cloudwatch_service = CloudWatchService(cfg.environment, cfg.aws_region)
    
    # Initialize stream processor
    processor = StreamProcessor(cfg, s3_service, cloudwatch_service)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Register routes
    init_routes(processor)
    app.register_blueprint(api_bp)
    
    print("Stream Worker initialized successfully")
    
    return app


# Create app instance (used by gunicorn)
app = create_app()


if __name__ == '__main__':
    config = Config.from_env()
    config.local_only = True  # For local testing
    config.specialists = False  # Until CPU specialist is implemented
    app.run(host='0.0.0.0', port=config.port, debug=False)
