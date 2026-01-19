"""
AWS service integrations
"""
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
import cv2
import numpy as np


class S3Service:
    """Handle S3 operations for model storage and artifacts"""
    
    def __init__(self, artifacts_bucket: Optional[str], region: str = 'us-east-1'):
        self.artifacts_bucket = artifacts_bucket
        self.region = region
        self.client = boto3.client('s3', region_name=region) if artifacts_bucket else None
    
    def download_model(self, s3_key: str, local_path: str):
        """Download model from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save the model
            
        Returns:
            True if successful, False otherwise
        """
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

class CloudWatchService:
    """Handle CloudWatch metrics"""
    
    NAMESPACE = 'Sentry/StreamWorker'
    
    def __init__(self, environment: str, region: str = 'us-east-1'):
        self.environment = environment
        self.region = region
        self.client = boto3.client('cloudwatch', region_name=region)
    
    def publish_metrics(self, stream_id: str, metrics: Dict[str, float]):
        """Publish custom metrics to CloudWatch
        
        Args:
            stream_id: Stream identifier
            metrics: Dictionary of metric names to values
        """
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
                    Namespace=self.NAMESPACE,
                    MetricData=metric_data
                )
        except Exception as e:
            print(f"ERROR: Failed to publish metrics: {e}")
