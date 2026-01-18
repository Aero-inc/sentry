"""
Configuration management for stream worker
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration"""
    # Environment
    environment: str
    aws_region: str
    
    # AWS Resources
    s3_artifacts_bucket: Optional[str]
    s3_clips_bucket: Optional[str]
    
    # Application
    port: int
    log_level: str
    
    # Model
    model_path: str
    model_type: str
    model_input_size: tuple
    confidence_threshold: float
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            environment=os.getenv('ENVIRONMENT', 'dev'),
            aws_region=os.getenv('AWS_REGION', 'us-east-1'),
            s3_artifacts_bucket=os.getenv('S3_ARTIFACTS_BUCKET'),
            s3_clips_bucket=os.getenv('S3_CLIPS_BUCKET'),
            port=int(os.getenv('PORT', '8080')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            model_path=os.getenv('MODEL_PATH', '/models/detector.onnx'),
            model_type=os.getenv('MODEL_TYPE', 'onnx'),
            model_input_size=tuple(map(int, os.getenv('MODEL_INPUT_SIZE', '640,640').split(','))),
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', '0.5'))
        )
    
    def to_model_config(self) -> dict:
        """Convert to model specialist configuration"""
        return {
            'model_path': self.model_path,
            'model_type': self.model_type,
            'confidence_threshold': self.confidence_threshold,
            'input_size': self.model_input_size
        }


@dataclass
class StreamConfig:
    """Configuration for individual stream processing"""
    stream_id: str
    frame_sample_rate: int = 5
    min_confidence: float = 0.5
    max_detections_per_frame: int = 10
    enable_clip_recording: bool = False
    clip_duration_seconds: int = 10
