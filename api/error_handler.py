# -*- coding: utf-8 -*-
"""API 错误处理装饰器

提供统一的异常捕获、日志记录和响应格式化逻辑
"""

import logging
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger("qwenpaw.humanthinking.api")


def _is_fallback_enabled() -> bool:
    """检查是否启用了降级模式"""
    try:
        from ..core.memory_manager import get_config
        config = get_config()
        return getattr(config, 'enable_api_fallback', False)
    except:
        return False


def _add_source_to_response(data: Any, source: str = "fallback") -> Any:
    """在响应中添加数据来源标识"""
    if isinstance(data, dict):
        data = data.copy()
        data["_source"] = source
        return data
    elif hasattr(data, "dict"):
        # Pydantic 模型
        data_dict = data.dict()
        data_dict["_source"] = source
        return data_dict
    elif hasattr(data, "model_dump"):
        # Pydantic v2 模型
        data_dict = data.model_dump()
        data_dict["_source"] = source
        return data_dict
    return data


def handle_api_errors(
    operation_name: str,
    allow_fallback: bool = False,
    fallback_data: Optional[Any] = None
):
    """
    API 错误处理装饰器

    参数:
        operation_name: 操作名称，用于日志记录
        allow_fallback: 是否允许降级到模拟数据
        fallback_data: 降级时返回的数据
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                result = await func(*args, **kwargs)
                return result
            except HTTPException:
                # 已经是 HTTPException，直接抛出
                raise
            except Exception as e:
                # 记录详细错误日志
                logger.error(
                    f"API operation failed: {operation_name}",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

                # 检查是否允许降级
                should_fallback = (
                    allow_fallback and
                    fallback_data is not None and
                    _is_fallback_enabled()
                )

                if should_fallback:
                    # 记录降级警告
                    logger.warning(
                        f"Falling back to mock data for: {operation_name}",
                        extra={"operation": operation_name, "fallback": True}
                    )
                    # 添加来源标识
                    return _add_source_to_response(fallback_data, "fallback")

                # 不允许降级，抛出 HTTP 异常
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {operation_name} failed"
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(
                    f"API operation failed: {operation_name}",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

                should_fallback = (
                    allow_fallback and
                    fallback_data is not None and
                    _is_fallback_enabled()
                )

                if should_fallback:
                    logger.warning(
                        f"Falling back to mock data for: {operation_name}",
                        extra={"operation": operation_name, "fallback": True}
                    )
                    return _add_source_to_response(fallback_data, "fallback")

                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {operation_name} failed"
                )

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
