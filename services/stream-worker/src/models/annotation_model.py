"""
Annotation Model
Performs initial object detection to identify regions of interest
"""
import time
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class Annotation:
    """Annotation result from the annotation model"""
    object_type: str
    confidence: float
    bounding_box: List[float]  # [x1, y1, x2, y2]
    region_id: str


class AnnotationModel:
    """
    Lightweight annotation model for initial frame analysis
    Identifies regions and objects for downstream specialist processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model: Optional[Any] = None
        self.is_loaded = False
        self.annotation_times: List[float] = []
        
    def load_model(self) -> None:
        """Load annotation model"""
        print("Loading annotation model")
        
        model_path = self.config.get('annotation_model_path')
        if not model_path:
            raise ValueError("annotation_model_path is required in config")
        
        try:
            import onnxruntime as ort
            
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            self.model = ort.InferenceSession(
                model_path,
                sess_options=session_options,
                providers=['CPUExecutionProvider']
            )
            
            self.is_loaded = True
            print("Annotation model loaded successfully")
        except Exception as e:
            print(f"ERROR: Failed to load annotation model: {e}")
            raise
    
    def unload_model(self) -> None:
        """Unload annotation model from memory"""
        self.model = None
        self.is_loaded = False
        self.annotation_times.clear()
        print("Annotation model unloaded")
    
    def annotate(self, frame: np.ndarray) -> List[Annotation]:
        """
        Annotate frame to identify regions and objects
        
        Args:
            frame: RGB image as numpy array (H, W, 3)
            
        Returns:
            List of annotations
        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Annotation model not loaded")
        
        start_time = time.perf_counter()
        
        try:
            # Preprocess frame
            processed = self._preprocess(frame)
            
            # Run inference
            input_name = self.model.get_inputs()[0].name
            outputs = self.model.run(None, {input_name: processed})
            
            # Parse annotations
            annotations = self._parse_annotations(outputs[0])
            
            # Track time
            annotation_time_ms = (time.perf_counter() - start_time) * 1000
            self.annotation_times.append(annotation_time_ms)
            
            return annotations
            
        except Exception as e:
            print(f"ERROR: Annotation failed: {e}")
            raise
    
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for annotation model"""
        import cv2
        
        input_size = self.config.get('annotation_input_size', (640, 640))
        
        # Resize
        resized = cv2.resize(frame, input_size)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Transpose to NCHW format and add batch dimension
        preprocessed = np.transpose(normalized, (2, 0, 1))
        preprocessed = np.expand_dims(preprocessed, axis=0)
        
        return preprocessed
    
    def _parse_annotations(self, outputs: np.ndarray) -> List[Annotation]:
        """Parse model outputs into Annotation objects"""
        annotations = []
        confidence_threshold = self.config.get('annotation_confidence_threshold', 0.3)
        
        for idx, detection in enumerate(outputs):
            if len(detection) >= 6:
                confidence = float(detection[4])
                if confidence >= confidence_threshold:
                    object_class = int(detection[5])
                    annotations.append(Annotation(
                        object_type=f"object_{object_class}",
                        confidence=confidence,
                        bounding_box=[
                            float(detection[0]),
                            float(detection[1]),
                            float(detection[2]),
                            float(detection[3])
                        ],
                        region_id=f"region_{idx}"
                    ))
        
        return annotations
    
    def get_metrics(self) -> Dict[str, float]:
        """Get annotation metrics"""
        if not self.annotation_times:
            return {
                'annotation_time_ms': 0.0,
                'annotation_count': 0
            }
        
        avg_time = sum(self.annotation_times) / len(self.annotation_times)
        
        return {
            'annotation_time_ms': self.annotation_times[-1],
            'annotation_avg_ms': avg_time,
            'annotation_count': len(self.annotation_times)
        }
