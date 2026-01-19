"""
Specialist Interface - Abstract base class for ML inference specialists
This allows CPU and GPU implementations to be swapped without changing the stream worker logic
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List

import numpy as np
import torch

if TYPE_CHECKING:
    from src.models.annotation_model import Annotation


@dataclass
class DetectionResult:
    """Result from a specialist model"""
    class_name: str
    confidence: float
    bounding_box: List[float]  # [x1, y1, x2, y2]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SpecialistInterface(ABC):
    """
    Abstract interface for specialist models
    Allows swapping between CPU and GPU implementations
    """
    
    def __init__(self, model_name: str, config: Dict[str, Any]) -> None:
        self.model_name = model_name
        self.config = config
        self.is_loaded = False
        self.device = self._determine_device()
    
    def _determine_device(self) -> torch.device:
        """Determine the appropriate device for this specialist"""
        # Override in subclasses to specify device preference
        return torch.device('cpu')
    
    @abstractmethod
    def load_model(self) -> None:
        """Load the model into memory"""
        pass
    
    @abstractmethod
    def unload_model(self) -> None:
        """Unload the model from memory"""
        pass
    
    @abstractmethod
    def infer(self, frame: np.ndarray, annotations: List['Annotation']) -> List[DetectionResult]:
        """
        Run inference on a frame with annotation context
        
        Args:
            frame: RGB image as numpy array (H, W, 3)
            annotations: List of annotations from annotation model
            
        Returns:
            List of detection results
        """
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """
        Get performance metrics
        
        Returns:
            Dictionary with metrics like inference_time_ms, memory_usage_mb, etc.
        """
        pass
    
    def preprocess(self, frame: np.ndarray) -> torch.Tensor:
        """
        Common preprocessing step (can be overridden)
        Default implementation converts numpy array to torch tensor
        
        Args:
            frame: RGB image as numpy array (H, W, 3)
            
        Returns:
            Preprocessed tensor ready for model input
        """
        tensor = torch.from_numpy(frame).float()
        return tensor.to(self.device)
    
    def __enter__(self) -> 'SpecialistInterface':
        """Context manager support"""
        if not self.is_loaded:
            self.load_model()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Context manager cleanup"""
        if self.is_loaded:
            self.unload_model()
        return False
