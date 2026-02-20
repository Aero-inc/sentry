"""
Stream processing service
Handles frame processing pipeline
"""
import os
import time
from dataclasses import asdict
from typing import Any, Dict, List, Callable, Optional

import numpy as np

from src.core.config import Config, StreamConfig, MODEL_WEIGHTS_DIR
from src.core.errors import StreamNotFoundError, InvalidFrameError
from src.models.annotation_model import AnnotationModel, Annotation
from src.models.cpu_specialist import CPUSpecialist
from src.models.specialist_interface import SpecialistInterface, DetectionResult
from src.services.aws_services import S3Service, CloudWatchService
from src.services.decision_maker import DecisionMaker, SpecialistDecision
from src.services.redis_service import RedisService


class StreamProcessor:
    """
    Main stream processor for video processing
    Pipeline: Annotation → Decision Maker → Specialist Models → Actions
    """

    # Frame validation constants
    MIN_FRAME_DIM = 100
    MAX_FRAME_DIM = 4096
    EXPECTED_CHANNELS = 3

    def __init__(self, cfg: Config, s3: S3Service, cloudwatch: CloudWatchService):
        self.config = cfg
        self.s3_service = s3
        self.cloudwatch_service = cloudwatch
        
        # Initialize Redis for distributed state
        self.redis = RedisService(cfg.redis_host, cfg.redis_port, cfg.redis_db)
        
        # Fallback to in-memory if Redis unavailable
        self.active_streams: Dict[str, StreamConfig] = {}
        
        if self.redis.enabled:
            print("✓ Stream processor using Redis for distributed state")
        else:
            print("⚠ WARNING: Stream processor using in-memory dict (not production-ready)")
            print("⚠ WARNING: Multiple workers will not share state!")
        
        # Pipeline components
        self.annotation_model: Optional[AnnotationModel] = None
        self.decision_maker: Optional[DecisionMaker] = None
        self.specialists: Dict[str, SpecialistInterface] = {}
        
        self.stats = {
            'frames_processed': 0,
            'frames_sampled': 0,
            'frames_annotated': 0,
            'total_detections': 0,
            'specialist_invocations': 0
        }
        
        self._initialize_pipeline()
    
    def _initialize_pipeline(self) -> None:
        """Initialize annotation model, decision maker, and specialists"""
        print("Initializing ML pipeline")
        
        try:
            # Initialize annotation model
            annotator_path = self.config.get_local_model_path('annotator')
            annotation_config = {
                'annotation_model_path': annotator_path,
                'annotation_input_size': self.config.model_input_size,
                'annotation_confidence_threshold': 0.3
            }
            self.annotation_model = AnnotationModel(annotation_config)
            
            # Download models from S3 on startup
            if not self.config.local_only and self.config.s3_artifacts_bucket:
                print(f"Downloading models from S3: {self.config.s3_artifacts_bucket}")
                os.makedirs(MODEL_WEIGHTS_DIR, exist_ok=True)
                
                # Download annotator model
                annotator_s3_key = self.config.get_s3_model_key('annotator')
                if not self.s3_service.download_model(annotator_s3_key, annotator_path):
                    print(f"WARNING: Could not download {annotator_s3_key}, will run without model")
                
                # Download specialist models
                cpu_specialist_path = self.config.get_local_model_path('cpu_specialist')
                cpu_specialist_s3_key = self.config.get_s3_model_key('cpu_specialist')
                if not self.s3_service.download_model(cpu_specialist_s3_key, cpu_specialist_path):
                    print(f"WARNING: Could not download {cpu_specialist_s3_key}, will run without specialist model")
            
            # Load annotation model
            if os.path.exists(annotator_path):
                self.annotation_model.load_model()
                print("Annotation model loaded successfully")
            else:
                print("WARNING: Annotation model file not found")
            
            # Initialize decision maker
            decision_config = {
                'high_priority_objects': ['person', 'vehicle', 'object_0'],
                'confidence_threshold_specialist': 0.7,
                'min_annotations_for_specialist': 1
            }
            self.decision_maker = DecisionMaker(decision_config)
            print("Decision maker initialized")
            
            # Initialize specialists
            self._initialize_specialists()
            
            print("ML pipeline initialized successfully")
            
        except Exception as e:
            print(f"ERROR: Failed to initialize pipeline: {e}")
            # Continue without models for graceful degradation
    
    def _initialize_specialists(self) -> None:
        """Initialize specialist models"""
        try:
            # Initialize CPU specialist
            cpu_specialist_path = self.config.get_local_model_path('cpu_specialist')
            model_config = {
                'model_path': cpu_specialist_path,
                'confidence_threshold': self.config.confidence_threshold,
                'input_size': self.config.model_input_size,
                'specialists': self.config.specialists
            }
            cpu_specialist = CPUSpecialist('cpu_detector', model_config)
            
            if os.path.exists(cpu_specialist_path):
                cpu_specialist.load_model()
                self.specialists['cpu_detector'] = cpu_specialist
                print("CPU specialist loaded successfully")
            else:
                print("WARNING: CPU specialist model file not found")
                
        except Exception as e:
            print(f"ERROR: Failed to initialize specialists: {e}")
    
    def start_stream(self, stream_config: StreamConfig) -> Dict[str, Any]:
        """Start processing a stream"""
        print(f"Starting stream: {stream_config.stream_id}")
        
        # Store in Redis if available, otherwise in-memory
        if self.redis.enabled:
            success = self.redis.set_stream(stream_config.stream_id, asdict(stream_config))
            if not success:
                print(f"WARNING: Failed to store stream {stream_config.stream_id} in Redis, using in-memory fallback")
                self.active_streams[stream_config.stream_id] = stream_config
        else:
            self.active_streams[stream_config.stream_id] = stream_config
        
        return {
            'stream_id': stream_config.stream_id,
            'status': 'active',
            'config': asdict(stream_config)
        }
    
    def stop_stream(self, stream_id: str) -> Dict[str, Any]:
        """Stop processing a stream"""
        print(f"Stopping stream: {stream_id}")
        
        # Remove from Redis if available, otherwise from in-memory
        if self.redis.enabled:
            self.redis.delete_stream(stream_id)
        else:
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
        # Retrieve stream config from Redis or in-memory
        if self.redis.enabled:
            stream_data = self.redis.get_stream(stream_id)
            if not stream_data:
                raise StreamNotFoundError(f"Stream not active: {stream_id}")
            stream_config = StreamConfig(**stream_data)
        else:
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
        
        # PIPELINE STEP 1: Annotation Model
        annotations: List[Annotation] = []
        annotation_metrics: Dict[str, float] = {}
        
        if self.annotation_model and self.annotation_model.is_loaded:
            try:
                annotations = self.annotation_model.annotate(frame)
                annotation_metrics = self.annotation_model.get_metrics()
                self.stats['frames_annotated'] += 1
                print(f"ANNOTATION: stream={stream_id} frame={frame_index} annotations={len(annotations)}")
            except Exception as e:
                print(f"ERROR: Annotation error: {e}")
        
        # PIPELINE STEP 2: Decision Maker
        specialist_decisions: List[SpecialistDecision] = []
        if self.decision_maker and annotations:
            try:
                specialist_decisions = self.decision_maker.decide(annotations)
                print(f"DECISIONS: stream={stream_id} frame={frame_index} decisions={len(specialist_decisions)}")
            except Exception as e:
                print(f"ERROR: Decision making error: {e}")
        
        # PIPELINE STEP 3: Specialist Models
        detections: List[DetectionResult] = []
        specialist_metrics: Dict[str, Any] = {}
        
        for decision in specialist_decisions:
            specialist = self.specialists.get(decision.specialist_name)
            if specialist and specialist.is_loaded:
                try:
                    # Pass both frame and annotations to specialist
                    if isinstance(specialist, Callable):
                        specialist_detections = specialist(frame, decision.annotations)
                    else:
                        specialist_detections = specialist.infer(frame, decision.annotations)
                    detections.extend(specialist_detections)
                    specialist_metrics[decision.specialist_name] = specialist.get_metrics()
                    self.stats['specialist_invocations'] += 1
                    
                    print(f"SPECIALIST: {decision.specialist_name} detected {len(specialist_detections)} objects (reason: {decision.reason})")
                    
                except Exception as e:
                    print(f"ERROR: Specialist {decision.specialist_name} inference error: {e}")
        
        # Filter by confidence and limit count
        detections = [
            d for d in detections 
            if d.confidence >= stream_config.min_confidence
        ][:stream_config.max_detections_per_frame]
        
        self.stats['total_detections'] += len(detections)
        
        # Publish metrics
        combined_metrics = {
            **annotation_metrics,
            **specialist_metrics
        }
        self._publish_metrics(stream_id, detections, combined_metrics)
        
        # Log detections
        print(f"FINAL: stream={stream_id} frame={frame_index} annotations={len(annotations)} detections={len(detections)}")
        
        result = {
            'stream_id': stream_id,
            'frame_index': frame_index,
            'sampled': True,
            'annotations': [asdict(a) for a in annotations],
            'decisions': [asdict(d) for d in specialist_decisions],
            'detections': [asdict(d) for d in detections],
            'metrics': combined_metrics
        }
        
        # Cleanup frame data to prevent memory accumulation
        del frame
        
        return result
    
    @classmethod
    def _validate_frame(cls, frame: np.ndarray):
        """Validate frame quality and format
        
        Args:
            frame: RGB image as numpy array
            
        Returns:
            True if frame is valid, False otherwise
        """
        if frame is None or frame.size == 0:
            return False
        
        if len(frame.shape) != 3 or frame.shape[2] != cls.EXPECTED_CHANNELS:
            return False
        
        height, width = frame.shape[:2]
        if not (cls.MIN_FRAME_DIM <= height <= cls.MAX_FRAME_DIM and 
                cls.MIN_FRAME_DIM <= width <= cls.MAX_FRAME_DIM):
            return False
        
        return True
    
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
        annotation_metrics = {}
        if self.annotation_model and self.annotation_model.is_loaded:
            annotation_metrics = self.annotation_model.get_metrics()
        
        specialist_metrics = {}
        for name, specialist in self.specialists.items():
            if specialist and specialist.is_loaded:
                specialist_metrics[name] = specialist.get_metrics()
        
        # Get active streams count from Redis or in-memory
        if self.redis.enabled:
            active_stream_count = len(self.redis.get_all_stream_ids())
        else:
            active_stream_count = len(self.active_streams)
        
        return {
            'active_streams': active_stream_count,
            'redis_enabled': self.redis.enabled,
            'annotation_model_loaded': self.annotation_model.is_loaded if self.annotation_model else False,
            'specialists_loaded': list(self.specialists.keys()),
            'annotation_metrics': annotation_metrics,
            'specialist_metrics': specialist_metrics,
            **self.stats
        }