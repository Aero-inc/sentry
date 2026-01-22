"""
API routes for stream worker
"""
from typing import Any, Dict, Optional, Tuple
import base64

import cv2
import numpy as np
from flask import Blueprint, jsonify, request

from src.core.config import StreamConfig
from src.core.errors import InvalidFrameError, InferenceError, StreamNotFoundError
from src.services.stream_processor import StreamProcessor


api_bp = Blueprint('api', __name__)

# Global processor instance (injected by app factory)
stream_processor: Optional[StreamProcessor] = None


def init_routes(processor: StreamProcessor):
    """Initialize routes with stream processor
    
    Args:
        processor: StreamProcessor instance to handle requests
    """
    global stream_processor
    stream_processor = processor


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - lightweight, no model dependency"""
    return jsonify({
        'status': 'healthy',
        'service': 'stream-worker'
    }), 200


@api_bp.route('/status', methods=['GET'])
def status_check():
    """Detailed status endpoint with model info"""
    stats = stream_processor.get_stats() if stream_processor else {}
    redis_enabled = stats.get('redis_enabled', False)
    
    return jsonify({
        'status': 'ok',
        'service': 'stream-worker',
        'annotation_model_loaded': stats.get('annotation_model_loaded', False),
        'specialists_loaded': stats.get('specialists_loaded', []),
        'active_streams': stats.get('active_streams', 0),
        'redis_enabled': redis_enabled,
        'storage_backend': 'redis' if redis_enabled else 'in-memory-dict',
        'production_ready': redis_enabled
    }), 200


@api_bp.route('/streams', methods=['POST'])
def create_stream():
    """Start a new stream"""
    try:
        data = request.get_json()
        
        if not data or 'stream_id' not in data:
            return jsonify({'error': 'stream_id is required'}), 400
        
        # Create stream config
        stream_config = StreamConfig(
            stream_id=data['stream_id'],
            frame_sample_rate=data.get('frame_sample_rate', 5),
            min_confidence=data.get('min_confidence', 0.5),
            max_detections_per_frame=data.get('max_detections_per_frame', 100),
            enable_clip_recording=data.get('enable_clip_recording', False)
        )
        
        result = stream_processor.start_stream(stream_config)
        
        print(f"Stream created: {stream_config.stream_id}")
        return jsonify(result), 201
        
    except Exception as e:
        print(f"ERROR: Failed to create stream: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/streams/<stream_id>', methods=['DELETE'])
def delete_stream(stream_id: str):
    """Stop a stream"""
    try:
        result = stream_processor.stop_stream(stream_id)
        print(f"Stream stopped: {stream_id}")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"ERROR: Failed to stop stream: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/streams/<stream_id>/frames', methods=['POST'])
def process_frame(stream_id: str):
    """Process a frame from a stream"""
    try:
        data = request.get_json()
        
        if not data or 'frame' not in data:
            return jsonify({'error': 'frame is required'}), 400
        
        # Decode base64 frame
        frame_b64 = data['frame']
        frame_index = data.get('frame_index', 0)
        
        # Decode image
        img_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Process frame
        result = stream_processor.process_frame(stream_id, frame_rgb, frame_index)
        
        return jsonify(result), 200
        
    except StreamNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except InvalidFrameError as e:
        return jsonify({'error': str(e)}), 400
    except InferenceError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"ERROR: Frame processing failed: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get processing statistics"""
    try:
        stats = stream_processor.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        print(f"ERROR: Failed to get stats: {e}")
        return jsonify({'error': str(e)}), 500
