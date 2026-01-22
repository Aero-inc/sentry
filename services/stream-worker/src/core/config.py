"""
Configuration management for stream worker
"""
import os
from dataclasses import dataclass
from typing import Optional


# Model name constants
MODEL_NAMES = {
    'annotator': 'annotator.onnx',
    'cpu_specialist': 'cpu_specialist.onnx',
    'gpu_specialist': 'gpu_specialist.onnx',
}

# Local model storage directory
MODEL_WEIGHTS_DIR = '/app/src/models/weights'

# S3 model paths (prefix + model name)
S3_MODEL_PREFIX = 'models/'


@dataclass
class Config:
    """Application configuration"""
    # Environment
    environment: str
    aws_region: str
    
    # AWS Resources
    s3_artifacts_bucket: Optional[str]
    
    # Redis
    redis_host: Optional[str]
    redis_port: int
    redis_db: int
    
    # Application
    port: int
    log_level: str
    
    # Model Configuration
    model_input_size: tuple
    confidence_threshold: float
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            environment=os.getenv('ENVIRONMENT', 'staging'),
            aws_region=os.getenv('AWS_REGION', 'us-east-1'),
            s3_artifacts_bucket=os.getenv('S3_ARTIFACTS_BUCKET'),
            redis_host=os.getenv('REDIS_HOST'),
            redis_port=int(os.getenv('REDIS_PORT', '6379')),
            redis_db=int(os.getenv('REDIS_DB', '0')),
            port=int(os.getenv('PORT', '8080')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            model_input_size=tuple(map(int, os.getenv('MODEL_INPUT_SIZE', '640,640').split(','))),
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
        )
    
    @staticmethod
    def get_s3_model_key(model_type: str) -> str:
        """Get S3 key for a model type"""
        model_name = MODEL_NAMES.get(model_type, MODEL_NAMES['annotator'])
        return f"{S3_MODEL_PREFIX}{model_name}"
    
    @staticmethod
    def get_local_model_path(model_type: str, base_dir: str = MODEL_WEIGHTS_DIR) -> str:
        """Get local file path for a model type"""
        model_name = MODEL_NAMES.get(model_type, MODEL_NAMES['annotator'])
        return f"{base_dir}/{model_name}"


@dataclass
class StreamConfig:
    """Configuration for individual stream processing"""
    stream_id: str
    frame_sample_rate: int = 5
    min_confidence: float = 0.5
    max_detections_per_frame: int = 10
    enable_clip_recording: bool = False
