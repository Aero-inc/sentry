"""
CPU Specialist Implementation
Uses CPU-based inference for object detection with PyTorch
"""
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Callable, Optional
import time
import math

import cv2
import numpy as np
import torch

from src.core.errors import ModelNotLoadedError, InferenceError
from src.models.specialist_interface import SpecialistInterface, DetectionResult

TYPE_CHECKING = True
if TYPE_CHECKING:
    from src.models.annotation_model import Annotation


def specialist_substitute(frame: np.ndarray, annotations: List[Annotation], threshold: float = 0.05) -> bool:
    """A substitute function for the specialist models.

    Args:
        frame (np.ndarray): ndarray of the frame being processed.
        annotations (List[Annotation]): List of annotations from annotation model.
        threshold (float, optional): Threshold for distance between human and gun. Defaults to 0.05.

    Returns:
        bool: True if a dangerous pair is found, False otherwise.
    """
    humans = []
    guns = []

    for annotation in annotations:
        if annotation.object_type == 'person':
            humans.append((annotation.bounding_box[0], annotation.bounding_box[1]))
        elif annotation.object_type == 'gun':
            guns.append((annotation.bounding_box[0], annotation.bounding_box[1]))

    if not humans or not guns:
        return False

    # Early exit: the moment we find a dangerous pair
    for hx, hy in humans:
        for gx, gy in guns:
            if math.hypot(hx - gx, hy - gy) < threshold:
                return True

    return False


class CPUSpecialist(SpecialistInterface):
    """
    CPU-based ML specialist implementation using PyTorch
    """
    
    DEFAULT_INPUT_SIZE = (640, 640)
    DEFAULT_CONFIDENCE_THRESHOLD = 0.5
    DEFAULT_NUM_THREADS = 4
    MAX_METRICS_HISTORY = 100
    MIN_DETECTION_SIZE = 6  # Minimum number of values in detection array
    
    def __init__(self, model_name: str, config: Dict[str, Any]) -> None:
        super().__init__(model_name, config)
        self.model: Optional[torch.nn.Module, Callable] = None
        self.inference_times: List[float] = []
        self._max_metrics_history = self.MAX_METRICS_HISTORY
        self._input_size = config.get('input_size', self.DEFAULT_INPUT_SIZE)
        self._confidence_threshold = config.get('confidence_threshold', self.DEFAULT_CONFIDENCE_THRESHOLD)
        self._num_threads = config.get('num_threads', self.DEFAULT_NUM_THREADS)
        
    def load_model(self) -> None:
        """Load model for CPU inference using PyTorch or ONNX Runtime"""
        
        # TODO: Remove this when CPU specialist is implemented
        if not self.config.specialists:
            self.is_loaded = True
            print("CPU Specialist: Using specialist substitute")
            self.model = specialist_substitute
            return

        model_path = Path(self.config.get('model_path', ''))
        if not model_path or not model_path.exists():
            raise ValueError(f"Invalid model path: {model_path}")
        
        try:
            print(f"Loading CPU model: {self.model_name} from {model_path}")
            
            # Load based on file extension
            if model_path.suffix in ['.onnx']:
                self._load_onnx_model(model_path)
            else:
                # PyTorch format (.pt, .pth)
                self.model = torch.load(str(model_path), map_location=self.device)
                self.model.eval()  # Set to evaluation mode
            
            # Optimize for CPU inference
            if hasattr(torch, 'set_num_threads'):
                torch.set_num_threads(self._num_threads)
            
            self.is_loaded = True
            print(f"CPU model loaded successfully: {self.model_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}") from e
    
    def _load_onnx_model(self, model_path: Path) -> None:
        """Load ONNX model using ONNX Runtime"""
        import onnxruntime as ort
        
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        self.model = ort.InferenceSession(
            str(model_path),
            sess_options=session_options,
            providers=['CPUExecutionProvider']
        )
    
    def unload_model(self) -> None:
        """Unload model from memory"""
        if self.model is not None:
            del self.model
            self.model = None
        
        self.is_loaded = False
        self.inference_times.clear()
        print(f"CPU model unloaded: {self.model_name}")
    
    @torch.no_grad()
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
            # Preprocess to tensor
            input_tensor = self.preprocess(frame)
            
            # Run inference
            detections = self._run_inference(input_tensor)
            
            # Enrich detections with annotation context
            detections = self._enrich_with_annotations(detections, annotations)
            
            # Track inference time
            inference_time_ms = (time.perf_counter() - start_time) * 1000
            self._record_inference_time(inference_time_ms)
            
            return detections
            
        except Exception as e:
            raise InferenceError(f"Inference failed: {e}") from e
    
    def _run_inference(self, input_tensor: torch.Tensor) -> List[DetectionResult]:
        """Run model inference"""
        # Check if ONNX Runtime session
        if hasattr(self.model, 'run'):
            # ONNX Runtime
            input_name = self.model.get_inputs()[0].name
            outputs = self.model.run(None, {input_name: input_tensor.cpu().numpy()})
            return self._parse_detections(outputs[0])
        else:
            # PyTorch model
            outputs = self.model(input_tensor).cpu().numpy()
            return self._parse_detections(outputs)
    
    def _parse_detections(self, outputs: np.ndarray) -> List[DetectionResult]:
        """Parse model outputs into DetectionResult objects"""
        detections = []
        
        # Handle different output shapes
        if outputs.ndim > 2:
            outputs = outputs.squeeze()
        
        # Handle empty outputs
        if outputs.size == 0:
            return detections
        
        # Ensure outputs is 2D
        if outputs.ndim == 1:
            outputs = outputs.reshape(1, -1)
        
        # Parse detections
        for detection in outputs:
            if len(detection) >= self.MIN_DETECTION_SIZE:
                confidence = float(detection[4])
                if confidence >= self._confidence_threshold:
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
    
    def preprocess(self, frame: np.ndarray) -> torch.Tensor:
        """Preprocess frame to tensor for model input"""
        # Resize
        resized = cv2.resize(frame, self._input_size)
        
        # Convert to tensor and normalize [0, 1]
        tensor = torch.from_numpy(resized).float() / 255.0
        
        # Transpose to NCHW format: (H, W, C) -> (C, H, W) and add batch
        tensor = tensor.permute(2, 0, 1).unsqueeze(0)
        
        # Move to device (CPU in this case)
        return tensor.to(self.device)
    
    def _record_inference_time(self, time_ms: float) -> None:
        """Record inference time for metrics"""
        self.inference_times.append(time_ms)
        if len(self.inference_times) > self._max_metrics_history:
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
