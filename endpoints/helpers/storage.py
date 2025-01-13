import json
from datetime import datetime

from dify_plugin.core.runtime import Session


class StorageCacheProvider:
    def __init__(self, session: Session, ttl: int = 3600) -> None:
        if session is None:
            raise ValueError("session is not available")
        self.session = session
        self.ttl = ttl

    def get(self, key: str) -> bytes | None:
        storage = self.session.storage
        if storage is None:
            raise ValueError("storage is not available")

        ts = datetime.now().timestamp()
        value_loaded: bytes | None = None
        ttl_loaded: bytes | None = None

        # Try to load the value from the storage
        try:
            value_loaded = storage.get(key)
            ttl_loaded = storage.get(f"{key}/ttl")
        except Exception:
            pass

        # If the value and ttl combination is abnormal, correct it and return early.
        if value_loaded is None and ttl_loaded is not None:
            try:
                storage.delete(f"{key}/ttl")
            except Exception:
                pass
            return None
        if value_loaded is not None and ttl_loaded is None:
            try:
                storage.set(f"{key}/ttl", str(ts).encode())
            except Exception:
                pass
            return value_loaded

        # If the value and ttl combination is both None, return None.
        if value_loaded is None and ttl_loaded is None:
            return None

        # If the value and ttl combination is both not None, check if the value is expired.
        if value_loaded is not None and ttl_loaded is not None:
            ttl = int.from_bytes(ttl_loaded, "little")
            if ts - ttl > self.ttl:
                try:
                    storage.delete(key)
                    storage.delete(f"{key}/ttl")
                except Exception:
                    pass
                return None
            return value_loaded

        # default return None, should never reach here.
        return None

    def set(self, key: str, value: bytes) -> bool:
        storage = self.session.storage
        if storage is None:
            raise ValueError("storage is not available")
        ts = datetime.now().timestamp()
        try:
            storage.set(key, value)
            storage.set(f"{key}/ttl", str(ts).encode())
        except Exception:
            return False
        return True

    def delete(self, key: str) -> bool:
        storage = self.session.storage
        if storage is None:
            raise ValueError("storage is not available")
        try:
            storage.delete(key)
            storage.delete(f"{key}/ttl")
        except Exception:
            return False
        return True

    def get_as_str(self, key: str, encoding="utf-8") -> str | None:
        value = self.get(key)
        if value is None:
            return None
        return value.decode(encoding=encoding)

    def set_as_str(self, key: str, value: str, encoding="utf-8") -> bool:
        return self.set(key, value.encode(encoding=encoding))

    def get_as_int(self, key: str) -> int | None:
        value = self.get(key)
        if value is None:
            return None
        return int.from_bytes(value, "little")

    def set_as_int(self, key: str, value: int) -> bool:
        return self.set(key, value.to_bytes(4, "little"))

    def get_as_json(self, key: str) -> dict | None:
        value = self.get(key)
        if value is None:
            return None
        return json.loads(value)

    def set_as_json(self, key: str, value: dict) -> bool:
        return self.set(key, json.dumps(value).encode())
