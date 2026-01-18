"""
Stream processing service
Handles frame processing pipeline
"""
import os
import time
from typing import Dict, Any, List
from dataclasses import asdict

import numpy as np

from src.core.config import Config, StreamConfig
from src.core.errors import StreamNotFoundError, InvalidFrameError
from src.services.aws_services import S3Service, CloudWatchService
from src.models.specialist_interface import SpecialistInterface, DetectionResult
from src.models.cpu_specialist import CPUSpecialist


class StreamProcessor:
    """
    Main stream processor for video processing
    Orchestrates frame sampling, validation, ML inference, and actions
    """
    
    def __init__(self, cfg: Config, s3: S3Service, cloudwatch: CloudWatchService):
        self.config = cfg
        self.s3_service = s3
        self.cloudwatch_service = cloudwatch
        self.specialist: SpecialistInterface = None
        self.active_streams: Dict[str, StreamConfig] = {}
        self.stats = {
            'frames_processed': 0,
            'frames_sampled': 0,
            'total_detections': 0
        }
        
        self._initialize_specialist()
    
    def _initialize_specialist(self) -> None:
        """Initialize ML specialist"""
        print("Initializing ML specialist")
        
        try:
            model_config = self.config.to_model_config()
            self.specialist = CPUSpecialist('detector', model_config)
            
            # Download model from S3 if needed
            if self.config.s3_artifacts_bucket and not os.path.exists(self.config.model_path):
                os.makedirs(os.path.dirname(self.config.model_path), exist_ok=True)
                self.s3_service.download_model('models/detector.onnx', self.config.model_path)
            
            # Load model
            if os.path.exists(self.config.model_path):
                self.specialist.load_model()
                print("Specialist model loaded successfully")
            else:
                print("WARNING: Model file not found, specialist will not be available")
                
        except Exception as e:
            print(f"ERROR: Failed to initialize specialist: {e}")
            # Continue without model for graceful degradation
    
    def start_stream(self, stream_config: StreamConfig) -> Dict[str, Any]:
        """Start processing a stream"""
        print(f"Starting stream: {stream_config.stream_id}")
        self.active_streams[stream_config.stream_id] = stream_config
        
        return {
            'stream_id': stream_config.stream_id,
            'status': 'active',
            'config': asdict(stream_config)
        }
    
    def stop_stream(self, stream_id: str) -> Dict[str, Any]:
        """Stop processing a stream"""
        print(f"Stopping stream: {stream_id}")
        
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
        
        return {'stream_id': stream_id, 'status': 'stopped'}
    
    def process_frame(
        self,
        stream_id: str,
        frame: np.ndarray,
        frame_index: int
    ) -> Dict[str, Any]:
        """
        Process a video frame through the ML pipeline
        
        Args:
            stream_id: Unique stream identifier
            frame: RGB frame as numpy array
            frame_index: Frame sequence number
            
        Returns:
            Processing result with detections and actions
            
        Raises:
            StreamNotFoundError: If stream is not active
            InvalidFrameError: If frame validation fails
        """
        stream_config = self.active_streams.get(stream_id)
        if not stream_config:
            raise StreamNotFoundError(f"Stream not active: {stream_id}")
        
        self.stats['frames_processed'] += 1
        
        # Frame sampling - only process every Nth frame
        if frame_index % stream_config.frame_sample_rate != 0:
            return {
                'stream_id': stream_id,
                'frame_index': frame_index,
                'sampled': False,
                'detections': []
            }
        
        self.stats['frames_sampled'] += 1
        
        # Validate frame
        if not self._validate_frame(frame):
            raise InvalidFrameError(f"Invalid frame: {stream_id}/{frame_index}")
        
        # Run inference
        detections: List[DetectionResult] = []
        inference_metrics: Dict[str, float] = {}
        
        if self.specialist and self.specialist.is_loaded:
            try:
                detections = self.specialist.infer(frame)
                inference_metrics = self.specialist.get_metrics()
                
                # Filter by confidence and limit count
                detections = [
                    d for d in detections 
                    if d.confidence >= stream_config.min_confidence
                ][:stream_config.max_detections_per_frame]
                
                self.stats['total_detections'] += len(detections)
                
            except Exception as e:
                print(f"ERROR: Inference error: {e}")
        
        # Decide actions
        actions = self._decide_actions(stream_config, detections)
        
        # Execute actions
        if actions:
            self._execute_actions(stream_id, frame_index, frame, actions)
        
        # Publish metrics
        self._publish_metrics(stream_id, detections, inference_metrics)
        
        # Log detections
        print(f"DETECTION: stream={stream_id} frame={frame_index} detections={len(detections)} actions={actions}")
        
        return {
            'stream_id': stream_id,
            'frame_index': frame_index,
            'sampled': True,
            'detections': [asdict(d) for d in detections],
            'actions': actions,
            'metrics': inference_metrics
        }
    
    @staticmethod
    def _validate_frame(frame: np.ndarray) -> bool:
        """Validate frame quality and format"""
        if frame is None or frame.size == 0:
            return False
        
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            return False
        
        height, width = frame.shape[:2]
        if not (100 <= height <= 4096 and 100 <= width <= 4096):
            return False
        
        return True
    
    @staticmethod
    def _decide_actions(stream_config: StreamConfig, detections: List[DetectionResult]) -> List[str]:
        """Determine actions based on detections"""
        actions = []
        
        high_conf_detections = [d for d in detections if d.confidence > 0.8]
        
        if high_conf_detections:
            actions.append('alert')
        
        if len(detections) > 5:
            actions.append('save_clip')
        
        if stream_config.enable_clip_recording and detections:
            actions.append('record_clip')
        
        return actions
    
    def _execute_actions(
        self,
        stream_id: str,
        frame_index: int,
        frame: np.ndarray,
        actions: List[str]
    ) -> None:
        """Execute decided actions"""
        for action in actions:
            if action == 'save_clip':
                self.s3_service.save_frame(stream_id, frame_index, frame)
            elif action == 'alert':
                print(f"ALERT: High-confidence detection in {stream_id}/{frame_index}")
    
    def _publish_metrics(
        self,
        stream_id: str,
        detections: List[DetectionResult],
        inference_metrics: Dict[str, float]
    ) -> None:
        """Publish metrics to CloudWatch"""
        metrics = {
            'detection_count': len(detections),
            **inference_metrics
        }
        self.cloudwatch_service.publish_metrics(stream_id, metrics)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        specialist_metrics = {}
        if self.specialist and self.specialist.is_loaded:
            specialist_metrics = self.specialist.get_metrics()
        
        return {
            'active_streams': len(self.active_streams),
            'specialist_loaded': self.specialist.is_loaded if self.specialist else False,
            'specialist_metrics': specialist_metrics,
            **self.stats
        }
