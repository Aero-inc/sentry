"""
Custom exceptions for stream worker
"""


class StreamWorkerError(Exception):
    """Base exception for stream worker errors"""
    pass


class ModelNotLoadedError(StreamWorkerError):
    """Raised when attempting to use a model that hasn't been loaded"""
    pass


class InvalidFrameError(StreamWorkerError):
    """Raised when frame validation fails"""
    pass


class StreamNotFoundError(StreamWorkerError):
    """Raised when stream ID is not found"""
    pass


class InferenceError(StreamWorkerError):
    """Raised when inference fails"""
    pass
