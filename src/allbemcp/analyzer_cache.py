#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class AnalysisCache:
    """Simple incremental analysis cache keyed by library fingerprint and analyzer config."""

    def __init__(self, cache_dir: str = ".allbemcp_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_file(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def make_cache_key(self, library_name: str, config_signature: str, fingerprint: str) -> str:
        raw = f"{library_name}|{config_signature}|{fingerprint}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def load(self, cache_key: str) -> Optional[Dict[str, Any]]:
        cache_file = self._cache_file(cache_key)
        if not cache_file.exists():
            return None
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def save(self, cache_key: str, result: Dict[str, Any]) -> None:
        cache_file = self._cache_file(cache_key)
        try:
            cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


class IncrementalCache:
    """Module-level incremental cache for scanned function metadata."""

    def __init__(self, cache_dir: str = ".allbemcp_cache"):
        self.cache_dir = Path(cache_dir) / "modules"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _module_key(self, module_name: str, module_file: str, config_signature: str) -> str:
        raw = f"{module_name}|{module_file}|{config_signature}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _module_fingerprint(self, module_file: str) -> Optional[str]:
        try:
            p = Path(module_file)
            if not p.exists():
                return None
            st = p.stat()
            return f"{st.st_mtime_ns}:{st.st_size}"
        except Exception:
            return None

    def get_module_cache(self, module_name: str, module_file: str, config_signature: str) -> Optional[Dict[str, Any]]:
        fingerprint = self._module_fingerprint(module_file)
        if fingerprint is None:
            return None

        cache_key = self._module_key(module_name, module_file, config_signature)
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if data.get("fingerprint") != fingerprint:
                return None
            return data
        except Exception:
            return None

    def save_module_cache(
        self,
        module_name: str,
        module_file: str,
        config_signature: str,
        functions: List[Dict[str, Any]],
        skipped: List[Dict[str, str]],
    ) -> None:
        fingerprint = self._module_fingerprint(module_file)
        if fingerprint is None:
            return

        cache_key = self._module_key(module_name, module_file, config_signature)
        cache_file = self.cache_dir / f"{cache_key}.json"
        payload = {
            "fingerprint": fingerprint,
            "functions": functions,
            "skipped": skipped,
        }
        try:
            cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
