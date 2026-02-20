#!/usr/bin/env python3
"""
Python Library to Production-Grade OpenAPI Service Converter - Universal Intelligent Version
Supports quality scoring, intelligent filtering, and deduplication, without hardcoding for specific libraries.
"""

import ast
import inspect
import importlib
import pkgutil
import re
import json
import sys
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Tuple, get_type_hints, get_origin, get_args, Sequence, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor
try:
    import docstring_parser
except ImportError:
    docstring_parser = None
from types import ModuleType
from dataclasses import dataclass, asdict, is_dataclass, fields
from collections import defaultdict


@dataclass
class FunctionInfo:
    """Function Information"""
    name: str
    module: str
    class_name: Optional[str]  # Added: Explicitly record class name
    qualname: str
    signature: str
    doc: Optional[str]
    parameters: List[Dict]
    return_type: Optional[str]
    is_async: bool
    http_method: str
    path: str
    returns_object: bool = False  # Whether it returns a complex object (needs state management)
    object_methods: List[Dict] = None  # If returns object, list of available methods
    # Added: Record raw annotation info for quality assessment
    raw_param_annotations: List[Any] = None  # Raw parameter annotations
    raw_return_annotation: Any = None  # Raw return annotation
    target_name: Optional[str] = None  # Actual callable name in source module/class
    is_constructor: bool = False  # Whether this function is a class-constructor factory tool


class QualityMetrics:
    """Function Quality Assessment Metrics - Universal Assessment Mechanism"""

    _INTERNAL_PATTERN = re.compile(
        r'(^|\.)(_?tests?|testing|testdata|benchmarks?|examples?|demos?|experimental|internal|_internal|private|_private|compat|legacy|deprecated|cache)(\.|$)',
        re.IGNORECASE,
    )
    
    @staticmethod
    def has_good_documentation(func_info: FunctionInfo) -> Tuple[bool, float]:
        """Documentation Quality Assessment"""
        if not func_info.doc:
            # If function name is standard/simple, give some credit even without doc
            if func_info.name in ('make', 'create', 'run', 'build', 'generate'):
                return True, 0.5
            
            # If function name is very descriptive, give a small bonus instead of 0
            if len(func_info.name) > 10 or '_' in func_info.name:
                return False, 0.2
            return False, 0.0
        
        doc_len = len(func_info.doc.strip())
        
        # Try to use docstring_parser for structural analysis
        if docstring_parser:
            try:
                parsed = docstring_parser.parse(func_info.doc)
                has_desc = bool(parsed.short_description or parsed.long_description)
                has_params = len(parsed.params) > 0
                has_returns = bool(parsed.returns)
                
                # If structured info is present, give high score regardless of length
                if has_desc and (has_params or has_returns):
                    return True, 1.0
                if has_desc:
                    # If description is present, check if it's a "standard" function
                    if func_info.name in ('make', 'create', 'run', 'build', 'generate'):
                        return True, 0.9
                    return True, 0.8
            except:
                pass
        
        # Scoring criteria (Fallback to length)
        if doc_len > 200:  # Detailed documentation
            return True, 1.0
        elif doc_len > 100:  # Medium documentation
            return True, 0.7
        elif doc_len > 30:  # Short documentation
            return True, 0.4
        else:
            # Very short documentation
            # If function name is standard/simple, short doc is acceptable
            if func_info.name in ('make', 'create', 'run', 'build', 'generate'):
                return True, 0.6
            return False, 0.2
    
    @staticmethod
    def has_reasonable_params(func_info: FunctionInfo) -> Tuple[bool, float]:
        """Parameter Reasonableness Assessment"""
        num_params = len(func_info.parameters)
        
        # Ideal parameter count: 1-5
        if 1 <= num_params <= 5:
            return True, 1.0
        elif num_params == 0:  # No-param function might be a factory function
            return True, 0.8
        elif 6 <= num_params <= 8:
            return True, 0.6
        elif num_params > 10:  # Too many parameters usually indicate internal function
            return False, 0.2
        else:
            return True, 0.5
    
    @staticmethod
    def has_type_annotations(func_info: FunctionInfo) -> Tuple[bool, float]:
        """Type Annotation Completeness Assessment."""
        doc_has_types = False
        if docstring_parser and func_info.doc:
            try:
                parsed = docstring_parser.parse(func_info.doc)
                doc_has_types = any(p.type_name for p in parsed.params) or bool(parsed.returns and parsed.returns.type_name)
            except Exception:
                doc_has_types = False

        has_defaults = any(not p.get('required', True) for p in (func_info.parameters or []))

        raw_param_annotations = getattr(func_info, 'raw_param_annotations', None) or []
        raw_return_annotation = getattr(func_info, 'raw_return_annotation', None)
        has_return_annotation = raw_return_annotation not in (None, inspect.Signature.empty)

        if raw_param_annotations:
            total_params = len(raw_param_annotations)
            annotated_params = sum(1 for ann in raw_param_annotations if ann not in (None, inspect.Parameter.empty))
            param_coverage = annotated_params / max(total_params, 1)
        else:
            total_params = len(func_info.parameters or [])
            if total_params == 0:
                param_coverage = 0.0
            else:
                annotated_params = sum(1 for p in func_info.parameters if p.get('schema', {}).get('type') != 'string')
                param_coverage = annotated_params / total_params

        if total_params == 0 and has_return_annotation:
            return True, 1.0
        if param_coverage >= 0.8 and has_return_annotation:
            return True, 1.0
        if param_coverage >= 0.5 and has_return_annotation:
            return True, 0.8
        if param_coverage >= 0.5 or has_return_annotation or doc_has_types:
            return True, 0.7
        if has_defaults:
            return True, 0.6
        return False, 0.4
    
    @staticmethod
    def is_public_api(func_info: FunctionInfo) -> Tuple[bool, float]:
        """Determine if it is a public API - Universal Mechanism (Improved)"""
        # 0. Skip test/internal/experimental modules regardless of __all__
        if QualityMetrics._INTERNAL_PATTERN.search(func_info.module):
            return False, 0.0

        # 1. Name does not start with underscore
        if func_info.name.startswith('_'):
            return False, 0.0
        
        # 2. Check if in module's __all__
        try:
            module = sys.modules.get(func_info.module)
            if module and hasattr(module, '__all__'):
                if func_info.name in module.__all__:
                    return True, 1.0
                else:
                    # Not in __all__, but if top-level module, still give higher score
                    # Top-level module check: module name has one dot or is library name itself
                    module_parts = func_info.module.split('.')
                    is_top_level = len(module_parts) <= 2  # e.g. pdfkit or pdfkit.api
                    
                    if is_top_level and not func_info.class_name:
                        # Direct function of top-level module, give higher score even if not in __all__
                        return True, 0.8
                    else:
                        # Not in __all__, lower score
                        return True, 0.5
            else:
                # No __all__ attribute, judge by module hierarchy
                module_parts = func_info.module.split('.')
                is_top_level = len(module_parts) <= 2
                
                if is_top_level and not func_info.class_name:
                    # Direct function of top-level module
                    return True, 0.9
                else:
                    return True, 0.7
        except:
            pass
        
        # 3. Check if module path contains internal/_ etc.
        if re.search(r'(internal|_private|compat|testing)', func_info.module):
            return False, 0.2
        
        return True, 0.7
    
    @staticmethod
    def naming_quality(func_info: FunctionInfo) -> Tuple[bool, float]:
        """Naming Convention Assessment"""
        name = func_info.name
        
        # Good naming patterns
        good_patterns = [
            r'^[a-z][a-z0-9_]*$',  # lowercase + underscore
            r'^[A-Z][a-zA-Z0-9]*$',  # UpperCamelCase (Class name)
        ]
        
        # Bad naming patterns
        bad_patterns = [
            r'.*\d+$',  # Ends with digit (e.g. func1, test2)
            r'^(test|demo|example)_.*',  # Test/Example functions
            r'^(bench|benchmark)_.*',  # Benchmark functions
            r'.*_(internal|private|impl)$',  # Internal implementation
        ]
        
        # Check bad patterns
        for pattern in bad_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False, 0.2
        
        # Check good patterns
        for pattern in good_patterns:
            if re.match(pattern, name):
                return True, 1.0
        
        return True, 0.6

    @staticmethod
    def hierarchy_quality(func_info: FunctionInfo) -> Tuple[bool, float]:
        """Hierarchy Quality Assessment - Universal Version"""
        module_parts = func_info.module.split('.')
        
        # 0. Utility/helper/cache modules are often not intended as primary public APIs
        if any(part.lower() in ('utils', 'util', 'helpers', 'helper', 'cache') for part in module_parts[1:]):
            return True, 0.7

        # 1. Private module detection (Universal convention)
        # Any path component starting with _ usually indicates private
        # tests/testing are also common non-production code directories
        for part in module_parts:
            if part.startswith('_') or part.lower() in ('tests', 'testing', 'test'):
                return False, 0.0
        
        # 2. Depth scoring (Relative depth)
        # Shallower is better, but no longer hardcoding core/common etc.
        # Assume library name is root (depth 1)
        # root.api (depth 2) -> 1.0
        # root.sub.detail (depth 3) -> 0.8
        # root.sub.detail.impl (depth 4) -> 0.6
        
        # Base score
        score = 1.0
        
        # Depth penalty (Start from 3rd level, deduct 0.2 per level)
        # pandas (1) -> 1.0
        # pandas.io (2) -> 1.0
        # pandas.core.frame (3) -> 0.8
        # pandas.core.arrays.categorical (4) -> 0.6
        if len(module_parts) > 2:
            penalty = (len(module_parts) - 2) * 0.2
            score = max(0.4, 1.0 - penalty)
            
        return True, score


class TypeParser:
    """Type Annotation Parser"""
    
    @staticmethod
    def parse_annotation(annotation: Any, _depth: int = 0, _seen: Optional[Set[int]] = None) -> Dict[str, Any]:
        """Convert Python type annotation to OpenAPI Schema"""
        if _depth > 12:
            return {}

        if _seen is None:
            _seen = set()

        annotation_id = id(annotation)
        if annotation_id in _seen:
            return {}

        _seen.add(annotation_id)

        if annotation is None or annotation == inspect.Parameter.empty:
            # Strategy 2: Map undetermined types to {} (Any)
            return {}
        
        if isinstance(annotation, str):
            return TypeParser._parse_string_annotation(annotation)
        
        # Strategy 3: Detection based on Abstract Base Classes (ABC)
        try:
            import os
            if isinstance(annotation, type) and issubclass(annotation, os.PathLike):
                return {"type": "string"}
        except (ImportError, TypeError):
            pass
        
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        type_map = {
            int: {"type": "integer"},
            float: {"type": "number"},
            str: {"type": "string"},
            bool: {"type": "boolean"},
            bytes: {"type": "string", "format": "byte"},
        }
        
        if annotation in type_map:
            return type_map[annotation]
        
        if is_dataclass(annotation):
            return TypeParser._parse_dataclass(annotation, _depth=_depth + 1, _seen=_seen)
        
        if origin in (list, List):
            items = TypeParser.parse_annotation(args[0], _depth=_depth + 1, _seen=_seen) if args else {}
            return {"type": "array", "items": items}
        
        if origin in (dict, Dict):
            additional = TypeParser.parse_annotation(args[1], _depth=_depth + 1, _seen=_seen) if len(args) >= 2 else {}
            return {"type": "object", "additionalProperties": additional or True}
        
        if origin in (tuple, Tuple):
            return {"type": "array", "items": {"type": "string"}}
        
        if origin in (set, Set):
            items = TypeParser.parse_annotation(args[0], _depth=_depth + 1, _seen=_seen) if args else {}
            return {"type": "array", "uniqueItems": True, "items": items}
        
        # Strategy 1: Implement "Union Unwrapping"
        if origin is Union:
            schemas = []
            has_none = False
            for arg in args:
                if arg is type(None):
                    has_none = True
                    continue
                schemas.append(TypeParser.parse_annotation(arg, _depth=_depth + 1, _seen=_seen))
            
            if not schemas:
                return {}
                
            if len(schemas) == 1:
                schema = schemas[0]
                if has_none:
                    schema["nullable"] = True
                return schema
            
            # Use anyOf to allow matching any subtype
            result = {"anyOf": schemas}
            if has_none:
                result["nullable"] = True
            return result
        
        try:
            from typing import Literal
            if origin is Literal:
                return {"type": "string", "enum": list(args)}
        except ImportError:
            pass
        
        if annotation is Any:
            return {}
        
        # Strategy 2: Fix "Any" type mapping semantics
        # Map undetermined types to Empty Schema ({}) instead of "object"
        return {}
    
    @staticmethod
    def _parse_dataclass(dc: type, _depth: int = 0, _seen: Optional[Set[int]] = None) -> Dict[str, Any]:
        """Parse dataclass"""
        properties = {}
        required = []
        
        try:
            for field in fields(dc):
                properties[field.name] = TypeParser.parse_annotation(field.type, _depth=_depth + 1, _seen=_seen)
                # Fix: Use correct MISSING check
                from dataclasses import MISSING
                if field.default is MISSING and field.default_factory is MISSING:
                    required.append(field.name)
        except:
            pass
        
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema
    
    @staticmethod
    def _parse_string_annotation(annotation: str) -> Dict[str, Any]:
        """Parse string annotation"""
        annotation = annotation.strip()
        
        basic = {
            'int': {"type": "integer"},
            'float': {"type": "number"},
            'str': {"type": "string"},
            'bool': {"type": "boolean"},
            'Any': {}
        }
        
        if annotation in basic:
            return basic[annotation]
        
        if annotation.startswith(('List[', 'list[')):
            inner = annotation[5:-1]
            return {"type": "array", "items": TypeParser._parse_string_annotation(inner)}
        
        if annotation.startswith(('Dict[', 'dict[')):
            return {"type": "object"}
        
        if annotation.startswith('Optional['):
            inner = annotation[9:-1]
            schema = TypeParser._parse_string_annotation(inner)
            schema["nullable"] = True
            return schema
        
        # Strategy 2: Unparsable string annotations fallback to {} (Any)
        return {}


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


class APIAnalyzer:
    """API Analyzer - Universal Intelligent Version"""

    INTERNAL_MODULE_PATTERN = re.compile(
        r'(^|\.)(_?tests?|testing|testdata|benchmarks?|examples?|demos?|experimental|internal|_internal|private|_private|compat|legacy|deprecated|cache|cookies?|sessions?)(\.|$)',
        re.IGNORECASE
    )
    INTERNAL_PATH_PATTERN = re.compile(
        r'(^|/)(tests?|testing|testdata|benchmarks?|examples?|demos?|experimental|internal|_internal|private|_private|compat|legacy|deprecated|cache|cookies?|sessions?)(/|$)',
        re.IGNORECASE
    )

    SERIALIZABLE_TYPES = {
        int, float, str, bool, bytes, type(None),
        list, dict, tuple, set,
    }
    
    def __init__(self, library_name: str, 
                 max_depth: int = 2, 
                 skip_non_serializable: bool = False,
                 warn_on_skip: bool = True,
                 enable_state_management: bool = True,
                 path_style: str = 'auto',
                 max_functions: int = None,
                 # Added quality control parameters
                 enable_quality_filter: bool = True,
                 min_quality_score: float = 60.0,
                 enable_deduplication: bool = True,
                 quality_mode: str = 'balanced',
                 enable_input_complexity_filter: bool = True,
                 # Adaptive filtering parameters
                 enable_adaptive_filter: bool = True,
                 adaptive_keep_ratio: float = 0.3,
                 adaptive_min_keep: int = 3,
                 adaptive_max_keep: int = 30,
                 enable_parallel_scan: bool = True,
                 parallel_scan_workers: int = 4,
                 enable_analysis_cache: bool = True,
                 cache_dir: str = ".allbemcp_cache"):
        self.library_name = library_name
        self.max_depth = max_depth
        self.skip_non_serializable = skip_non_serializable
        self.warn_on_skip = warn_on_skip
        self.enable_state_management = enable_state_management
        self.path_style = path_style
        self.max_functions = max_functions
        
        # Quality control parameters
        self.enable_quality_filter = enable_quality_filter
        self.min_quality_score = min_quality_score
        self.enable_deduplication = enable_deduplication
        self.quality_mode = quality_mode
        self.enable_input_complexity_filter = enable_input_complexity_filter
        self.enable_adaptive_filter = enable_adaptive_filter
        self.adaptive_keep_ratio = adaptive_keep_ratio
        self.adaptive_min_keep = adaptive_min_keep
        self.adaptive_max_keep = adaptive_max_keep
        self.enable_parallel_scan = enable_parallel_scan
        self.parallel_scan_workers = max(1, parallel_scan_workers)
        self.enable_analysis_cache = enable_analysis_cache
        self.analysis_cache = AnalysisCache(cache_dir) if enable_analysis_cache else None

        # AST caches
        self._ast_cache: Dict[str, bool] = {}
        self._ast_return_index_cache: Dict[str, Dict[int, str]] = {}
        self._ast_name_index_cache: Dict[str, Dict[str, str]] = {}
        self._module_all_cache: Dict[str, Optional[Set[str]]] = {}
        
        # Apply quality mode presets
        self._apply_quality_mode()
        
        # Data storage
        self.functions: List[FunctionInfo] = []
        self.analyzed: Set[str] = set()
        self.skipped_functions: List[Dict[str, str]] = []
        self.object_returning_functions: List[FunctionInfo] = []
        self.function_scores: Dict[str, float] = {}
        self.quality_stats: Dict[str, Any] = {}
    
    def _apply_quality_mode(self):
        """Apply quality mode presets"""
        modes = {
            'strict': {
                'min_quality_score': 95,
                'max_functions': 50,
            },
            'balanced': {
                'min_quality_score': 75,
                'max_functions': 3000,
            },
            'permissive': {
                'min_quality_score': 60,
                'max_functions': 20000,
            }
        }
        
        if self.quality_mode in modes:
            mode_config = modes[self.quality_mode]
            # Only apply presets if not explicitly set
            if self.min_quality_score == 60.0:  # Default value
                self.min_quality_score = mode_config['min_quality_score']
            if self.max_functions is None:
                self.max_functions = mode_config['max_functions']
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze library - Enhanced version with quality filtering."""
        try:
            root = importlib.import_module(self.library_name)
        except ImportError as e:
            return {"error": f"Cannot import: {e}"}

        cache_key = None
        if self.enable_analysis_cache and self.analysis_cache:
            config_signature = self._build_analysis_config_signature()
            fingerprint = self._compute_library_fingerprint(root)
            cache_key = self.analysis_cache.make_cache_key(self.library_name, config_signature, fingerprint)
            cached = self.analysis_cache.load(cache_key)
            if cached:
                return cached
        
        # 1. Scan module
        self._scan_module(root)
        
        # 2. If quality filtering is enabled, apply post-processing
        if self.enable_quality_filter:
            self._apply_quality_filtering()
        
        # 3. Generate OpenAPI specification
        spec = self._generate_openapi()

        if cache_key and self.analysis_cache:
            self.analysis_cache.save(cache_key, spec)

        return spec

    def _build_analysis_config_signature(self) -> str:
        payload = {
            "max_depth": self.max_depth,
            "skip_non_serializable": self.skip_non_serializable,
            "enable_state_management": self.enable_state_management,
            "path_style": self.path_style,
            "max_functions": self.max_functions,
            "enable_quality_filter": self.enable_quality_filter,
            "min_quality_score": self.min_quality_score,
            "enable_deduplication": self.enable_deduplication,
            "quality_mode": self.quality_mode,
            "enable_input_complexity_filter": self.enable_input_complexity_filter,
            "enable_adaptive_filter": self.enable_adaptive_filter,
            "adaptive_keep_ratio": self.adaptive_keep_ratio,
            "adaptive_min_keep": self.adaptive_min_keep,
            "adaptive_max_keep": self.adaptive_max_keep,
        }
        return hashlib.md5(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def _compute_library_fingerprint(self, root_module: ModuleType) -> str:
        chunks: List[str] = []
        try:
            root_file = getattr(root_module, "__file__", None)
            if root_file and Path(root_file).exists():
                p = Path(root_file)
                st = p.stat()
                chunks.append(f"{p}:{st.st_mtime_ns}:{st.st_size}")

            root_paths = getattr(root_module, "__path__", None)
            if root_paths:
                for root_path in root_paths:
                    base = Path(root_path)
                    if not base.exists():
                        continue
                    for py in base.rglob("*.py"):
                        try:
                            st = py.stat()
                            chunks.append(f"{py}:{st.st_mtime_ns}:{st.st_size}")
                        except Exception:
                            continue
        except Exception:
            pass

        chunks.sort()
        payload = "|".join(chunks)
        return hashlib.md5(payload.encode("utf-8")).hexdigest()
    
    def _apply_quality_filtering(self):
        """Apply quality filtering and deduplication."""
        # 1. Calculate quality scores
        scored_functions = []
        self._module_all_cache = {}

        for func in self.functions:
            module_name = func.module
            if module_name in self._module_all_cache:
                continue
            module_obj = sys.modules.get(module_name)
            if module_obj and hasattr(module_obj, '__all__'):
                try:
                    self._module_all_cache[module_name] = set(getattr(module_obj, '__all__', []) or [])
                except Exception:
                    self._module_all_cache[module_name] = None
            else:
                self._module_all_cache[module_name] = None

        score_weights = self._get_adaptive_weights()

        for func in self.functions:
            score = self.calculate_function_score(
                func,
                score_weights,
                module_all=self._module_all_cache.get(func.module),
            )
            self.function_scores[func.qualname] = score
            
            if score >= self.min_quality_score:
                scored_functions.append((func, score))
        
        # Fallback mechanism: if too few functions found and mode is not permissive, try lowering threshold
        # If we found very few high-quality functions, we should include medium-quality ones too
        if len(scored_functions) < 5 and self.min_quality_score > 60:
            existing_qualnames = {f.qualname for f, s in scored_functions}
            
            for func in self.functions:
                if func.qualname in existing_qualnames:
                    continue
                    
                score = self.function_scores[func.qualname]
                # Lower threshold to 60 to include more functions
                if score >= 60:
                    scored_functions.append((func, score))

        # 1.5 Adaptive filtering: keep the best functions per module (self-tuning)
        if self.enable_adaptive_filter and scored_functions:
            scored_functions = self._apply_adaptive_filter(scored_functions)

        # 2. Deduplication
        if self.enable_deduplication and len(scored_functions) > 0:
            funcs = [f for f, s in scored_functions]
            deduped = self._deduplicate_similar_functions(funcs)
            # Use a set for O(1) membership to avoid O(n^2) filtering on large libraries.
            deduped_qualnames = {f.qualname for f in deduped}
            scored_functions = [(f, s) for f, s in scored_functions if f.qualname in deduped_qualnames]
        
        # 3. Sort by score and limit quantity
        scored_functions.sort(key=lambda x: x[1], reverse=True)
        if self.max_functions and len(scored_functions) > self.max_functions:
            scored_functions = scored_functions[:self.max_functions]
        
        # 4. Update function list
        self.functions = [f for f, s in scored_functions]
        
        # 5. Record statistics
        self._collect_quality_stats(scored_functions)

    def _apply_adaptive_filter(self, scored_functions: List[Tuple[FunctionInfo, float]]) -> List[Tuple[FunctionInfo, float]]:
        """Adaptive filter using two-phase allocation (fair minimum + weighted remainder)."""
        by_module: Dict[str, List[Tuple[FunctionInfo, float]]] = defaultdict(list)
        for func, score in scored_functions:
            by_module[func.module].append((func, score))

        if not by_module:
            return []

        module_weights: Dict[str, float] = {}
        for module, items in by_module.items():
            depth = max(1, len(module.split('.')))
            module_obj = sys.modules.get(module)
            has_all = bool(module_obj and hasattr(module_obj, '__all__'))
            avg_score = sum(score for _, score in items) / len(items)
            module_weights[module] = ((1.0 / depth) * (2.0 if has_all else 1.0)) * (0.5 + avg_score / 200.0)

        total_items = len(scored_functions)
        total_budget = int(total_items * self.adaptive_keep_ratio)
        min_needed = sum(min(self.adaptive_min_keep, len(items)) for items in by_module.values())
        total_budget = min(total_items, max(total_budget, min_needed, 1))

        for items in by_module.values():
            items.sort(key=lambda x: x[1], reverse=True)

        kept: List[Tuple[FunctionInfo, float]] = []
        allocated: Dict[str, int] = {module: 0 for module in by_module}

        # Phase 1: minimum keep per module
        for module, items in by_module.items():
            min_keep = min(self.adaptive_min_keep, self.adaptive_max_keep, len(items))
            if min_keep <= 0:
                continue
            kept.extend(items[:min_keep])
            allocated[module] = min_keep

        remaining_budget = total_budget - len(kept)
        if remaining_budget <= 0:
            kept.sort(key=lambda x: x[1], reverse=True)
            return kept[:total_budget]

        # Phase 2: weighted distribution of remaining budget
        total_weight = sum(module_weights.values()) or 1.0
        extra_targets: Dict[str, int] = {module: 0 for module in by_module}
        for module, items in by_module.items():
            capacity = min(self.adaptive_max_keep, len(items)) - allocated[module]
            if capacity <= 0:
                continue
            quota = int(remaining_budget * (module_weights[module] / total_weight))
            extra_targets[module] = min(capacity, max(0, quota))

        assigned = sum(extra_targets.values())
        if assigned < remaining_budget:
            ranked_modules = sorted(
                by_module.keys(),
                key=lambda module: module_weights[module],
                reverse=True,
            )
            remaining = remaining_budget - assigned
            for module in ranked_modules:
                if remaining <= 0:
                    break
                items = by_module[module]
                capacity = min(self.adaptive_max_keep, len(items)) - allocated[module] - extra_targets[module]
                if capacity <= 0:
                    continue
                take = min(capacity, remaining)
                extra_targets[module] += take
                remaining -= take

        candidates: List[Tuple[FunctionInfo, float]] = []
        for module, items in by_module.items():
            start = allocated[module]
            end = start + extra_targets[module]
            candidates.extend(items[start:end])

        if len(candidates) < remaining_budget:
            spillover: List[Tuple[FunctionInfo, float]] = []
            for module, items in by_module.items():
                start = allocated[module] + extra_targets[module]
                max_end = min(self.adaptive_max_keep, len(items))
                if start < max_end:
                    spillover.extend(items[start:max_end])
            spillover.sort(key=lambda x: x[1], reverse=True)
            candidates.extend(spillover[: remaining_budget - len(candidates)])

        kept.extend(candidates[:remaining_budget])
        kept.sort(key=lambda x: x[1], reverse=True)
        return kept[:total_budget]
    
    def _get_adaptive_weights(self) -> Dict[str, float]:
        """Get score weights adapted to the current library characteristics."""
        if not self.functions:
            return {
                'documentation': 25,
                'type_annotations': 20,
                'public_api': 20,
                'naming': 10,
                'hierarchy': 25,
            }

        total = max(len(self.functions), 1)
        doc_coverage = sum(1 for f in self.functions if f.doc) / total
        type_coverage = sum(
            1
            for f in self.functions
            if getattr(f, 'raw_return_annotation', None) not in (None, inspect.Signature.empty)
        ) / total
        all_coverage = sum(
            1
            for f in self.functions
            if (self._module_all_cache.get(f.module) if self._module_all_cache else None) is not None
        ) / total

        dynamic = {
            'documentation': 10 + 20 * doc_coverage,
            'type_annotations': 10 + 15 * type_coverage,
            'public_api': 15 + 10 * all_coverage,
            'naming': 10,
            'hierarchy': 15 + 10 * (1 - doc_coverage),
        }
        total_weight = sum(dynamic.values()) or 1.0
        return {k: (v * 100.0 / total_weight) for k, v in dynamic.items()}

    def calculate_function_score(
        self,
        func_info: FunctionInfo,
        weights: Optional[Dict[str, float]] = None,
        module_all: Optional[Set[str]] = None,
    ) -> float:
        """Calculate function quality score (0-100)."""
        score = 0.0
        weights = weights or self._get_adaptive_weights()

        has_module_all = module_all is not None
        all_gate_bonus = False
        if has_module_all and not func_info.class_name:
            if func_info.name in module_all:
                all_gate_bonus = True
            else:
                return 0.0
        
        # 1. Documentation quality
        _, doc_score = QualityMetrics.has_good_documentation(func_info)
        score += weights['documentation'] * doc_score
        
        # 2. Type annotations
        _, type_score = QualityMetrics.has_type_annotations(func_info)
        score += weights['type_annotations'] * type_score
        
        # 3. Public API
        _, public_score = QualityMetrics.is_public_api(func_info)
        if public_score == 0.0:
            return 0.0
        score += weights['public_api'] * public_score
        
        # 4. Naming convention
        _, name_score = QualityMetrics.naming_quality(func_info)
        score += weights['naming'] * name_score
        
        # 5. Hierarchy quality
        _, hierarchy_score = QualityMetrics.hierarchy_quality(func_info)
        score += weights['hierarchy'] * hierarchy_score
        
        # Extra points
        # - Returns simple type instead of object (+5)
        if not func_info.returns_object:
            score += 5

        final_score = min(score, 100.0)
        if all_gate_bonus:
            return max(90.0, final_score)
        return final_score
    
    def _normalize_function_purpose(self, func_name: str) -> str:
        """Extract core semantic purpose of the function"""
        # Remove common prefixes
        name = func_name.lower()
        prefixes = ['get_', 'fetch_', 'query_', 'find_', 'search_',
                   'create_', 'add_', 'insert_', 'make_',
                   'update_', 'modify_', 'edit_', 'set_',
                   'delete_', 'remove_', 'del_']
        
        for prefix in prefixes:
            if name.startswith(prefix):
                return name[len(prefix):]
        
        return name
    
    def _deduplicate_similar_functions(self, functions: List[FunctionInfo]) -> List[FunctionInfo]:
        """Remove redundant functions with similar functionality"""
        # Group by core purpose
        groups = defaultdict(list)
        for func in functions:
            purpose = self._normalize_function_purpose(func.name)
            param_sig = frozenset(p.get('name', '') for p in func.parameters)
            key = (purpose, param_sig)
            groups[key].append(func)
        
        # Keep only the best one per group
        result = []
        for group_funcs in groups.values():
            if len(group_funcs) == 1:
                result.append(group_funcs[0])
            else:
                # Select the best function
                best = max(group_funcs, key=lambda f: (
                    # 1. Quality score
                    self.function_scores.get(f.qualname, 0),
                    # 2. Documentation length
                    len(f.doc or ''),
                    # 3. Fewer parameters is better
                    -len(f.parameters),
                    # 4. In __all__
                    f.name in getattr(sys.modules.get(f.module), '__all__', []),
                    # 5. Name length (shorter is usually more generic)
                    -len(f.name),
                ))
                result.append(best)
        
        return result
    
    def _collect_quality_stats(self, scored_functions: List[Tuple[FunctionInfo, float]]):
        """收集质量统计信息"""
        self.quality_stats = {
            'total_modules_scanned': len(self.analyzed),
            'total_functions_found': len(self.function_scores),
            'functions_after_filtering': len(self.functions),
            'avg_score': sum(s for _, s in scored_functions) / len(scored_functions) if scored_functions else 0,
            'score_distribution': {
                '90-100': len([s for _, s in scored_functions if s >= 90]),
                '80-89': len([s for _, s in scored_functions if 80 <= s < 90]),
                '70-79': len([s for _, s in scored_functions if 70 <= s < 80]),
                '60-69': len([s for _, s in scored_functions if 60 <= s < 70]),
            },
            'top_10_functions': [
                {'name': f.qualname, 'score': round(s, 1)}
                for f, s in scored_functions[:10]
            ]
        }
    
    def _scan_module(self, module: ModuleType, depth: int = 0):
        """扫描模块"""
        if depth > self.max_depth or module.__name__ in self.analyzed:
            return
        
        # Skip test/internal/experimental modules early to reduce noise and speed up scanning
        if self._is_internal_module(module.__name__, getattr(module, "__file__", None)):
            return
        
        self.analyzed.add(module.__name__)

        self._prepare_module_ast_cache(module)
        
        try:
            # 优先检查 __all__
            if hasattr(module, '__all__'):
                members = []
                for name in module.__all__:
                    try:
                        val = getattr(module, name)
                        members.append((name, val))
                    except AttributeError:
                        continue
            else:
                members = list(vars(module).items())

            for name, obj in members:
                if inspect.isfunction(obj):
                    if self._should_include(name, obj, module, is_method=False):
                        info = self._extract_function(name, obj, module)
                        if info:
                            # Check if returns complex object
                            self._analyze_return_type(info, obj)
                            
                            # Check if suitable for API
                            if self._is_suitable_for_api(info, obj):
                                self.functions.append(info)
                                if info.returns_object:
                                    self.object_returning_functions.append(info)
                            elif self.skip_non_serializable:
                                # Record skip reason
                                reason = self._get_unsuitability_reason(info, obj)
                                self.skipped_functions.append({
                                    'qualname': info.qualname,
                                    'reason': reason
                                })
                
                elif inspect.isclass(obj) and not name.startswith('_'):
                    self._scan_class(obj, module)
        except:
            pass
        
        if hasattr(module, '__path__'):
            try:
                submodule_names: List[str] = []
                for _, subname, _ in pkgutil.iter_modules(module.__path__, f"{module.__name__}."):
                    # Filter private modules and test modules (Universal rule)
                    last_part = subname.split('.')[-1]
                    if last_part.startswith('_') or last_part.lower() in ('tests', 'testing', 'test'):
                        continue

                    submodule_names.append(subname)

                submodules: List[ModuleType] = []
                if (
                    self.enable_parallel_scan
                    and self.parallel_scan_workers > 1
                    and len(submodule_names) > 3
                    and depth == 0
                ):
                    with ThreadPoolExecutor(max_workers=self.parallel_scan_workers) as executor:
                        for sub in executor.map(self._safe_import_submodule, submodule_names):
                            if sub is not None:
                                submodules.append(sub)
                else:
                    for subname in submodule_names:
                        sub = self._safe_import_submodule(subname)
                        if sub is not None:
                            submodules.append(sub)

                for sub in submodules:
                    self._scan_module(sub, depth + 1)
            except:
                pass

    def _safe_import_submodule(self, subname: str) -> Optional[ModuleType]:
        try:
            return importlib.import_module(subname)
        except Exception:
            return None

    def _prepare_module_ast_cache(self, module: ModuleType) -> None:
        file_path = getattr(module, '__file__', None)
        if not file_path:
            return

        p = Path(file_path)
        if p.suffix != '.py':
            return

        file_key = str(p.resolve())
        if file_key in self._ast_cache:
            return

        try:
            source = p.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(source, filename=file_key)
        except Exception:
            self._ast_cache[file_key] = True
            self._ast_return_index_cache[file_key] = {}
            self._ast_name_index_cache[file_key] = {}
            return

        self._ast_cache[file_key] = True
        by_lineno: Dict[int, str] = {}
        by_name: Dict[str, str] = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inferred = self._infer_return_type_from_ast_node(node)
                if inferred:
                    by_lineno[node.lineno] = inferred
                    by_name.setdefault(node.name, inferred)

        self._ast_return_index_cache[file_key] = by_lineno
        self._ast_name_index_cache[file_key] = by_name

    def _infer_return_type_from_ast_node(self, func_def: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Optional[str]:
        returns: List[str] = []
        for node in ast.walk(func_def):
            if isinstance(node, ast.Return):
                if node.value is None:
                    returns.append('None')
                elif isinstance(node.value, ast.Constant):
                    if node.value.value is None:
                        returns.append('None')
                    else:
                        returns.append(type(node.value.value).__name__)
                elif isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        returns.append(node.value.func.id)
                    elif isinstance(node.value.func, ast.Attribute):
                        returns.append(node.value.func.attr)

        if not returns:
            return 'None'
        unique = list(dict.fromkeys(returns))
        if len(unique) == 1:
            return unique[0]
        return 'Union[' + ', '.join(unique) + ']'
    
    def _scan_class(self, cls: type, module: ModuleType):
        """Scan class and expose constructor factory + static/class methods."""
        # Constructor factory: create_<class> that returns object_id through runtime object storage.
        try:
            init_obj = getattr(cls, '__init__', None)
            if callable(init_obj):
                constructor_name = f"create_{cls.__name__.lower()}"
                constructor_info = self._extract_function(
                    constructor_name,
                    init_obj,
                    module,
                    class_name=cls.__name__,
                    target_name='__init__',
                    is_constructor=True,
                )
                if constructor_info and self._is_suitable_for_api(constructor_info, init_obj):
                    constructor_info.returns_object = True
                    constructor_info.object_methods = self._extract_object_methods(cls)
                    self.functions.append(constructor_info)
                    self.object_returning_functions.append(constructor_info)
        except Exception:
            pass
        
        for name, member in inspect.getmembers(cls):
            if name.startswith('_'):
                continue
            
            # Must be callable
            if not callable(member):
                continue
                
            should_extract = False
            
            # Case 1: Class method (@classmethod)
            # inspect.ismethod() returns True for class methods, and __self__ is bound to the class
            if inspect.ismethod(member) and member.__self__ is cls:
                should_extract = True
                
            # Case 2: Function (could be instance method or static method)
            elif inspect.isfunction(member):
                try:
                    sig = inspect.signature(member)
                    params = list(sig.parameters.keys())
                    
                    # Signature introspection filtering
                    if not params:
                        # No-param function -> static method -> keep
                        should_extract = True
                    elif params[0] == 'self':
                        # First param is self -> instance method -> filter
                        should_extract = False
                    elif params[0] == 'cls':
                        # First param is cls -> class method (not decorated with @classmethod) -> keep
                        should_extract = True
                    else:
                        # Other cases -> static method -> keep
                        should_extract = True
                except (ValueError, TypeError):
                    # Cannot get signature -> conservatively skip
                    should_extract = False
            
            if should_extract:
                if self._should_include(name, member, module, is_method=True):
                    info = self._extract_function(name, member, module, class_name=cls.__name__)
                    if info:
                        # Analyze return type
                        self._analyze_return_type(info, member)
                        
                        # Check if suitable for API
                        if self._is_suitable_for_api(info, member):
                            self.functions.append(info)
                            if info.returns_object:
                                self.object_returning_functions.append(info)
                        elif self.skip_non_serializable:
                            reason = self._get_unsuitability_reason(info, member)
                            self.skipped_functions.append({
                                'qualname': info.qualname,
                                'reason': reason
                            })
    
    def _should_include(self, name: str, obj: Any, module: ModuleType = None, is_method: bool = False) -> bool:
        """Determine whether to include - Universal Intelligent Version"""
        checks = [
            lambda: callable(obj) and not name.startswith('_'),
            lambda: not module or not self._is_internal_module(module.__name__, getattr(module, '__file__', None)),
            lambda: self._belongs_to_library(obj),
            lambda: self._passes_all_check(name, module, is_method),
            lambda: self._passes_definition_check(obj, module, is_method),
        ]
        return all(check() for check in checks)

    def _belongs_to_library(self, obj: Any) -> bool:
        obj_module = getattr(obj, '__module__', None)
        if not obj_module:
            return True
        if not obj_module.startswith(self.library_name):
            return False
        return not self._is_internal_module(obj_module, None)

    def _passes_all_check(self, name: str, module: Optional[ModuleType], is_method: bool) -> bool:
        if is_method or not module:
            return True

        if hasattr(module, '__all__'):
            return name in module.__all__

        return True

    def _passes_definition_check(self, obj: Any, module: Optional[ModuleType], is_method: bool) -> bool:
        if is_method or not module:
            return True

        obj_module = getattr(obj, '__module__', None)
        if obj_module == module.__name__:
            return True

        if obj_module and obj_module.startswith(f"{self.library_name}."):
            return True

        module_file = getattr(module, '__file__', '') or ''
        is_init = module_file.endswith('__init__.py')
        if is_init and obj_module and obj_module.startswith(module.__name__):
            return True

        return False

    def _is_internal_module(self, module_name: str, module_file: Optional[str]) -> bool:
        """Heuristic filter for test/internal/experimental modules."""
        if module_name and self.INTERNAL_MODULE_PATTERN.search(module_name):
            return True
        if module_file and self.INTERNAL_PATH_PATTERN.search(module_file.replace("\\", "/")):
            return True
        return False
    
    def _infer_return_type_from_ast(self, func_obj: Any) -> Optional[str]:
        """Infer return type via AST analysis (Static analysis, no side effects)"""
        try:
            file_path = inspect.getsourcefile(func_obj)
            if file_path:
                file_key = str(Path(file_path).resolve())
                if file_key not in self._ast_return_index_cache:
                    module = inspect.getmodule(func_obj)
                    if module:
                        self._prepare_module_ast_cache(module)

                line_index = self._ast_return_index_cache.get(file_key, {})
                name_index = self._ast_name_index_cache.get(file_key, {})
                try:
                    _, start_line = inspect.getsourcelines(func_obj)
                except Exception:
                    start_line = None

                if start_line and start_line in line_index:
                    return line_index[start_line]

                func_name = getattr(func_obj, '__name__', None)
                if func_name and func_name in name_index:
                    return name_index[func_name]
        except Exception:
            pass

        try:
            source = inspect.getsource(func_obj)
            # Handle indentation issues
            source = inspect.cleandoc(source)
            tree = ast.parse(source)
            
            # Find function definition
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_def = node
                    break
            
            if not func_def:
                return None

            return self._infer_return_type_from_ast_node(func_def)
            
        except Exception:
            return None

    def _analyze_return_type(self, func_info: FunctionInfo, func_obj: Any):
        """Analyze function return type, check if it returns a complex object"""
        if not self.enable_state_management:
            return
        
        # 1. Check type annotation first
        if func_info.return_type is not None and func_info.return_type != inspect.Signature.empty:
            if not self._is_type_serializable(func_info.return_type):
                func_info.returns_object = True
                func_info.object_methods = self._extract_object_methods(func_info.return_type)
                return
        
        # 2. AST static analysis (replaces runtime check)
        # Runtime check causes severe performance issues and side effects in large libraries (like pandas)
        try:
            inferred_type = self._infer_return_type_from_ast(func_obj)
            if inferred_type:
                # Simple heuristic: if it looks like a class name
                if inferred_type[0].isupper() and inferred_type not in ('None', 'True', 'False'):
                    # Check if basic type
                    if inferred_type not in ('int', 'float', 'str', 'bool', 'list', 'dict', 'set', 'tuple'):
                        func_info.returns_object = True
                        # Try to get definition of that type (if possible)
                        # Here we cannot easily get the class object, so just mark as object
                        return
        except:
            pass
    
    def _extract_object_methods(self, obj_type: Any) -> List[Dict]:
        """Extract available methods of the object"""
        methods = []
        
        try:
            if isinstance(obj_type, type):
                for name, method in inspect.getmembers(obj_type, predicate=inspect.isfunction):
                    if name.startswith('_'):
                        continue
                    
                    try:
                        sig = inspect.signature(method)
                        params = []
                        
                        for pname, param in sig.parameters.items():
                            if pname in ('self', 'cls'):
                                continue
                            params.append({
                                'name': pname,
                                'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                                'required': param.default == inspect.Parameter.empty
                            })
                        
                        methods.append({
                            'name': name,
                            'params': params,
                            'doc': inspect.getdoc(method) or ''
                        })
                    except:
                        pass
        except:
            pass
        
        return methods[:20]  # Limit quantity
    
    def _is_type_serializable(self, annotation: Any) -> bool:
        """Check if type is serializable - Universal Mechanism"""
        if annotation is None or annotation == inspect.Parameter.empty:
            return True  # No type annotation, assume yes
        
        # Basic types
        if annotation in self.SERIALIZABLE_TYPES:
            return True
        
        # String annotations
        if isinstance(annotation, str):
            annotation_lower = annotation.lower()
            if annotation_lower in ('int', 'float', 'str', 'bool', 'bytes', 'none', 'any'):
                return True
            if annotation_lower.startswith(('list', 'dict', 'tuple', 'set', 'optional')):
                return True
            return False
        
        # Types from typing module
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        # List, Dict, Tuple, Set, Optional etc.
        if origin in (list, dict, tuple, set, List, Dict, Tuple, Set):
            # Recursively check internal types
            if args:
                return all(self._is_type_serializable(arg) for arg in args)
            return True
        
        # Union and Optional
        if origin is Union:
            return all(self._is_type_serializable(arg) for arg in args)
        
        # Any
        if annotation is Any:
            return True
        
        # dataclass is serializable
        if is_dataclass(annotation):
            return True
        
        # Check if Pydantic BaseModel
        try:
            from pydantic import BaseModel
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                return True
        except ImportError:
            pass
        
        # Other custom types - Judge by trying to serialize
        # For user custom classes, if they have __dict__ attribute, usually serializable
        if isinstance(annotation, type):
            if hasattr(annotation, '__dict__'):
                # Try to check if it has simple attributes
                return True
        
        return False
    
    def _check_input_complexity(self, func_obj: Any) -> bool:
        """Input complexity filter: Only allow functions accepting basic types or container types"""
        try:
            sig = inspect.signature(func_obj)
            for name, param in sig.parameters.items():
                # Ignore self, cls
                if name in ('self', 'cls'):
                    continue
                
                # Only check required parameters (no default value)
                if param.default != inspect.Parameter.empty:
                    continue
                
                # Check type annotation
                annotation = param.annotation
                
                # If no annotation, treat as Any (Safe), unless we want to be very strict
                # But for compatibility, we assume no annotation is safe (or undetermined)
                if annotation == inspect.Parameter.empty:
                    continue

                if not self._is_safe_input_type(annotation):
                    return False
            
            return True
        except:
            # If cannot get signature, conservatively keep (or discard?)
            # Usually functions without signature might not be Python functions
            return True

    def _is_safe_input_type(self, annotation: Any) -> bool:
        """Check if type is safe (basic type or container)"""
        if annotation is None or annotation == inspect.Parameter.empty:
            return True

        # Handle string annotations
        if isinstance(annotation, str):
            # Handle Python 3.10+ style unions (A | B)
            if '|' in annotation:
                parts = [p.strip() for p in annotation.split('|')]
                return any(self._is_safe_input_type(p) for p in parts)

            ann_lower = annotation.lower()
            # Basic types
            if ann_lower in ('int', 'float', 'str', 'bool', 'bytes', 'none', 'any', 'filepath', 'path'):
                return True
            # Container types
            if ann_lower in ('list', 'dict', 'set', 'tuple', 'sequence', 'iterable', 'mapping'):
                return True
            # Generic containers
            if '[' in annotation:
                base = annotation.split('[')[0].lower()
                if base in ('list', 'dict', 'union', 'optional', 'set', 'tuple', 'sequence', 'iterable', 'mapping'):
                    return True
            return False

        # Handle typing objects
        origin = get_origin(annotation)
        args = get_args(annotation)

        # Basic types
        if annotation in (int, float, str, bool, list, dict, set, tuple, bytes, type(None)):
            return True
        
        if annotation is Any:
            return True

        # Container types
        if origin in (list, dict, set, tuple, List, Dict, Set, Tuple, Sequence, Iterable, Mapping):
            return True
        
        # Union (as long as one is safe, consider safe, because caller can choose the safe one)
        if origin is Union:
            return any(self._is_safe_input_type(arg) for arg in args)
            
        # PathLike (treat as string)
        try:
            import os
            if isinstance(annotation, type) and issubclass(annotation, os.PathLike):
                return True
        except:
            pass

        return False
    
    def _suitable_for_api_via_signature(self, func_info: FunctionInfo, func_obj: Any) -> bool:
        """Check if function is suitable for API via signature"""
        try:
            sig = inspect.signature(func_obj)
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                # Check if parameter type is serializable
                if not self._is_type_serializable(param.annotation):
                    return False
                
                # Check if default value is serializable
                if param.default != inspect.Parameter.empty:
                    if not self._is_value_serializable(param.default):
                        return False
        except:
            return False
        
        # 2. If state management enabled, functions returning objects are also accepted
        if self.enable_state_management and func_info.returns_object:
            return True
        
        # 3. Check return type annotation
        if func_info.return_type is not None:
            if not self._is_type_serializable(func_info.return_type):
                # If state management not enabled, reject
                if not self.enable_state_management:
                    return False
        
        return True
    
    def _is_suitable_for_api(self, func_info: FunctionInfo, func_obj: Any) -> bool:
        """Check if function is suitable for API"""
        # 1. Input complexity filter
        if self.enable_input_complexity_filter:
            if not self._check_input_complexity(func_obj):
                return False

        if not self.skip_non_serializable:
            return True
        
        # Try to judge via signature
        if self._suitable_for_api_via_signature(func_info, func_obj):
            return True
        
        # Try to judge via AST analysis
        if self.enable_state_management and func_info.returns_object:
            # Function returning object, allow as API
            return True
        
        if func_info.return_type is not None:
            if not self._is_type_serializable(func_info.return_type):
                # If state management not enabled, reject
                if not self.enable_state_management:
                    return False
        
        return True
    
    def _is_value_serializable(self, value: Any) -> bool:
        """Check if value is JSON serializable"""
        if value is None:
            return True
        if isinstance(value, (int, float, str, bool)):
            return True
        if isinstance(value, (list, tuple, dict, set)):
            return True
        # Other complex objects considered not serializable
        return False
    
    def _get_unsuitability_reason(self, func_info: FunctionInfo, func_obj: Any) -> str:
        """Get reason why function is not suitable for API"""
        reasons = []
        
        # Check parameters
        try:
            sig = inspect.signature(func_obj)
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                if not self._is_type_serializable(param.annotation):
                    param_type = self._get_type_name(param.annotation)
                    reasons.append(f"Parameter '{param_name}' type not serializable ({param_type})")
        except:
            pass
        
        # Check return type annotation
        if func_info.return_type is not None:
            if not self._is_type_serializable(func_info.return_type):
                return_type = self._get_type_name(func_info.return_type)
                reasons.append(f"Return type not serializable ({return_type})")
        
        # Check runtime return value
        if not reasons and (func_info.return_type is None or func_info.return_type == inspect.Signature.empty):
            if not self.enable_state_management:
                reasons.append("Return type unknown and state management not enabled")
        
        return "; ".join(reasons) if reasons else "Unknown reason"
    
    def _get_type_name(self, annotation: Any) -> str:
        """Get readable name of type"""
        if annotation is None or annotation == inspect.Parameter.empty:
            return "Unknown"
        
        if isinstance(annotation, str):
            return annotation
        
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        
        return str(annotation)
    
    def _parse_docstring(self, obj: Any) -> Tuple[Optional[str], Optional[Any], Dict[str, Any]]:
        """Parse docstring and build param docs map"""
        doc_string = inspect.getdoc(obj)
        parsed_doc = None
        param_docs: Dict[str, Any] = {}
        if doc_string and docstring_parser:
            try:
                parsed_doc = docstring_parser.parse(doc_string)
                for p in parsed_doc.params:
                    param_docs[p.arg_name] = p
            except:
                pass
        return doc_string, parsed_doc, param_docs

    def _extract_parameters(
        self,
        sig: inspect.Signature,
        param_docs: Dict[str, Any],
        parsed_doc: Optional[Any],
        func_name: str
    ) -> Tuple[List[Dict[str, Any]], List[Any]]:
        """Extract parameters and raw annotations from signature and docstring"""
        parameters: List[Dict[str, Any]] = []
        raw_param_annotations: List[Any] = []
        existing_param_names = set()

        for pname, param in sig.parameters.items():
            if pname in ('self', 'cls'):
                continue

            # Record raw annotations
            raw_param_annotations.append(param.annotation)

            # Handle **kwargs
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                # Extract extra parameters from docstring
                if parsed_doc:
                    for doc_p in parsed_doc.params:
                        if doc_p.arg_name not in existing_param_names and doc_p.arg_name not in ('self', 'cls', 'args', 'kwargs'):
                            # This is a parameter only existing in docstring (passed via kwargs)
                            param_info = self._create_param_from_doc(doc_p, func_name)
                            parameters.append(param_info)
                continue

            # Skip *args
            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                continue

            existing_param_names.add(pname)

            # Get doc info first for optional check
            doc_param = param_docs.get(pname)
            description = doc_param.description if doc_param else None

            # Check if parameter is optional (from default value, is_optional flag, or description)
            has_default = param.default != inspect.Parameter.empty
            default_value = None
            if has_default:
                default_value = self._serialize_default(param.default)

            # Check if description indicates optional (e.g., "(optional) ..." or contains "optional")
            is_optional_from_desc = description and (
                description.strip().lower().startswith('(optional)') or
                'optional' in description.lower()
            )
            # Determine if parameter is optional: has default OR is_optional flag OR description says optional
            is_optional = has_default or (doc_param and doc_param.is_optional) or is_optional_from_desc

            # Parse type: Prioritize annotation in signature, if Any or empty, try to use type in docstring
            schema = TypeParser.parse_annotation(param.annotation)
            if (not schema or schema == {}) and doc_param and doc_param.type_name:
                schema = TypeParser._parse_string_annotation(doc_param.type_name)

            # If type uncertain, do not specify type, allow any type (Any)
            if not schema:
                schema = {}

            # Add description
            if description:
                schema["description"] = description

            # Try to extract enum values from description
            if description and "enum" not in schema:
                enums = self._extract_enums_from_description(description)
                if enums:
                    schema["enum"] = enums
                    if "type" not in schema or schema.get("type") == "object":
                        schema["type"] = "string"

            param_info = {
                "name": pname,
                "required": not is_optional,
                "schema": schema,
                "in": self._classify_param(pname, func_name)
            }

            if default_value is not None:
                param_info["default"] = default_value

            parameters.append(param_info)

        return parameters, raw_param_annotations

    def _extract_function(
        self,
        name: str,
        obj: Any,
        module: ModuleType,
        class_name: Optional[str] = None,
        target_name: Optional[str] = None,
        is_constructor: bool = False,
    ) -> Optional[FunctionInfo]:
        """Extract function information"""
        try:
            sig = inspect.signature(obj)
        except:
            return None
        
        # Parse docstring and parameters
        doc_string, parsed_doc, param_docs = self._parse_docstring(obj)
        parameters, raw_param_annotations = self._extract_parameters(sig, param_docs, parsed_doc, name)
        
        return_type = None
        raw_return_annotation = sig.return_annotation
        if sig.return_annotation != inspect.Signature.empty:
            return_type = sig.return_annotation
        
        http_method = self._infer_method(name)
        qualname = f"{module.__name__}.{class_name}.{name}" if class_name else f"{module.__name__}.{name}"
        
        # 🔥 Pass module name
        path = self._generate_path(name, parameters, class_name, module_name=module.__name__)
        
        return FunctionInfo(
            name=name,
            module=module.__name__,
            class_name=class_name,
            qualname=qualname,
            signature=f"{name}{sig}",
            doc=doc_string,
            parameters=parameters,
            return_type=return_type,
            is_async=inspect.iscoroutinefunction(obj),
            http_method=http_method,
            path=path,
            raw_param_annotations=raw_param_annotations,
            raw_return_annotation=raw_return_annotation,
            target_name=target_name or name,
            is_constructor=is_constructor,
        )

    def _extract_enums_from_description(self, description: str) -> Optional[List[str]]:
        """Extract enum values from description"""
        if not description:
            return None
            
        # Pattern 1: One of: 'a', 'b', 'c'
        match = re.search(r'One of:? (.*)', description, re.IGNORECASE)
        if match:
            values_str = match.group(1)
            # Try to extract content in quotes
            values = re.findall(r"['\"]([^'\"]+)['\"]", values_str)
            if values:
                return values
            # Try comma separated
            return [v.strip() for v in values_str.split(',') if v.strip()]
            
        # Pattern 2: {'a', 'b', 'c'}
        match = re.search(r'\{([^}]+)\}', description)
        if match:
            values_str = match.group(1)
            values = re.findall(r"['\"]([^'\"]+)['\"]", values_str)
            if values:
                return values
        
        return None

    def _create_param_from_doc(self, doc_param: Any, func_name: str) -> Dict[str, Any]:
        """Create parameter info from docstring parameter"""
        schema = TypeParser._parse_string_annotation(doc_param.type_name) if doc_param.type_name else {"type": "string"}
        
        description = doc_param.description
        if description:
            schema["description"] = description
            enums = self._extract_enums_from_description(description)
            if enums:
                schema["enum"] = enums
                if "type" not in schema or schema.get("type") == "object":
                    schema["type"] = "string"
        
        # Check if parameter is optional:
        # 1. from is_optional flag
        # 2. description starts with "(optional)"
        # 3. parameter name contains 'kwargs' or 'args' (variadic params are always optional)
        # 4. description contains "optional" (case insensitive)
        is_optional_from_desc = description and (
            description.strip().lower().startswith('(optional)') or
            'optional' in description.lower()
        )
        is_variadic = 'kwargs' in doc_param.arg_name.lower() or doc_param.arg_name == 'args'
        is_optional = doc_param.is_optional or is_optional_from_desc or is_variadic
        
        return {
            "name": doc_param.arg_name,
            "required": not is_optional,
            "schema": schema,
            "in": self._classify_param(doc_param.arg_name, func_name)
        }
    
    def _serialize_default(self, value: Any) -> Any:
        """Safely serialize default value"""
        if value is None:
            return None
        
        if isinstance(value, (int, float, str, bool)):
            return value
        
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, dict):
            return value
        
        try:
            return str(value)
        except:
            return None
    
    def _classify_param(self, param_name: str, func_name: str) -> str:
        """Classify parameter"""
        if re.match(r'.*_?id$', param_name, re.IGNORECASE):
            return 'path'
        return 'query'
    
    def _infer_method(self, name: str) -> str:
        """Infer HTTP method"""
        name_lower = name.lower()
        
        if any(name_lower.startswith(p) for p in ['get', 'list', 'fetch', 'search', 'query', 'find']):
            return 'get'
        elif any(name_lower.startswith(p) for p in ['create', 'add', 'insert', 'post']):
            return 'post'
        elif any(name_lower.startswith(p) for p in ['update', 'modify', 'edit', 'put']):
            return 'put'
        elif any(name_lower.startswith(p) for p in ['patch']):
            return 'patch'
        elif any(name_lower.startswith(p) for p in ['delete', 'remove']):
            return 'delete'
        elif name_lower in ['load', 'loads', 'read', 'parse', 'decode']:
            return 'get'
        elif name_lower in ['dump', 'dumps', 'write', 'save', 'encode']:
            return 'post'
        else:
            return 'post'
    
    def _generate_path(self, name: str, parameters: List[Dict], class_name: Optional[str] = None, module_name: str = None) -> str:
        """Generate path (supports multiple strategies)"""
        
        # 1. Simple: Only use class name and function name (default, may conflict)
        if self.path_style == 'simple':
            base = f"/{class_name.lower()}" if class_name else ""
            path_params = [p['name'] for p in parameters if p['in'] == 'path']
            
            if path_params:
                path_suffix = '/' + '/'.join([f"{{{p}}}" for p in path_params])
                return f"{base}/{name}{path_suffix}"
            else:
                return f"{base}/{name}"
        
        # 2. Module: Include relative module path (remove library name)
        elif self.path_style == 'module':
            if module_name:
                # Remove library name prefix: pdfkit.config.Configuration -> config/configuration
                module_parts = module_name.replace(f"{self.library_name}.", "").split('.')
                # Filter out empty strings and library name itself
                module_parts = [p for p in module_parts if p and p != self.library_name]
                module_path = '/'.join([p.lower() for p in module_parts]) if module_parts else ""
                
                base = f"/{module_path}" if module_path else ""
                if class_name:
                    base += f"/{class_name.lower()}"
            else:
                base = f"/{class_name.lower()}" if class_name else ""
            
            path_params = [p['name'] for p in parameters if p['in'] == 'path']
            
            if path_params:
                path_suffix = '/' + '/'.join([f"{{{p}}}" for p in path_params])
                return f"{base}/{name}{path_suffix}"
            else:
                return f"{base}/{name}"
        
        # 3. Full: Full module path
        elif self.path_style == 'full':
            if module_name:
                # Full path: pdfkit.config.Configuration -> pdfkit/config/configuration
                module_parts = module_name.split('.')
                module_path = '/'.join([p.lower() for p in module_parts])
                
                base = f"/{module_path}"
                if class_name:
                    base += f"/{class_name.lower()}"
            else:
                base = f"/{self.library_name.lower()}"
                if class_name:
                    base += f"/{class_name.lower()}"
            
            path_params = [p['name'] for p in parameters if p['in'] == 'path']
            
            if path_params:
                path_suffix = '/' + '/'.join([f"{{{p}}}" for p in path_params])
                return f"{base}/{name}{path_suffix}"
            else:
                return f"{base}/{name}"
        
        # 4. Auto: Simple path, upgrade after detecting conflict (handled in _generate_openapi)
        else:  # 'auto'
            base = f"/{class_name.lower()}" if class_name else ""
            path_params = [p['name'] for p in parameters if p['in'] == 'path']
            
            if path_params:
                path_suffix = '/' + '/'.join([f"{{{p}}}" for p in path_params])
                return f"{base}/{name}{path_suffix}"
            else:
                return f"{base}/{name}"
    
    def _generate_openapi(self) -> Dict[str, Any]:
        """Generate OpenAPI specification"""
        paths = {}
        conflicts = []
        
        # If auto mode, need to detect conflicts and regenerate paths
        if self.path_style == 'auto':
            # First pass: Collect all path and method combinations
            path_method_funcs = {}  # (path, method) -> [FunctionInfo]
            
            for func in self.functions:
                key = (func.path, func.http_method)
                if key not in path_method_funcs:
                    path_method_funcs[key] = []
                path_method_funcs[key].append(func)
            
            self._resolve_path_conflicts(path_method_funcs, conflicts)
        
        # Build final paths
        for func in self.functions:
            operation = self._build_operation(func)
            
            if func.path not in paths:
                paths[func.path] = {}
            
            
            paths[func.path][func.http_method] = operation
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": f"{self.library_name} API",
                "version": "1.0.0",
                "description": self._generate_description()
            },
            "servers": [{"url": "http://localhost:8000"}],
            "paths": paths
        }

    def _resolve_path_conflicts(self, path_method_funcs: Dict[Tuple[str, str], List[FunctionInfo]], conflicts: List[Dict[str, str]]) -> None:
        """Batch resolve path conflicts by escalating style from module to full."""
        original_style = self.path_style

        for (old_path, method), funcs in path_method_funcs.items():
            if len(funcs) <= 1:
                continue

            self.path_style = 'module'
            module_paths = {
                func.qualname: self._generate_path(func.name, func.parameters, func.class_name, func.module)
                for func in funcs
            }

            if len(set(module_paths.values())) == len(funcs):
                chosen_paths = module_paths
            else:
                self.path_style = 'full'
                chosen_paths = {
                    func.qualname: self._generate_path(func.name, func.parameters, func.class_name, func.module)
                    for func in funcs
                }

            for func in funcs:
                new_path = chosen_paths[func.qualname]
                conflicts.append({
                    'old_path': old_path,
                    'new_path': new_path,
                    'method': method,
                    'qualname': func.qualname,
                })
                func.path = new_path

        self.path_style = original_style
    
    def _generate_description(self) -> str:
        """Generate API description, including quality statistics"""
        desc = f"Auto-generated API for {self.library_name}"
        
        # Add quality statistics
        if self.quality_stats and self.enable_quality_filter:
            stats = self.quality_stats
            desc += f"""

## Quality Statistics

- **Total Functions Scanned**: {stats['total_functions_found']}
- **Functions Exposed**: {stats['functions_after_filtering']}
- **Average Quality Score**: {stats['avg_score']:.1f}/100
- **Quality Mode**: {self.quality_mode}
- **Min Score Threshold**: {self.min_quality_score}

### Score Distribution
"""
            for score_range, count in stats['score_distribution'].items():
                desc += f"\n- {score_range}: {count} functions"
            
            if stats['top_10_functions']:
                desc += "\n\n### Top Functions\n"
                for i, func in enumerate(stats['top_10_functions'], 1):
                    desc += f"\n{i}. {func['name']} (score: {func['score']})"
        
        return desc
    
    def _build_operation(self, func: FunctionInfo) -> Dict[str, Any]:
        """Build operation"""
        operation = {
            "summary": func.name.replace('_', ' ').title(),
            "operationId": func.qualname.replace('.', '_'),
            "tags": [func.module.split('.')[0]],
            # New: Save function meta info
            "x-function": {
                "module": func.module,
                "class": func.class_name,
                "name": func.target_name or func.name,
                "is_async": func.is_async,
                "returns_object": func.returns_object,
                "object_methods": func.object_methods if func.returns_object else None,
                "is_constructor": func.is_constructor,
            }
        }
        
        if func.doc:
            lines = func.doc.strip().split('\n')
            operation["summary"] = lines[0][:100]
            if len(func.doc) > 100:
                operation["description"] = func.doc
        
        path_params = [p for p in func.parameters if p['in'] == 'path']
        query_params = [p for p in func.parameters if p['in'] == 'query']
        
        # For POST/PUT/PATCH, query parameters should be in requestBody, not in parameters
        if func.http_method in ('post', 'put', 'patch'):
            # Only add path parameters to parameters
            if path_params:
                operation["parameters"] = []
                for param in path_params:
                    p = {
                        "name": param["name"],
                        "in": param["in"],
                        "required": param.get("required", False),
                        "schema": param["schema"]
                    }
                    if "default" in param and param["default"] is not None:
                        p["schema"]["default"] = param["default"]
                    operation["parameters"].append(p)
            
            # query parameters put in requestBody
            if query_params:
                properties = {}
                required = []
                
                for param in query_params:
                    properties[param["name"]] = param["schema"]
                    if param.get("required"):
                        required.append(param["name"])
                
                operation["requestBody"] = {
                    "required": bool(required),
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": properties,
                                "required": required
                            }
                        }
                    }
                }
        else:
            # For GET/DELETE, all parameters are in parameters
            if path_params or query_params:
                operation["parameters"] = []
                for param in path_params + query_params:
                    p = {
                        "name": param["name"],
                        "in": param["in"],
                        "required": param.get("required", False),
                        "schema": param["schema"]
                    }
                    if "default" in param and param["default"] is not None:
                        p["schema"]["default"] = param["default"]
                    operation["parameters"].append(p)
        
        # Response schema - if returns object, use special format
        if func.returns_object:
            response_schema = {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "object_id": {"type": "string", "description": "Object ID, used for subsequent calls"},
                    "object_type": {"type": "string", "description": "Object type"},
                    "available_methods": {
                        "type": "array",
                        "description": "List of available methods",
                        "items": {"type": "object"}
                    }
                }
            }
        else:
            response_schema = TypeParser.parse_annotation(func.return_type) if func.return_type else {}
        
        operation["responses"] = {
            "200": {
                "description": "Success",
                "content": {"application/json": {"schema": response_schema}}
            },
            "400": {"description": "Bad Request"},
            "500": {"description": "Internal Server Error"}
        }
        
        return operation


def _format_python_value(value: Any, indent: int = 0) -> str:
    """Format Python value as code string"""
    if value is None:
        return "None"
    elif isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return repr(value)
    elif isinstance(value, list):
        if not value:
            return "[]"
        items = ",\n".join([" " * (indent + 2) + _format_python_value(v, indent + 2) for v in value])
        return f"[\n{items}\n{' ' * indent}]"
    elif isinstance(value, dict):
        if not value:
            return "{}"
        indent_str = " " * (indent + 2)
        items = []
        for k, v in value.items():
            key_str = repr(k) if isinstance(k, str) else str(k)
            val_str = _format_python_value(v, indent + 2)
            items.append(f'{indent_str}{key_str}: {val_str}')
        return "{\n" + ",\n".join(items) + f"\n{' ' * indent}}}"
    else:
        return repr(value)





def _infer_python_type(schema: Dict) -> str:
    """Infer Python type"""
    type_map = {
        "integer": "int",
        "number": "float",
        "string": "str",
        "boolean": "bool",
        "array": "List",
        "object": "Dict"
    }
    return type_map.get(schema.get("type", "string"), "Any")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Python Library to OpenAPI Converter - Universal Intelligent Version')
    parser.add_argument('library', help='Library name')
    parser.add_argument('-o', '--output', default=None, help='Output file (default: <library_name>_openapi.json)')
    
    # Basic arguments
    parser.add_argument('--depth', type=int, default=2, help='Module scan depth')
    parser.add_argument('--skip-non-serializable', action='store_true', 
                       help='Skip non-serializable functions (default not skip, use state management)')
    parser.add_argument('--no-state-management', action='store_true',
                       help='Disable state management (not recommended)')
    parser.add_argument('--no-warnings', action='store_true', 
                       help='Do not show warnings')
    
    # Path generation strategy
    parser.add_argument('--path-style', 
                       choices=['simple', 'module', 'full', 'auto'],
                       default='auto',
                       help='Path generation strategy')
    
    # Quality control arguments (New)
    parser.add_argument('--quality-mode', 
                       choices=['strict', 'balanced', 'permissive'],
                       default='balanced',
                       help='Quality control mode: strict(<20 APIs), balanced(<50 APIs), permissive(<100 APIs)')
    
    parser.add_argument('--min-score', type=float, default=None,
                       help='Minimum quality score (0-100, default: strict=85, balanced=70, permissive=60)')
    
    parser.add_argument('--max-functions', type=int, default=None,
                       help='Maximum number of APIs (default: strict=20, balanced=50, permissive=100)')
    
    parser.add_argument('--no-quality-filter', action='store_true',
                       help='Disable quality filtering')
    
    parser.add_argument('--no-dedup', action='store_true',
                       help='Disable deduplication')
    
    parser.add_argument('--no-input-complexity-filter', action='store_true',
                       help='Disable input complexity filter (allow functions accepting complex objects)')

    parser.add_argument('--stats', action='store_true', help='Show detailed statistics')
    
    args = parser.parse_args()
    
    # If output file not specified, use library name as prefix
    if args.output is None:
        args.output = f"{args.library}_openapi.json"
    
    # Build arguments
    analyzer_kwargs = {
        'max_depth': args.depth,
        'skip_non_serializable': args.skip_non_serializable,
        'warn_on_skip': not args.no_warnings,
        'enable_state_management': not args.no_state_management,
        'path_style': args.path_style,
        'enable_quality_filter': not args.no_quality_filter,
        'enable_deduplication': not args.no_dedup,
        'quality_mode': args.quality_mode,
        'enable_input_complexity_filter': not args.no_input_complexity_filter,
    }
    
    if args.min_score is not None:
        analyzer_kwargs['min_quality_score'] = args.min_score
    if args.max_functions is not None:
        analyzer_kwargs['max_functions'] = args.max_functions
    
    print(f"[INFO] Analyzing library: {args.library}")
    print(f"       Quality mode: {args.quality_mode}")
    
    analyzer = APIAnalyzer(args.library, **analyzer_kwargs)
    spec = analyzer.analyze()
    
    if "error" in spec:
        print(f"[ERROR] Analysis failed: {spec['error']}")
        sys.exit(1)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] OpenAPI specification generated: {args.output}")
    
    # Show statistics
    if args.stats and analyzer.quality_stats:
        print("\n[STATS] Quality Statistics:")
        stats = analyzer.quality_stats
        print(f"   Modules Scanned: {stats['total_modules_scanned']}")
        print(f"   Functions Found: {stats['total_functions_found']}")
        print(f"   APIs Exposed: {stats['functions_after_filtering']}")
        print(f"   Average Score: {stats['avg_score']:.1f}/100")
        print(f"\n   Score Distribution:")
        for score_range, count in stats['score_distribution'].items():
            print(f"     {score_range}: {count} functions")
        
        if stats['top_10_functions']:
            print(f"\n   Top 10 APIs:")
            for i, func in enumerate(stats['top_10_functions'], 1):
                print(f"     {i}. {func['name']} (Score: {func['score']})")


if __name__ == "__main__":
    main()
