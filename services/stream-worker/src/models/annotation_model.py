"""
Annotation Model
Performs initial object detection to identify regions of interest
Uses ONNX Runtime for efficient CPU inference without PyTorch overhead
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

import cv2
import numpy as np

try:
    import onnxruntime as ort
    HAS_ONNXRUNTIME = True
except ImportError:
    HAS_ONNXRUNTIME = False


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
    
    DEFAULT_INPUT_SIZE = (640, 640)
    DEFAULT_CONFIDENCE_THRESHOLD = 0.3
    MIN_DETECTION_SIZE = 6  # Minimum number of values in detection array
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model: Optional[Any] = None  # ONNX InferenceSession
        self.is_loaded = False
        self.annotation_times: List[float] = []
        self._input_size = config.get('annotation_input_size', self.DEFAULT_INPUT_SIZE)
        self._confidence_threshold = config.get('annotation_confidence_threshold', self.DEFAULT_CONFIDENCE_THRESHOLD)
        
    def load_model(self):
        """Load annotation model using ONNX Runtime"""
        model_path = Path(self.config.get('annotation_model_path', ''))
        if not model_path or not model_path.exists():
            raise ValueError(f"Invalid model path: {model_path}")
        
        if model_path.suffix != '.onnx':
            raise ValueError(f"Only ONNX models supported for annotation. Got: {model_path.suffix}")
        
        try:
            print(f"Loading ONNX annotation model from {model_path}")
            self._load_onnx_model(model_path)
            self.is_loaded = True
            print(f"ONNX annotation model loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load annotation model: {e}") from e
    
    def _load_onnx_model(self, model_path: Path):
        """Load ONNX model using ONNX Runtime"""
        if not HAS_ONNXRUNTIME:
            raise RuntimeError("onnxruntime is not installed. Install it to load ONNX models.")
        
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        # Enable parallel execution for faster inference
        session_options.intra_op_num_threads = 2
        session_options.inter_op_num_threads = 2
        
        # Use CPU execution provider for memory efficiency
        self.model = ort.InferenceSession(
            str(model_path),
            sess_options=session_options,
            providers=['CPUExecutionProvider']
        )
        print("ONNX model loaded with CPUExecutionProvider")
        
        # Warm up the model with a dummy inference to avoid first-request latency
        self._warmup_model()
    
    def unload_model(self):
        """Unload annotation model from memory"""
        if self.model is not None:
            del self.model
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
            # Preprocess frame to numpy array (ONNX input)
            input_array = self._preprocess(frame)
            
            # Run ONNX inference
            outputs = self._run_inference(input_array)
            
            # Parse annotations
            annotations = self._parse_annotations(outputs)
            
            # Track time
            annotation_time_ms = (time.perf_counter() - start_time) * 1000
            self.annotation_times.append(annotation_time_ms)
            
            return annotations
            
        except Exception as e:
            raise RuntimeError(f"Annotation failed: {e}") from e
        finally:
            # Explicit cleanup (input_array is numpy, will be GC'd)
            pass
    
    def _warmup_model(self) -> None:
        """Warm up model with dummy inference to avoid first-request latency"""
        try:
            dummy_frame = np.zeros((*self._input_size, 3), dtype=np.uint8)
            dummy_input = self._preprocess(dummy_frame)
            self.model.run(None, {self.model.get_inputs()[0].name: dummy_input})
            print("Model warmed up successfully")
        except Exception as e:
            print(f"WARNING: Model warmup failed: {e}")
    
    def _run_inference(self, input_array: np.ndarray):
        """Run ONNX model inference"""
        input_name = self.model.get_inputs()[0].name
        outputs = self.model.run(None, {input_name: input_array})
        return outputs[0]
    
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame to numpy array for ONNX inference"""
        # Resize to model input size
        resized = cv2.resize(frame, self._input_size)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # Convert to NCHW format: (H, W, C) -> (C, H, W) and add batch dimension
        # Transpose: (H, W, C) -> (C, H, W)
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # Add batch dimension: (C, H, W) -> (1, C, H, W)
        batched = np.expand_dims(transposed, axis=0)
        
        return batched
    
    def _parse_annotations(self, outputs: np.ndarray):
        """Parse model outputs into Annotation objects"""
        annotations = []
        
        # Handle different output shapes
        if outputs.ndim > 2:
            outputs = outputs.squeeze()
        
        # Handle empty outputs
        if outputs.size == 0:
            return annotations
        
        # Ensure outputs is 2D
        if outputs.ndim == 1:
            outputs = outputs.reshape(1, -1)
        
        for idx, detection in enumerate(outputs):
            if len(detection) >= self.MIN_DETECTION_SIZE:
                confidence = float(detection[4])
                if confidence >= self._confidence_threshold:
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
    
    def get_metrics(self):
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
