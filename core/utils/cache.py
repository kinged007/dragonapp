import time
from typing import Callable, Any, Dict, Union
from pydantic import BaseModel
from functools import wraps
from sys import getsizeof
from pympler import asizeof

class CacheItem(BaseModel):
    value: Any
    expiry: float

class SimpleCache:
    # _instance = None

    # def __new__(cls, *args, **kwargs):
    #     if not cls._instance:
    #         cls._instance = super(SimpleCache, cls).__new__(cls, *args, **kwargs)
    #     return cls._instance

    def __init__(self):
        self.storage: Dict[str, CacheItem] = {}

    def set(self, key: str, value: Any, ttl: int = 300, namespace: str = 'default'):
        expiry = time.time() + ttl
        namespaced_key = f"{namespace}:{key}"
        self.storage[namespaced_key] = CacheItem(value=value, expiry=expiry)

    def get(self, key: str, namespace: str = 'default'):
        namespaced_key = f"{namespace}:{key}"
        item = self.storage.get(namespaced_key)
        print("Total Cache Size: (pympler) {:.5f} MB".format(asizeof.asizeof(self.storage)/ 1024 / 1024))        
        if item and time.time() < item.expiry:
            return item.value
        else:
            self.storage.pop(namespaced_key, None)
            return None

    def clear(self, key: str = None, namespace: str = 'default'):
        # from rich import print
        # print(self.storage)
        if key is None:
            # Clear the entire namespace
            self.storage = {k: v for k, v in self.storage.items() if not k.startswith(f"{namespace}:")}
        else:
            # Clear a specific key in the namespace
            namespaced_key = f"{namespace}:{key}"
            self.storage.pop(namespaced_key, None)
            
    def cache(self, ttl: int, key: Union[Callable[[Any], str], str] = None, namespace: str = 'default'):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if callable(key):
                    cache_key = key(*args, **kwargs)
                else:
                    cache_key = key or str((func, args, frozenset(kwargs.items())))
                result = self.get(cache_key, namespace=namespace)
                if result is None:
                    result = func(*args, **kwargs)
                    self.set(cache_key, result, ttl, namespace=namespace)
                return result
            return wrapper
        return decorator

    def async_cache(self, ttl: int, key: Union[Callable[[Any], str], str] = None, namespace: str = 'default'):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if callable(key):
                    cache_key = key(*args, **kwargs)
                else:
                    cache_key = key or str((func, args, frozenset(kwargs.items())))
                result = self.get(cache_key, namespace=namespace)
                if result is None:
                    result = await func(*args, **kwargs)
                    self.set(cache_key, result, ttl, namespace=namespace)
                return result
            return wrapper
        return decorator
    

global_cache = SimpleCache()