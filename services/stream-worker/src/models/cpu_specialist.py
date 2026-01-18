"""
CPU Specialist Implementation
Uses CPU-based inference for object detection
"""
import time
import numpy as np
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import cv2

from src.models.specialist_interface import SpecialistInterface, DetectionResult
from src.core.errors import ModelNotLoadedError, InferenceError

if TYPE_CHECKING:
    from src.models.annotation_model import Annotation


class CPUSpecialist(SpecialistInterface):
    """
    CPU-based ML specialist implementation using ONNX Runtime
    """
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        super().__init__(model_name, config)
        self.model: Optional[Any] = None
        self.inference_times: List[float] = []
        self.max_metrics_history = 100
        
    def load_model(self) -> None:
        """Load model for CPU inference"""
        print(f"Loading CPU model: {self.model_name} from {self.config.get('model_path')}")
        
        model_path = self.config.get('model_path')
        if not model_path:
            raise ValueError("model_path is required in config")
        
        try:
            self.model = self._load_onnx(model_path)
            self.is_loaded = True
            print(f"CPU model loaded successfully: {self.model_name}")
        except Exception as e:
            print(f"ERROR: Failed to load model: {e}")
            raise
    
    def _load_onnx(self, model_path: str) -> Any:
        """Load ONNX model with CPU execution provider"""
        import onnxruntime as ort
        
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        return ort.InferenceSession(
            model_path,
            sess_options=session_options,
            providers=['CPUExecutionProvider']
        )
    
    def unload_model(self) -> None:
        """Unload model from memory"""
        self.model = None
        self.is_loaded = False
        self.inference_times.clear()
        print(f"CPU model unloaded: {self.model_name}")
    
    def infer(self, frame: np.ndarray, annotations: List['Annotation']) -> List[DetectionResult]:
        """
        Run CPU inference on frame with annotation context
        
        Args:
            frame: RGB image as numpy array (H, W, 3)
            annotations: List of annotations from annotation model
            
        Returns:
            List of detection results
            
        Raises:
            ModelNotLoadedError: If model hasn't been loaded
            InferenceError: If inference fails
        """
        if not self.is_loaded or self.model is None:
            raise ModelNotLoadedError(f"Model {self.model_name} not loaded")
        
        start_time = time.perf_counter()
        
        try:
            # Preprocess (annotations can be used for ROI cropping in future)
            processed = self.preprocess(frame)
            
            # Run ONNX inference
            detections = self._infer_onnx(processed)
            
            # Enrich detections with annotation context
            detections = self._enrich_with_annotations(detections, annotations)
            
            # Track inference time
            inference_time_ms = (time.perf_counter() - start_time) * 1000
            self._record_inference_time(inference_time_ms)
            
            return detections
            
        except Exception as e:
            print(f"ERROR: Inference failed: {e}")
            raise InferenceError(f"Inference failed: {e}") from e
    
    def _infer_onnx(self, frame: np.ndarray) -> List[DetectionResult]:
        """Run ONNX Runtime inference"""
        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: frame})
        return self._parse_detections(outputs[0])
    
    def _parse_detections(self, outputs: np.ndarray) -> List[DetectionResult]:
        """Parse model outputs into DetectionResult objects"""
        detections = []
        confidence_threshold = self.config.get('confidence_threshold', 0.5)
        
        # Adapt this to your model's output format
        for detection in outputs:
            if len(detection) >= 6:
                confidence = float(detection[4])
                if confidence >= confidence_threshold:
                    detections.append(DetectionResult(
                        class_name=f"class_{int(detection[5])}",
                        confidence=confidence,
                        bounding_box=[
                            float(detection[0]),
                            float(detection[1]),
                            float(detection[2]),
                            float(detection[3])
                        ],
                        metadata={}
                    ))
        
        return detections
    
    def _enrich_with_annotations(
        self, 
        detections: List[DetectionResult], 
        annotations: List['Annotation']
    ) -> List[DetectionResult]:
        """Enrich detections with annotation context"""
        for detection in detections:
            # Find overlapping annotations
            overlapping_annotations = []
            for annotation in annotations:
                if self._boxes_overlap(detection.bounding_box, annotation.bounding_box):
                    overlapping_annotations.append(annotation.object_type)
            
            if overlapping_annotations:
                detection.metadata['annotation_context'] = overlapping_annotations
        
        return detections
    
    @staticmethod
    def _boxes_overlap(box1: List[float], box2: List[float]) -> bool:
        """Check if two bounding boxes overlap"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        return not (x1_max < x2_min or x2_max < x1_min or 
                    y1_max < y2_min or y2_max < y1_min)
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for model input"""
        input_size = self.config.get('input_size', (640, 640))
        
        # Resize
        resized = cv2.resize(frame, input_size)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Transpose to NCHW format and add batch dimension
        preprocessed = np.transpose(normalized, (2, 0, 1))
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def _record_inference_time(self, time_ms: float) -> None:
        """Record inference time for metrics"""
        self.inference_times.append(time_ms)
        if len(self.inference_times) > self.max_metrics_history:
            self.inference_times.pop(0)
    
    def get_metrics(self) -> Dict[str, float]:
        """Get performance metrics"""
        if not self.inference_times:
            return {
                'inference_time_ms': 0.0,
                'inference_count': 0,
                'model_name': self.model_name
            }
        
        avg_time = sum(self.inference_times) / len(self.inference_times)
        
        return {
            'inference_time_ms': self.inference_times[-1],
            'inference_avg_ms': avg_time,
            'inference_count': len(self.inference_times),
            'model_name': self.model_name
        }
