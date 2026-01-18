"""
AWS service integrations
"""
import boto3
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
import cv2


class S3Service:
    """Handle S3 operations"""
    
    def __init__(self, artifacts_bucket: Optional[str]):
        self.artifacts_bucket = artifacts_bucket
        self.client = boto3.client('s3') if artifacts_bucket else None
    
    def download_model(self, s3_key: str, local_path: str) -> bool:
        """Download model from S3"""
        if not self.artifacts_bucket or not self.client:
            print("WARNING: S3 artifacts bucket not configured")
            return False
        
        try:
            print(f"Downloading model from s3://{self.artifacts_bucket}/{s3_key}")
            self.client.download_file(self.artifacts_bucket, s3_key, local_path)
            print(f"Model downloaded to {local_path}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to download model: {e}")
            return False
    
    def save_frame(self, stream_id: str, frame_index: int, frame: np.ndarray) -> Optional[str]:
        """Save frame to S3 clips bucket"""
        if not self.clips_bucket or not self.client:
            return None
        
        try:
            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            # Generate S3 key
            key = f"{stream_id}/{datetime.utcnow().strftime('%Y%m%d')}/frame_{frame_index:08d}.jpg"
            
            # Upload
            self.client.put_object(
                Bucket=self.clips_bucket,
                Key=key,
                Body=buffer.tobytes(),
                ContentType='image/jpeg'
            )
            
            print(f"Frame saved to s3://{self.clips_bucket}/{key}")
            return key
        except Exception as e:
            print(f"ERROR: Failed to save frame to S3: {e}")
            return None


class CloudWatchService:
    """Handle CloudWatch metrics and logs"""
    
    def __init__(self, environment: str):
        self.environment = environment
        self.client = boto3.client('cloudwatch')
        self.namespace = 'Sentry/StreamWorker'
    
    def publish_metrics(self, stream_id: str, metrics: Dict[str, float]) -> None:
        """Publish custom metrics to CloudWatch"""
        try:
            metric_data = []
            
            # Detection count
            if 'detection_count' in metrics:
                metric_data.append({
                    'MetricName': 'DetectionCount',
                    'Value': metrics['detection_count'],
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'StreamId', 'Value': stream_id},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                })
            
            # Inference latency
            if 'inference_time_ms' in metrics:
                metric_data.append({
                    'MetricName': 'InferenceLatency',
                    'Value': metrics['inference_time_ms'],
                    'Unit': 'Milliseconds',
                    'Dimensions': [
                        {'Name': 'StreamId', 'Value': stream_id},
                        {'Name': 'Environment', 'Value': self.environment}
                    ]
                })
            
            if metric_data:
                self.client.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data
                )
        except Exception as e:
            print(f"ERROR: Failed to publish metrics: {e}")
