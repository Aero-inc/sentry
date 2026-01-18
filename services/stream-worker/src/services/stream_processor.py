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
from src.models.annotation_model import AnnotationModel, Annotation
from src.services.decision_maker import DecisionMaker, SpecialistDecision

class StreamProcessor:
    """
    Main stream processor for video processing
    Pipeline: Annotation → Decision Maker → Specialist Models → Actions
    """
    
    def __init__(self, cfg: Config, s3: S3Service, cloudwatch: CloudWatchService):
        self.config = cfg
        self.s3_service = s3
        self.cloudwatch_service = cloudwatch
        
        # Pipeline components
        self.annotation_model: AnnotationModel = None
        self.decision_maker: DecisionMaker = None
        self.specialists: Dict[str, SpecialistInterface] = {}
        
        self.active_streams: Dict[str, StreamConfig] = {}
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
            if self.config.s3_artifacts_bucket:
                print(f"Downloading models from S3: {self.config.s3_artifacts_bucket}")
                os.makedirs('/models', exist_ok=True)
                
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
                'input_size': self.config.model_input_size
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
        
        return {
            'stream_id': stream_id,
            'frame_index': frame_index,
            'sampled': True,
            'annotations': [asdict(a) for a in annotations],
            'decisions': [asdict(d) for d in specialist_decisions],
            'detections': [asdict(d) for d in detections],
            'metrics': combined_metrics
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
        
        return {
            'active_streams': len(self.active_streams),
            'annotation_model_loaded': self.annotation_model.is_loaded if self.annotation_model else False,
            'specialists_loaded': list(self.specialists.keys()),
            'annotation_metrics': annotation_metrics,
            'specialist_metrics': specialist_metrics,
            **self.stats
        }
