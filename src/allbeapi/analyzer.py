#!/usr/bin/env python3
"""
Python库到生产级OpenAPI服务转换器 - 通用智能版
支持质量评分、智能过滤和去重,无特定库硬编码
"""

import ast
import inspect
import importlib
import pkgutil
import re
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Tuple, get_type_hints, get_origin, get_args
from types import ModuleType
from dataclasses import dataclass, asdict, is_dataclass, fields
from collections import defaultdict


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    module: str
    class_name: Optional[str]  # 新增：明确记录类名
    qualname: str
    signature: str
    doc: Optional[str]
    parameters: List[Dict]
    return_type: Optional[str]
    is_async: bool
    http_method: str
    path: str
    returns_object: bool = False  # 是否返回复杂对象（需要状态管理）
    object_methods: List[Dict] = None  # 如果返回对象，其可用方法列表
    # 新增：记录原始注解信息用于质量评估
    raw_param_annotations: List[Any] = None  # 参数的原始注解
    raw_return_annotation: Any = None  # 返回值的原始注解


class QualityMetrics:
    """函数质量评估指标 - 通用评估机制"""
    
    @staticmethod
    def has_good_documentation(func_info: FunctionInfo) -> Tuple[bool, float]:
        """文档质量评估"""
        if not func_info.doc:
            return False, 0.0
        
        doc_len = len(func_info.doc.strip())
        
        # 评分标准
        if doc_len > 200:  # 详细文档
            return True, 1.0
        elif doc_len > 100:  # 中等文档
            return True, 0.7
        elif doc_len > 30:  # 简短文档
            return True, 0.4
        else:
            return False, 0.1
    
    @staticmethod
    def has_reasonable_params(func_info: FunctionInfo) -> Tuple[bool, float]:
        """参数合理性评估"""
        num_params = len(func_info.parameters)
        
        # 理想参数数量: 1-5个
        if 1 <= num_params <= 5:
            return True, 1.0
        elif num_params == 0:  # 无参数函数可能是工厂函数
            return True, 0.8
        elif 6 <= num_params <= 8:
            return True, 0.6
        elif num_params > 10:  # 过多参数通常是内部函数
            return False, 0.2
        else:
            return True, 0.5
    
    @staticmethod
    def has_type_annotations(func_info: FunctionInfo) -> Tuple[bool, float]:
        """类型注解完整性评估 - 改进版"""
        # 使用原始注解信息进行判断
        if hasattr(func_info, 'raw_param_annotations') and func_info.raw_param_annotations:
            total_params = len(func_info.raw_param_annotations)
            if total_params == 0:
                # 无参数，只看返回值
                has_return = (hasattr(func_info, 'raw_return_annotation') and 
                             func_info.raw_return_annotation is not None and 
                             func_info.raw_return_annotation != inspect.Signature.empty)
                return has_return, 1.0 if has_return else 0.5
            
            # 计算真实的注解覆盖率
            annotated_params = sum(
                1 for ann in func_info.raw_param_annotations 
                if ann is not None and ann != inspect.Parameter.empty
            )
            
            param_coverage = annotated_params / total_params
            has_return = (hasattr(func_info, 'raw_return_annotation') and 
                         func_info.raw_return_annotation is not None and 
                         func_info.raw_return_annotation != inspect.Signature.empty)
            
            # 综合评分 - 放宽要求
            if param_coverage >= 0.8 and has_return:
                return True, 1.0
            elif param_coverage >= 0.5 and has_return:
                return True, 0.8
            elif param_coverage >= 0.5 or has_return:
                return True, 0.6
            else:
                # 即使没有注解，也给予基础分（避免完全0分）
                return False, 0.4
        
        # 降级：使用旧的schema判断方式（向后兼容）
        total_params = len(func_info.parameters)
        if total_params == 0:
            has_return = func_info.return_type is not None
            return has_return, 1.0 if has_return else 0.5
        
        # 计算注解覆盖率
        annotated_params = sum(
            1 for p in func_info.parameters 
            if p.get('schema', {}).get('type') != 'string'  # string是默认类型
        )
        
        param_coverage = annotated_params / total_params
        has_return = func_info.return_type is not None
        
        # 综合评分 - 放宽要求
        if param_coverage >= 0.8 and has_return:
            return True, 1.0
        elif param_coverage >= 0.5 or has_return:
            return True, 0.6
        else:
            # 即使没有注解，也给予基础分
            return False, 0.4
    
    @staticmethod
    def is_public_api(func_info: FunctionInfo) -> Tuple[bool, float]:
        """判断是否是公开API - 通用机制（改进版）"""
        # 1. 名称不以下划线开头
        if func_info.name.startswith('_'):
            return False, 0.0
        
        # 2. 检查是否在模块的 __all__ 中
        try:
            module = sys.modules.get(func_info.module)
            if module and hasattr(module, '__all__'):
                if func_info.name in module.__all__:
                    return True, 1.0
                else:
                    # 不在__all__中，但如果是顶层模块，仍给较高分
                    # 顶层模块判断：模块名只有一个点或就是库名本身
                    module_parts = func_info.module.split('.')
                    is_top_level = len(module_parts) <= 2  # 如 pdfkit 或 pdfkit.api
                    
                    if is_top_level and not func_info.class_name:
                        # 顶层模块的直接函数，虽然不在__all__，也给较高分
                        return True, 0.8
                    else:
                        # 不在__all__中，降低分数
                        return True, 0.5
            else:
                # 没有__all__属性，根据模块层级判断
                module_parts = func_info.module.split('.')
                is_top_level = len(module_parts) <= 2
                
                if is_top_level and not func_info.class_name:
                    # 顶层模块的直接函数
                    return True, 0.9
                else:
                    return True, 0.7
        except:
            pass
        
        # 3. 检查模块路径是否包含internal/_等
        if re.search(r'(internal|_private|compat|testing)', func_info.module):
            return False, 0.2
        
        return True, 0.7
    
    @staticmethod
    def naming_quality(func_info: FunctionInfo) -> Tuple[bool, float]:
        """命名规范性评估"""
        name = func_info.name
        
        # 好的命名特征
        good_patterns = [
            r'^[a-z][a-z0-9_]*$',  # 小写+下划线
            r'^[A-Z][a-zA-Z0-9]*$',  # 大驼峰(类名)
        ]
        
        # 不好的命名特征
        bad_patterns = [
            r'.*\d+$',  # 以数字结尾 (如 func1, test2)
            r'^(test|demo|example)_.*',  # 测试/示例函数
            r'.*_(internal|private|impl)$',  # 内部实现
        ]
        
        # 检查不好的模式
        for pattern in bad_patterns:
            if re.match(pattern, name, re.IGNORECASE):
                return False, 0.2
        
        # 检查好的模式
        for pattern in good_patterns:
            if re.match(pattern, name):
                return True, 1.0
        
        return True, 0.6

    @staticmethod
    def hierarchy_quality(func_info: FunctionInfo) -> Tuple[bool, float]:
        """层级质量评估 - 通用版"""
        module_parts = func_info.module.split('.')
        
        # 1. 私有模块检测 (通用约定)
        # 任何以 _ 开头的路径组件通常表示私有
        # tests/testing 也是通用的非生产代码目录
        for part in module_parts:
            if part.startswith('_') or part.lower() in ('tests', 'testing', 'test'):
                return False, 0.0
        
        # 2. 深度评分 (相对深度)
        # 越浅越好，但不再硬编码 core/common 等词汇
        # 假设库名为 root (depth 1)
        # root.api (depth 2) -> 1.0
        # root.sub.detail (depth 3) -> 0.8
        # root.sub.detail.impl (depth 4) -> 0.6
        
        # 基础分
        score = 1.0
        
        # 深度惩罚 (从第3层开始，每层扣0.2)
        # pandas (1) -> 1.0
        # pandas.io (2) -> 1.0
        # pandas.core.frame (3) -> 0.8
        # pandas.core.arrays.categorical (4) -> 0.6
        if len(module_parts) > 2:
            penalty = (len(module_parts) - 2) * 0.2
            score = max(0.4, 1.0 - penalty)
            
        return True, score


class TypeParser:
    """类型注解解析器"""
    
    @staticmethod
    def parse_annotation(annotation: Any) -> Dict[str, Any]:
        """将Python类型注解转换为OpenAPI Schema"""
        if annotation is None or annotation == inspect.Parameter.empty:
            return {"type": "string"}
        
        if isinstance(annotation, str):
            return TypeParser._parse_string_annotation(annotation)
        
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
            return TypeParser._parse_dataclass(annotation)
        
        if origin in (list, List):
            items = TypeParser.parse_annotation(args[0]) if args else {"type": "string"}
            return {"type": "array", "items": items}
        
        if origin in (dict, Dict):
            additional = TypeParser.parse_annotation(args[1]) if len(args) >= 2 else {}
            return {"type": "object", "additionalProperties": additional or True}
        
        if origin in (tuple, Tuple):
            return {"type": "array", "items": {"type": "string"}}
        
        if origin in (set, Set):
            items = TypeParser.parse_annotation(args[0]) if args else {"type": "string"}
            return {"type": "array", "uniqueItems": True, "items": items}
        
        if origin is Union:
            if len(args) == 2 and type(None) in args:
                non_none = args[0] if args[1] is type(None) else args[1]
                schema = TypeParser.parse_annotation(non_none)
                schema["nullable"] = True
                return schema
            return {"oneOf": [TypeParser.parse_annotation(arg) for arg in args if arg is not type(None)]}
        
        try:
            from typing import Literal
            if origin is Literal:
                return {"type": "string", "enum": list(args)}
        except ImportError:
            pass
        
        if annotation is Any:
            return {}
        
        return {"type": "object"}
    
    @staticmethod
    def _parse_dataclass(dc: type) -> Dict[str, Any]:
        """解析dataclass"""
        properties = {}
        required = []
        
        try:
            for field in fields(dc):
                properties[field.name] = TypeParser.parse_annotation(field.type)
                # 修复：使用正确的MISSING检查
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
        """解析字符串注解"""
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
        
        return {"type": "object"}


class APIAnalyzer:
    """API分析器 - 通用智能版"""
    
    
    # 可序列化的基本类型
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
                 # 新增质量控制参数
                 enable_quality_filter: bool = True,
                 min_quality_score: float = 60.0,
                 enable_deduplication: bool = True,
                 quality_mode: str = 'balanced'):
        self.library_name = library_name
        self.max_depth = max_depth
        self.skip_non_serializable = skip_non_serializable
        self.warn_on_skip = warn_on_skip
        self.enable_state_management = enable_state_management
        self.path_style = path_style
        self.max_functions = max_functions
        
        # 质量控制参数
        self.enable_quality_filter = enable_quality_filter
        self.min_quality_score = min_quality_score
        self.enable_deduplication = enable_deduplication
        self.quality_mode = quality_mode
        
        # 应用质量模式预设
        self._apply_quality_mode()
        
        # 数据存储
        self.functions: List[FunctionInfo] = []
        self.analyzed: Set[str] = set()
        self.skipped_functions: List[Dict[str, str]] = []
        self.object_returning_functions: List[FunctionInfo] = []
        self.function_scores: Dict[str, float] = {}
        self.quality_stats: Dict[str, Any] = {}
    
    def _apply_quality_mode(self):
        """应用质量模式预设"""
        modes = {
            'strict': {
                'min_quality_score': 95,
                'max_functions': 50,
            },
            'balanced': {
                'min_quality_score': 90,
                'max_functions': 3000,
            },
            'permissive': {
                'min_quality_score': 60,
                'max_functions': 20000,
            }
        }
        
        if self.quality_mode in modes:
            mode_config = modes[self.quality_mode]
            # 只在未明确设置时应用预设值
            if self.min_quality_score == 60.0:  # 默认值
                self.min_quality_score = mode_config['min_quality_score']
            if self.max_functions is None:
                self.max_functions = mode_config['max_functions']
        
    def analyze(self) -> Dict[str, Any]:
        """分析库 - 增强版带质量过滤"""
        try:
            root = importlib.import_module(self.library_name)
        except ImportError as e:
            return {"error": f"Cannot import: {e}"}
        
        # 1. 扫描模块
        self._scan_module(root)
        
        # 2. 如果启用质量过滤，进行后处理
        if self.enable_quality_filter:
            self._apply_quality_filtering()
        
        # 3. 生成OpenAPI规范
        return self._generate_openapi()
    
    def _apply_quality_filtering(self):
        """应用质量过滤和去重"""
        # 1. 计算质量分数
        scored_functions = []
        for func in self.functions:
            score = self.calculate_function_score(func)
            self.function_scores[func.qualname] = score
            
            if score >= self.min_quality_score:
                scored_functions.append((func, score))
        
        # 2. 去重
        if self.enable_deduplication and len(scored_functions) > 0:
            funcs = [f for f, s in scored_functions]
            deduped = self._deduplicate_similar_functions(funcs)
            scored_functions = [(f, s) for f, s in scored_functions if f in deduped]
        
        # 3. 按分数排序并限制数量
        scored_functions.sort(key=lambda x: x[1], reverse=True)
        if self.max_functions and len(scored_functions) > self.max_functions:
            scored_functions = scored_functions[:self.max_functions]
        
        # 4. 更新函数列表
        self.functions = [f for f, s in scored_functions]
        
        # 5. 记录统计信息
        self._collect_quality_stats(scored_functions)
    
    def calculate_function_score(self, func_info: FunctionInfo) -> float:
        """计算函数质量分数 (0-100)"""
        score = 0.0
        weights = {
            'documentation': 25,
            'type_annotations': 20,
            'public_api': 20,
            'naming': 10,
            'hierarchy': 25,
        }
        
        # 1. 文档质量
        _, doc_score = QualityMetrics.has_good_documentation(func_info)
        score += weights['documentation'] * doc_score
        
        # 2. 类型注解
        _, type_score = QualityMetrics.has_type_annotations(func_info)
        score += weights['type_annotations'] * type_score
        
        # 3. 公开API
        _, public_score = QualityMetrics.is_public_api(func_info)
        score += weights['public_api'] * public_score
        
        # 4. 命名规范
        _, name_score = QualityMetrics.naming_quality(func_info)
        score += weights['naming'] * name_score
        
        # 5. 层级质量
        _, hierarchy_score = QualityMetrics.hierarchy_quality(func_info)
        score += weights['hierarchy'] * hierarchy_score
        
        # 额外加分项
        # - 返回简单类型而非对象 (+5)
        if not func_info.returns_object:
            score += 5
        
        return min(score, 100.0)
    
    def _normalize_function_purpose(self, func_name: str) -> str:
        """提取函数的核心语义目的"""
        # 移除常见前缀
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
        """去除功能相似的冗余函数"""
        # 按核心目的分组
        groups = defaultdict(list)
        for func in functions:
            key = self._normalize_function_purpose(func.name)
            groups[key].append(func)
        
        # 每组只保留最优的
        result = []
        for group_funcs in groups.values():
            if len(group_funcs) == 1:
                result.append(group_funcs[0])
            else:
                # 选择最优函数
                best = max(group_funcs, key=lambda f: (
                    # 1. 质量分数
                    self.function_scores.get(f.qualname, 0),
                    # 2. 文档长度
                    len(f.doc or ''),
                    # 3. 参数数量越少越好
                    -len(f.parameters),
                    # 4. 在__all__中
                    f.name in getattr(sys.modules.get(f.module), '__all__', []),
                    # 5. 命名长度(通常短的更通用)
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
        
        self.analyzed.add(module.__name__)
        
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
                members = inspect.getmembers(module)

            for name, obj in members:
                if inspect.isfunction(obj):
                    if self._should_include(name, obj, module, is_method=False):
                        info = self._extract_function(name, obj, module)
                        if info:
                            # 检查是否返回复杂对象
                            self._analyze_return_type(info, obj)
                            
                            # 检查是否适合作为 API
                            if self._is_suitable_for_api(info, obj):
                                self.functions.append(info)
                                if info.returns_object:
                                    self.object_returning_functions.append(info)
                            elif self.skip_non_serializable:
                                # 记录跳过原因
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
                for _, subname, _ in pkgutil.iter_modules(module.__path__, f"{module.__name__}."):
                    # 过滤私有模块和测试模块 (通用规则)
                    last_part = subname.split('.')[-1]
                    if last_part.startswith('_') or last_part.lower() in ('tests', 'testing', 'test'):
                        continue
                        
                    try:
                        sub = importlib.import_module(subname)
                        self._scan_module(sub, depth + 1)
                    except:
                        pass
            except:
                pass
    
    def _scan_class(self, cls: type, module: ModuleType):
        """扫描类"""
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if self._should_include(name, method, module, is_method=True):
                info = self._extract_function(name, method, module, class_name=cls.__name__)
                if info:
                    # 新逻辑：分析返回类型
                    self._analyze_return_type(info, method)
                    
                    # 检查是否适合作为 API
                    if self._is_suitable_for_api(info, method):
                        self.functions.append(info)
                        if info.returns_object:
                            self.object_returning_functions.append(info)
                    elif self.skip_non_serializable:
                        reason = self._get_unsuitability_reason(info, method)
                        self.skipped_functions.append({
                            'qualname': info.qualname,
                            'reason': reason
                        })
    
    def _should_include(self, name: str, obj: Any, module: ModuleType = None, is_method: bool = False) -> bool:
        """判断是否包含 - 通用智能版"""
        if not callable(obj) or name.startswith('_'):
            return False
        
        # 基础检查：必须属于本库
        if hasattr(obj, '__module__') and obj.__module__:
            if not obj.__module__.startswith(self.library_name):
                return False
            
        if is_method:
            return True

        # 模块级函数的关键过滤逻辑
        if module:
            # 1. 优先尊崇 __all__
            # 如果模块定义了 __all__，那么只有在其中的才是公开 API
            if hasattr(module, '__all__'):
                return name in module.__all__
                
            # 2. 如果没有 __all__，采用“定义地原则”
            # 只有定义在当前模块的函数才被视为该模块的 API
            # 这能有效过滤掉 import 进来的工具函数
            if obj.__module__ == module.__name__:
                return True
                
            # 3. 处理 __init__.py 的重导出 (Facade Pattern)
            # 如果当前模块是包的初始化文件，它通常会从子模块导入功能并暴露
            # 判断依据：模块名是包名，或者文件路径是 __init__.py
            is_init = False
            if hasattr(module, '__file__') and module.__file__:
                is_init = module.__file__.endswith('__init__.py')
            
            if is_init:
                # 允许从子模块导入
                # 例如：在 pandas/__init__.py 中导入 pandas.core.frame.DataFrame
                if obj.__module__.startswith(module.__name__):
                    return True
            
            # 4. 其他情况（普通模块中的导入），视为依赖，不作为 API 暴露
            # 例如：在 pandas/core/frame.py 中导入了 pandas/core/common.py 的函数
            # 除非它在 __all__ 中（上面已处理），否则不应该被视为 frame.py 的 API
            return False

        return True
    
    def _infer_return_type_from_ast(self, func_obj: Any) -> Optional[str]:
        """通过AST分析推断返回类型(静态分析，无副作用)"""
        try:
            source = inspect.getsource(func_obj)
            # 处理缩进问题
            source = inspect.cleandoc(source)
            tree = ast.parse(source)
            
            # 查找函数定义
            func_def = None
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_def = node
                    break
            
            if not func_def:
                return None
                
            # 查找返回语句
            returns = []
            for node in ast.walk(func_def):
                if isinstance(node, ast.Return):
                    if node.value is None:
                        returns.append("None")
                    elif isinstance(node.value, ast.Constant):
                        returns.append(type(node.value.value).__name__)
                    elif isinstance(node.value, ast.Call):
                        # 尝试获取被调用函数/类的名称
                        if isinstance(node.value.func, ast.Name):
                            returns.append(node.value.func.id)
                        elif isinstance(node.value.func, ast.Attribute):
                            returns.append(node.value.func.attr)
            
            if not returns:
                return "None"
            
            # 如果所有返回类型相同
            if len(set(returns)) == 1:
                return returns[0]
            
            return "Union[" + ", ".join(set(returns)) + "]"
            
        except Exception:
            return None

    def _analyze_return_type(self, func_info: FunctionInfo, func_obj: Any):
        """分析函数返回类型，检测是否返回复杂对象"""
        if not self.enable_state_management:
            return
        
        # 1. 先检查类型注解
        if func_info.return_type is not None and func_info.return_type != inspect.Signature.empty:
            if not self._is_type_serializable(func_info.return_type):
                func_info.returns_object = True
                func_info.object_methods = self._extract_object_methods(func_info.return_type)
                return
        
        # 2. AST静态分析 (替代运行时检测)
        # 运行时检测在大型库(如pandas)中会导致严重的性能问题和副作用
        try:
            inferred_type = self._infer_return_type_from_ast(func_obj)
            if inferred_type:
                # 简单的启发式判断：如果返回的是看起来像类名的东西
                if inferred_type[0].isupper() and inferred_type not in ('None', 'True', 'False'):
                    # 检查是否是基本类型
                    if inferred_type not in ('int', 'float', 'str', 'bool', 'list', 'dict', 'set', 'tuple'):
                        func_info.returns_object = True
                        # 尝试获取该类型的定义（如果可能）
                        # 这里我们无法轻易获取到类对象，所以只标记为对象
                        return
        except:
            pass
    
    def _extract_object_methods(self, obj_type: Any) -> List[Dict]:
        """提取对象的可用方法"""
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
        
        return methods[:20]  # 限制数量
    
    def _is_type_serializable(self, annotation: Any) -> bool:
        """检查类型是否可序列化 - 通用机制"""
        if annotation is None or annotation == inspect.Parameter.empty:
            return True  # 无类型注解，假设可以
        
        # 基本类型
        if annotation in self.SERIALIZABLE_TYPES:
            return True
        
        # 字符串注解
        if isinstance(annotation, str):
            annotation_lower = annotation.lower()
            if annotation_lower in ('int', 'float', 'str', 'bool', 'bytes', 'none', 'any'):
                return True
            if annotation_lower.startswith(('list', 'dict', 'tuple', 'set', 'optional')):
                return True
            return False
        
        # typing 模块的类型
        origin = get_origin(annotation)
        args = get_args(annotation)
        
        # List, Dict, Tuple, Set, Optional 等
        if origin in (list, dict, tuple, set, List, Dict, Tuple, Set):
            # 递归检查内部类型
            if args:
                return all(self._is_type_serializable(arg) for arg in args)
            return True
        
        # Union 和 Optional
        if origin is Union:
            return all(self._is_type_serializable(arg) for arg in args)
        
        # Any
        if annotation is Any:
            return True
        
        # dataclass 可以序列化
        if is_dataclass(annotation):
            return True
        
        # 检查是否是 Pydantic BaseModel
        try:
            from pydantic import BaseModel
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                return True
        except ImportError:
            pass
        
        # 其他自定义类型 - 通过尝试序列化来判断
        # 对于用户自定义类，如果有__dict__属性通常可以序列化
        if isinstance(annotation, type):
            if hasattr(annotation, '__dict__'):
                # 尝试检查是否有简单的属性
                return True
        
        return False
    
    def _is_suitable_for_api(self, func_info: FunctionInfo, func_obj: Any) -> bool:
        """检查函数是否适合作为 API"""
        if not self.skip_non_serializable:
            return True
        
        # 1. 检查参数类型
        try:
            sig = inspect.signature(func_obj)
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                # 检查参数类型是否可序列化
                if not self._is_type_serializable(param.annotation):
                    return False
                
                # 检查默认值是否可序列化
                if param.default != inspect.Parameter.empty:
                    if not self._is_value_serializable(param.default):
                        return False
        except:
            pass
        
        # 2. 如果启用状态管理，返回对象的函数也接受
        if self.enable_state_management and func_info.returns_object:
            return True
        
        # 3. 检查返回类型注解
        if func_info.return_type is not None:
            if not self._is_type_serializable(func_info.return_type):
                # 如果没有启用状态管理，则拒绝
                if not self.enable_state_management:
                    return False
        
        # 4. 运行时检测已移除，改为基于配置的策略
        if func_info.return_type is None or func_info.return_type == inspect.Signature.empty:
            # 如果启用了状态管理，我们假设它是安全的（或者返回对象）
            if self.enable_state_management:
                return True
            else:
                # 如果没有状态管理，且无法确定返回类型，保守起见拒绝
                return False
        
        return True
    
    def _is_value_serializable(self, value: Any) -> bool:
        """检查值是否可 JSON 序列化"""
        if value is None:
            return True
        if isinstance(value, (int, float, str, bool)):
            return True
        if isinstance(value, (list, tuple, dict, set)):
            return True
        # 其他复杂对象认为不可序列化
        return False
    
    def _get_unsuitability_reason(self, func_info: FunctionInfo, func_obj: Any) -> str:
        """获取函数不适合作为 API 的原因"""
        reasons = []
        
        # 检查参数
        try:
            sig = inspect.signature(func_obj)
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                
                if not self._is_type_serializable(param.annotation):
                    param_type = self._get_type_name(param.annotation)
                    reasons.append(f"参数 '{param_name}' 类型不可序列化 ({param_type})")
        except:
            pass
        
        # 检查返回类型注解
        if func_info.return_type is not None:
            if not self._is_type_serializable(func_info.return_type):
                return_type = self._get_type_name(func_info.return_type)
                reasons.append(f"返回类型不可序列化 ({return_type})")
        
        # 检查运行时返回值
        if not reasons and (func_info.return_type is None or func_info.return_type == inspect.Signature.empty):
            if not self.enable_state_management:
                reasons.append("返回类型未知且未启用状态管理")
        
        return "; ".join(reasons) if reasons else "未知原因"
    
    def _get_type_name(self, annotation: Any) -> str:
        """获取类型的可读名称"""
        if annotation is None or annotation == inspect.Parameter.empty:
            return "未知"
        
        if isinstance(annotation, str):
            return annotation
        
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        
        return str(annotation)
    
    def _extract_function(self, name: str, obj: Any, module: ModuleType, 
                         class_name: Optional[str] = None) -> Optional[FunctionInfo]:
        """提取函数信息"""
        try:
            sig = inspect.signature(obj)
        except:
            return None
        
        parameters = []
        raw_param_annotations = []  # 记录原始注解
        
        for pname, param in sig.parameters.items():
            if pname in ('self', 'cls'):
                continue
            
            # 跳过 *args 和 **kwargs 类型的参数
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            
            # 记录原始注解
            raw_param_annotations.append(param.annotation)
            
            has_default = param.default != inspect.Parameter.empty
            default_value = None
            if has_default:
                default_value = self._serialize_default(param.default)
            
            param_info = {
                "name": pname,
                "required": not has_default,
                "schema": TypeParser.parse_annotation(param.annotation),
                "in": self._classify_param(pname, name)
            }
            
            if default_value is not None:
                param_info["default"] = default_value
            
            parameters.append(param_info)
        
        return_type = None
        raw_return_annotation = sig.return_annotation
        if sig.return_annotation != inspect.Signature.empty:
            return_type = sig.return_annotation
        
        http_method = self._infer_method(name)
        qualname = f"{module.__name__}.{class_name}.{name}" if class_name else f"{module.__name__}.{name}"
        
        # 🔥 传递模块名
        path = self._generate_path(name, parameters, class_name, module_name=module.__name__)
        
        return FunctionInfo(
            name=name,
            module=module.__name__,
            class_name=class_name,
            qualname=qualname,
            signature=f"{name}{sig}",
            doc=inspect.getdoc(obj),
            parameters=parameters,
            return_type=return_type,
            is_async=inspect.iscoroutinefunction(obj),
            http_method=http_method,
            path=path,
            raw_param_annotations=raw_param_annotations,
            raw_return_annotation=raw_return_annotation
        )
    
    def _serialize_default(self, value: Any) -> Any:
        """安全序列化默认值"""
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
        """分类参数"""
        if re.match(r'.*_?id$', param_name, re.IGNORECASE):
            return 'path'
        return 'query'
    
    def _infer_method(self, name: str) -> str:
        """推断HTTP方法"""
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
        """生成路径（支持多种策略）"""
        
        # 1. Simple: 只用类名和函数名（默认，可能冲突）
        if self.path_style == 'simple':
            base = f"/{class_name.lower()}" if class_name else ""
            path_params = [p['name'] for p in parameters if p['in'] == 'path']
            
            if path_params:
                path_suffix = '/' + '/'.join([f"{{{p}}}" for p in path_params])
                return f"{base}/{name}{path_suffix}"
            else:
                return f"{base}/{name}"
        
        # 2. Module: 包含相对模块路径（去掉库名）
        elif self.path_style == 'module':
            if module_name:
                # 移除库名前缀：pdfkit.config.Configuration -> config/configuration
                module_parts = module_name.replace(f"{self.library_name}.", "").split('.')
                # 过滤掉空字符串和库名本身
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
        
        # 3. Full: 完整模块路径
        elif self.path_style == 'full':
            if module_name:
                # 完整路径：pdfkit.config.Configuration -> pdfkit/config/configuration
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
        
        # 4. Auto: 简单路径，后续检测冲突后升级（在 _generate_openapi 中处理）
        else:  # 'auto'
            base = f"/{class_name.lower()}" if class_name else ""
            path_params = [p['name'] for p in parameters if p['in'] == 'path']
            
            if path_params:
                path_suffix = '/' + '/'.join([f"{{{p}}}" for p in path_params])
                return f"{base}/{name}{path_suffix}"
            else:
                return f"{base}/{name}"
    
    def _generate_openapi(self) -> Dict[str, Any]:
        """生成OpenAPI规范"""
        paths = {}
        conflicts = []
        
        # 如果是 auto 模式，需要检测冲突并重新生成路径
        if self.path_style == 'auto':
            # 第一遍：收集所有路径和方法的组合
            path_method_funcs = {}  # (path, method) -> [FunctionInfo]
            
            for func in self.functions:
                key = (func.path, func.http_method)
                if key not in path_method_funcs:
                    path_method_funcs[key] = []
                path_method_funcs[key].append(func)
            
            # 检测冲突并重新生成路径
            for (path, method), funcs in path_method_funcs.items():
                if len(funcs) > 1:
                    # 有冲突，尝试升级路径
                    for func in funcs:
                        # 先尝试 module 模式
                        old_style = self.path_style
                        self.path_style = 'module'
                        new_path = self._generate_path(func.name, func.parameters, func.class_name, func.module)
                        
                        # 检查新路径是否还冲突
                        still_conflict = False
                        for other_func in funcs:
                            if other_func is not func:
                                other_new_path = self._generate_path(other_func.name, other_func.parameters, 
                                                                     other_func.class_name, other_func.module)
                                if new_path == other_new_path:
                                    still_conflict = True
                                    break
                        
                        # 如果还冲突，升级为 full 模式
                        if still_conflict:
                            self.path_style = 'full'
                            new_path = self._generate_path(func.name, func.parameters, func.class_name, func.module)
                        
                        self.path_style = old_style
                        
                        # 记录冲突
                        conflicts.append({
                            'old_path': path,
                            'new_path': new_path,
                            'method': method,
                            'qualname': func.qualname
                        })
                        
                        # 更新路径
                        func.path = new_path
        
        # 构建最终的 paths
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
    
    def _generate_description(self) -> str:
        """生成API描述，包含质量统计"""
        desc = f"Auto-generated API for {self.library_name}"
        
        # 添加质量统计信息
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
        """构建操作"""
        operation = {
            "summary": func.name.replace('_', ' ').title(),
            "operationId": func.qualname.replace('.', '_'),
            "tags": [func.module.split('.')[0]],
            # 新增：保存函数元信息
            "x-function": {
                "module": func.module,
                "class": func.class_name,
                "name": func.name,
                "is_async": func.is_async,
                "returns_object": func.returns_object,
                "object_methods": func.object_methods if func.returns_object else None
            }
        }
        
        if func.doc:
            lines = func.doc.strip().split('\n')
            operation["summary"] = lines[0][:100]
            if len(func.doc) > 100:
                operation["description"] = func.doc
        
        path_params = [p for p in func.parameters if p['in'] == 'path']
        query_params = [p for p in func.parameters if p['in'] == 'query']
        
        # 对于 POST/PUT/PATCH，query 参数应该在 requestBody 中，不在 parameters 中
        if func.http_method in ('post', 'put', 'patch'):
            # 只添加 path 参数到 parameters
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
            
            # query 参数放在 requestBody 中
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
            # 对于 GET/DELETE，所有参数都在 parameters 中
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
        
        # 响应 schema - 如果返回对象，使用特殊格式
        if func.returns_object:
            response_schema = {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "object_id": {"type": "string", "description": "对象ID，用于后续调用"},
                    "object_type": {"type": "string", "description": "对象类型"},
                    "available_methods": {
                        "type": "array",
                        "description": "可用的方法列表",
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
    """将Python值格式化为代码字符串"""
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
    """推断Python类型"""
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
    
    parser = argparse.ArgumentParser(description='Python库到OpenAPI转换器 - 通用智能版')
    parser.add_argument('library', help='库名')
    parser.add_argument('-o', '--output', default=None, help='输出文件（默认：<库名>_openapi.json）')
    
    # 基础参数
    parser.add_argument('--depth', type=int, default=2, help='模块扫描深度')
    parser.add_argument('--skip-non-serializable', action='store_true', 
                       help='跳过不可序列化的函数（默认不跳过，使用状态管理）')
    parser.add_argument('--no-state-management', action='store_true',
                       help='禁用状态管理（不推荐）')
    parser.add_argument('--no-warnings', action='store_true', 
                       help='不显示警告')
    
    # 路径生成策略
    parser.add_argument('--path-style', 
                       choices=['simple', 'module', 'full', 'auto'],
                       default='auto',
                       help='路径生成策略')
    
    # 质量控制参数 (新增)
    parser.add_argument('--quality-mode', 
                       choices=['strict', 'balanced', 'permissive'],
                       default='balanced',
                       help='质量控制模式: strict(严格,<20个API), balanced(平衡,<50个), permissive(宽松,<100个)')
    
    parser.add_argument('--min-score', type=float, default=None,
                       help='最低质量分数 (0-100, 默认: strict=85, balanced=70, permissive=60)')
    
    parser.add_argument('--max-functions', type=int, default=None,
                       help='最大API数量 (默认: strict=20, balanced=50, permissive=100)')
    
    parser.add_argument('--no-quality-filter', action='store_true',
                       help='禁用质量过滤')
    
    parser.add_argument('--no-dedup', action='store_true',
                       help='禁用去重功能')
    
    parser.add_argument('--stats', action='store_true', help='显示详细统计信息')
    
    args = parser.parse_args()
    
    # 如果没有指定输出文件，使用库名作为前缀
    if args.output is None:
        args.output = f"{args.library}_openapi.json"
    
    # 构建参数
    analyzer_kwargs = {
        'max_depth': args.depth,
        'skip_non_serializable': args.skip_non_serializable,
        'warn_on_skip': not args.no_warnings,
        'enable_state_management': not args.no_state_management,
        'path_style': args.path_style,
        'enable_quality_filter': not args.no_quality_filter,
        'enable_deduplication': not args.no_dedup,
        'quality_mode': args.quality_mode,
    }
    
    if args.min_score is not None:
        analyzer_kwargs['min_quality_score'] = args.min_score
    if args.max_functions is not None:
        analyzer_kwargs['max_functions'] = args.max_functions
    
    print(f"[INFO] 分析库: {args.library}")
    print(f"       质量模式: {args.quality_mode}")
    
    analyzer = APIAnalyzer(args.library, **analyzer_kwargs)
    spec = analyzer.analyze()
    
    if "error" in spec:
        print(f"[ERROR] 分析失败: {spec['error']}")
        sys.exit(1)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] OpenAPI 规范已生成: {args.output}")
    
    # 显示统计信息
    if args.stats and analyzer.quality_stats:
        print("\n[STATS] 质量统计:")
        stats = analyzer.quality_stats
        print(f"   模块扫描数: {stats['total_modules_scanned']}")
        print(f"   发现函数数: {stats['total_functions_found']}")
        print(f"   暴露API数: {stats['functions_after_filtering']}")
        print(f"   平均分数: {stats['avg_score']:.1f}/100")
        print(f"\n   分数分布:")
        for score_range, count in stats['score_distribution'].items():
            print(f"     {score_range}: {count} 个函数")
        
        if stats['top_10_functions']:
            print(f"\n   Top 10 API:")
            for i, func in enumerate(stats['top_10_functions'], 1):
                print(f"     {i}. {func['name']} (分数: {func['score']})")


if __name__ == "__main__":
    main()