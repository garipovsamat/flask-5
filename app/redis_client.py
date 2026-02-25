# app/redis_client.py
import redis
import json
from typing import Optional, Any, Union
from functools import wraps

class RedisCache:
    def __init__(self, host='redis', port=6379, db=0, decode_responses=True):
        self.client = None
        self.available = False
        self.host = host
        self.port = port
        self.db = db
        self.decode_responses = decode_responses
        self._connect()
    
    def _connect(self):
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=self.decode_responses,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30
            )
            self.client.ping()
            self.available = True
            print("Redis connected successfully")
        except Exception as e:
            print(f"Redis connection failed: {e}")
            self.available = False
            self.client = None
    
    def _get_key(self, endpoint: str, item_id: Optional[int] = None) -> str:
        if item_id is not None:
            return f"{endpoint}:{item_id}"
        return endpoint
    
    def get(self, endpoint: str, item_id: Optional[int] = None) -> Optional[Any]:
        if not self.available:
            return None
        
        key = self._get_key(endpoint, item_id)
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis get error: {e}")
        return None
    
    def set(self, endpoint: str, data: Any, timeout: int = 300, item_id: Optional[int] = None) -> bool:
        if not self.available:
            return False
        
        key = self._get_key(endpoint, item_id)
        try:
            self.client.setex(key, timeout, json.dumps(data))
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, endpoint: str, item_id: Optional[int] = None) -> bool:
        if not self.available:
            return False
        
        key = self._get_key(endpoint, item_id)
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> bool:
        if not self.available:
            return False
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis clear pattern error: {e}")
            return False
    
    def get_or_set(self, endpoint: str, func, timeout: int = 300, item_id: Optional[int] = None):

        cached_data = self.get(endpoint, item_id)
        if cached_data is not None:
            return cached_data
        
        data = func()
        
        if data is not None:
            self.set(endpoint, data, timeout, item_id)
        
        return data
    
    def invalidate(self, endpoint: str, item_id: Optional[int] = None):
        self.delete(endpoint)  
        if item_id:
            self.delete(endpoint, item_id)  

cache = RedisCache()