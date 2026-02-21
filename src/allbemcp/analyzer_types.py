#!/usr/bin/env python3

import inspect
import os
import re
import sys
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_args, get_origin

try:
    import docstring_parser
except ImportError:
    docstring_parser = None


@dataclass
class FunctionInfo:
    """Function Information"""
    name: str
    module: str
    class_name: Optional[str]
    qualname: str
    signature: str
    doc: Optional[str]
    parameters: List[Dict]
    return_type: Optional[str]
    is_async: bool
    http_method: str
    path: str
    returns_object: bool = False
    object_methods: List[Dict] = None
    raw_param_annotations: List[Any] = None
    raw_return_annotation: Any = None
    target_name: Optional[str] = None
    is_constructor: bool = False


class QualityMetrics:
    """Function Quality Assessment Metrics - Universal Assessment Mechanism"""

    _INTERNAL_PATTERN = re.compile(
        r'(^|\.)(_?tests?|testing|testdata|benchmarks?|examples?|demos?|experimental|internal|_internal|private|_private|compat|legacy|deprecated|cache)(\.|$)',
        re.IGNORECASE,
    )

    @staticmethod
    def has_good_documentation(func_info: FunctionInfo) -> Tuple[bool, float]:
        if not func_info.doc:
            if func_info.name in ('make', 'create', 'run', 'build', 'generate'):
                return True, 0.5
            if len(func_info.name) > 10 or '_' in func_info.name:
                return False, 0.2
            return False, 0.0

        doc_len = len(func_info.doc.strip())

        if docstring_parser:
            try:
                parsed = docstring_parser.parse(func_info.doc)
                has_desc = bool(parsed.short_description or parsed.long_description)
                has_params = len(parsed.params) > 0
                has_returns = bool(parsed.returns)

                if has_desc and (has_params or has_returns):
                    return True, 1.0
                if has_desc:
                    if func_info.name in ('make', 'create', 'run', 'build', 'generate'):
                        return True, 0.9
                    return True, 0.8
            except Exception:
                pass

        if doc_len > 200:
            return True, 1.0
        elif doc_len > 100:
            return True, 0.7
        elif doc_len > 30:
            return True, 0.4
        else:
            if func_info.name in ('make', 'create', 'run', 'build', 'generate'):
                return True, 0.6
            return False, 0.2

    @staticmethod
    def has_reasonable_params(func_info: FunctionInfo) -> Tuple[bool, float]:
        num_params = len(func_info.parameters)

        if 1 <= num_params <= 5:
            return True, 1.0
        elif num_params == 0:
            return True, 0.8
        elif 6 <= num_params <= 8:
            return True, 0.6
        elif num_params > 10:
            return False, 0.2
        else:
            return True, 0.5

    @staticmethod
    def has_type_annotations(func_info: FunctionInfo) -> Tuple[bool, float]:
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

        if total_params > 0 and param_coverage == 0.0 and not has_return_annotation and not doc_has_types:
            return False, 0.1

        return False, 0.4

    @staticmethod
    def is_public_api(func_info: FunctionInfo) -> Tuple[bool, float]:
        if QualityMetrics._INTERNAL_PATTERN.search(func_info.module):
            return False, 0.0

        if func_info.name.startswith('_'):
            return False, 0.0

        try:
            module = sys.modules.get(func_info.module)
            if module and hasattr(module, '__all__'):
                if func_info.name in module.__all__:
                    return True, 1.0
                else:
                    module_parts = func_info.module.split('.')
                    is_top_level = len(module_parts) <= 2

                    if is_top_level and not func_info.class_name:
                        return True, 0.8
                    else:
                        return True, 0.5
            else:
                module_parts = func_info.module.split('.')
                is_top_level = len(module_parts) <= 2

                if is_top_level and not func_info.class_name:
                    return True, 0.9
                else:
                    return True, 0.7
        except Exception:
            pass

        if re.search(r'(internal|_private|compat|testing)', func_info.module):
            return False, 0.2

        return True, 0.7

    @staticmethod
    def naming_quality(func_info: FunctionInfo) -> Tuple[bool, float]:
        name = func_info.name

        good_patterns = [
            r'^[a-z][a-z0-9_]*$',
            r'^[A-Z][a-zA-Z0-9]*$',
        ]

        bad_patterns = [
            r'.*\d+$',
            r'^(test|demo|example)_.*',
            r'^(bench|benchmark)_.*',
            r'.*_(internal|private|impl)$',
        ]

        for pattern in bad_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False, 0.2

        for pattern in good_patterns:
            if re.match(pattern, name):
                return True, 1.0

        return True, 0.6

    @staticmethod
    def hierarchy_quality(func_info: FunctionInfo) -> Tuple[bool, float]:
        module_parts = func_info.module.split('.')

        if any(part.lower() in ('utils', 'util', 'helpers', 'helper', 'cache') for part in module_parts[1:]):
            return True, 0.7

        for part in module_parts:
            if part.startswith('_') or part.lower() in ('tests', 'testing', 'test'):
                return False, 0.0

        score = 1.0
        if len(module_parts) > 2:
            penalty = (len(module_parts) - 2) * 0.2
            score = max(0.4, 1.0 - penalty)

        if len(module_parts) > 2 and not func_info.class_name:
            exposure_hits = 0
            for i in range(1, len(module_parts)):
                parent_name = '.'.join(module_parts[:i])
                parent_module = sys.modules.get(parent_name)
                if parent_module is None:
                    continue

                in_all = False
                if hasattr(parent_module, '__all__'):
                    try:
                        in_all = func_info.name in (getattr(parent_module, '__all__', []) or [])
                    except Exception:
                        in_all = False

                if in_all or hasattr(parent_module, func_info.name):
                    exposure_hits += 1

            if exposure_hits == 0:
                score *= 0.6
            elif exposure_hits == 1:
                score *= 0.8

        score = max(0.2, min(score, 1.0))

        return True, score

    @staticmethod
    def api_usability_score(func_info: FunctionInfo) -> Tuple[bool, float]:
        score = 1.0
        penalties = []

        name = func_info.name or ''
        lower_name = name.lower()
        if len(name) <= 2:
            penalties.append(0.5)

        overly_generic_names = {
            'run', 'do', 'go', 'call', 'exec', 'execute', 'process',
            'handle', 'apply', 'main', 'init', 'setup', 'configure',
        }
        if lower_name in overly_generic_names and not func_info.doc:
            penalties.append(0.3)

        unclear_param_names = {
            'x', 'y', 'z', 'a', 'b', 'c', 'v', 'k',
            'arg', 'args', 'val', 'obj', 'data', 'input',
        }
        if func_info.parameters:
            unclear_count = sum(
                1
                for p in func_info.parameters
                if (p.get('name', '') or '').lower() in unclear_param_names
            )
            if unclear_count > 0 and not func_info.doc:
                penalties.append(0.2 * unclear_count)

        num_params = len(func_info.parameters or [])
        if num_params > 8:
            penalties.append(0.4)
        elif num_params > 5:
            penalties.append(0.2)

        if func_info.is_constructor and not func_info.doc:
            penalties.append(0.3)

        total_penalty = min(sum(penalties), 0.9)
        score = max(0.1, score - total_penalty)
        return score >= 0.5, score


class TypeParser:
    """Type Annotation Parser"""

    @staticmethod
    def parse_annotation(annotation: Any, _depth: int = 0, _seen: Optional[Set[str]] = None) -> Dict[str, Any]:
        if _depth > 12:
            return {}

        if _seen is None:
            _seen = set()

        annotation_key = repr(annotation)
        if annotation_key in _seen:
            return {}

        _seen.add(annotation_key)

        if annotation is None or annotation == inspect.Parameter.empty:
            return {}

        if isinstance(annotation, str):
            return TypeParser._parse_string_annotation(annotation)

        try:
            if isinstance(annotation, type) and issubclass(annotation, os.PathLike):
                return {"type": "string"}
        except TypeError:
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

        return {}

    @staticmethod
    def _parse_dataclass(dc: type, _depth: int = 0, _seen: Optional[Set[str]] = None) -> Dict[str, Any]:
        properties = {}
        required = []

        try:
            from dataclasses import MISSING
            for field in fields(dc):
                properties[field.name] = TypeParser.parse_annotation(field.type, _depth=_depth + 1, _seen=_seen)
                if field.default is MISSING and field.default_factory is MISSING:
                    required.append(field.name)
        except Exception:
            pass

        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema

    @staticmethod
    def _parse_string_annotation(annotation: str) -> Dict[str, Any]:
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

        return {}
