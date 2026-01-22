"""
Redis service for distributed state management
"""
import json
from typing import Any, Dict, Optional

import redis


class RedisService:
    """Redis client for managing stream state across containers"""
    
    STREAM_PREFIX = "stream:"
    STREAM_TTL = 86400  # 24 hours
    
    def __init__(self, host: Optional[str], port: int = 6379, db: int = 0):
        """Initialize Redis connection
        
        Args:
            host: Redis host address
            port: Redis port
            db: Redis database number
        """
        self.host = host
        self.port = port
        self.db = db
        self.client: Optional[redis.Redis] = None
        self._enabled = False
        
        if host:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    max_connections=50,  # Connection pool size
                    socket_keepalive=True,  # Keep connections alive
                    health_check_interval=30  # Check connection health
                )
                # Test connection
                self.client.ping()
                self._enabled = True
                print(f"Redis connected: {host}:{port}/{db}")
            except Exception as e:
                print(f"WARNING: Redis connection failed: {e}")
                print("Running in in-memory mode (not recommended for production)")
                self.client = None
        else:
            print("Redis not configured - using in-memory storage")
    
    @property
    def enabled(self) -> bool:
        """Check if Redis is available"""
        return self._enabled
    
    def _get_key(self, stream_id: str) -> str:
        """Get Redis key for stream"""
        return f"{self.STREAM_PREFIX}{stream_id}"
    
    def set_stream(self, stream_id: str, config: Dict[str, Any]) -> bool:
        """Store stream configuration
        
        Args:
            stream_id: Stream identifier
            config: Stream configuration dictionary
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            key = self._get_key(stream_id)
            value = json.dumps(config)
            self.client.setex(key, self.STREAM_TTL, value)
            return True
        except Exception as e:
            print(f"ERROR: Failed to set stream in Redis: {e}")
            return False
    
    def get_stream(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stream configuration
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            Stream configuration or None if not found
        """
        if not self.client:
            return None
        
        try:
            key = self._get_key(stream_id)
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"ERROR: Failed to get stream from Redis: {e}")
            return None
    
    def delete_stream(self, stream_id: str) -> bool:
        """Delete stream configuration
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            True if successful
        """
        if not self.client:
            return False
        
        try:
            key = self._get_key(stream_id)
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"ERROR: Failed to delete stream from Redis: {e}")
            return False
    
    def stream_exists(self, stream_id: str) -> bool:
        """Check if stream exists
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            True if stream exists
        """
        if not self.client:
            return False
        
        try:
            key = self._get_key(stream_id)
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"ERROR: Failed to check stream existence: {e}")
            return False
    
    def get_all_stream_ids(self) -> list[str]:
        """Get all active stream IDs
        
        Returns:
            List of stream IDs
        """
        if not self.client:
            return []
        
        try:
            pattern = f"{self.STREAM_PREFIX}*"
            keys = self.client.keys(pattern)
            return [key.replace(self.STREAM_PREFIX, '') for key in keys]
        except Exception as e:
            print(f"ERROR: Failed to get stream IDs: {e}")
            return []
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                self.client.close()
                print("Redis connection closed")
            except Exception as e:
                print(f"ERROR: Failed to close Redis connection: {e}")
