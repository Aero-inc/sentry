"""
Stream Worker - Main Application Entry Point
Provides REST API for video stream processing with ML inference
"""
from flask import Flask
from flask_cors import CORS

from src.core.config import Config
from src.services.aws_services import S3Service, CloudWatchService
from src.services.stream_processor import StreamProcessor
from src.api.routes import api_bp, init_routes


def create_app() -> Flask:
    """Application factory"""
    print("Starting Stream Worker")
    
    # Load configuration
    config = Config.from_env()
    print(f"Environment: {config.environment}")
    
    # Initialize AWS services
    s3_service = S3Service(config.s3_artifacts_bucket)
    cloudwatch_service = CloudWatchService(config.environment)
    
    # Initialize stream processor
    processor = StreamProcessor(config, s3_service, cloudwatch_service)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Enable CORS for all origins (can be restricted to specific origins in production)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Register routes
    init_routes(processor)
    app.register_blueprint(api_bp)
    
    print("Stream Worker initialized successfully")
    
    return app


# Create app instance (used by both gunicorn and direct execution)
app = create_app()


if __name__ == '__main__':
    # Reuse the already-created app instance
    port = Config.from_env().port
    app.run(host='0.0.0.0', port=port, debug=False)
