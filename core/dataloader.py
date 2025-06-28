
from typing import Callable, Any, List, Dict, Optional
from core.lock.lock import Lock
from core.logger import Logger

class DataLoader:
    def __init__(
        self,
        batch_load_fn: Callable[[List[Any]], List[Any]],
        backend: Any,
        get_named_lock: Callable[[str], Lock],
        lock_name: Optional[str] = None,
        logger: Optional[Logger] = None,
    ):
        self.logger = logger or Logger()
        self._batch_load_fn = self._validate_batch_load_fn(batch_load_fn)
        self._backend = backend
        self._get_named_lock = get_named_lock
        self._lock = self._get_named_lock(lock_name or f"dataloader:{id(self)}")

    def load_many(self, keys: List[Any]) -> List[Any]:
        self.logger.debug("load_many called", keys=keys)
        with self._lock:
            # Check cache for keys
            cached = {}
            missing = []
            missing_indices = []
            for idx, key in enumerate(keys):
                value = self._backend.get(key)
                self.logger.debug("backend.get", key=key, value=value)
                if value is not None:
                    cached[key] = value
                else:
                    missing.append(key)
                    missing_indices.append(idx)

            self.logger.debug("Cached and missing keys", cached=cached, missing=missing)

            # Deduplicate missing keys, preserving order
            seen = set()
            unique_missing = []
            for key in missing:
                if key not in seen:
                    seen.add(key)
                    unique_missing.append(key)
            self.logger.debug("Unique missing keys", unique_missing=unique_missing)

            # Batch load unique missing keys
            results = {}
            if unique_missing:
                loaded = self._batch_load_fn(unique_missing)
                self.logger.debug("batch_load_fn result", unique_missing=unique_missing, loaded=loaded)
                for key, value in zip(unique_missing, loaded):
                    self._backend.set(key, value)
                    results[key] = value
            self.logger.debug("Results after batch load", results=results)

            # Merge cached and loaded results in order, preserving duplicates
            output = []
            for key in keys:
                if key in cached:
                    output.append(cached[key])
                else:
                    output.append(results.get(key))
            self.logger.debug("Final output", output=output)
            return output

    @staticmethod
    def _validate_batch_load_fn(fn: Callable) -> Callable:
        import inspect
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())
        if len(params) != 1:
            raise TypeError("batch_load_fn must accept exactly one argument (a list of keys)")
        def wrapper(keys):
            if not isinstance(keys, list):
                raise TypeError("Argument to batch_load_fn must be a list")
            primitive_types = (str, int, float, bool)
            if not all(isinstance(k, primitive_types) for k in keys):
                raise TypeError("All keys passed to batch_load_fn must be primitive types (str, int, float, bool)")
            if keys:
                first_type = type(keys[0])
                if not all(type(k) == first_type for k in keys):
                    raise TypeError("All keys passed to batch_load_fn must be of the same type")
            return fn(keys)
        return wrapper
