# HumanThinking 代码规范

## 1. 异常处理规范

### ❌ 禁止
```python
# 禁止裸except，会捕获所有异常包括KeyboardInterrupt
try:
    do_something()
except:
    pass
```

### ✅ 正确
```python
# 明确捕获特定异常
try:
    do_something()
except ImportError as e:
    logger.debug(f"Module not available: {e}")
    return fallback_result
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## 2. Pydantic 兼容性

### ❌ 禁止（Pydantic v1语法）
```python
request.dict(exclude_unset=True)
```

### ✅ 正确（Pydantic v2语法）
```python
request.model_dump(exclude_unset=True)
```

## 3. 输入验证

### ✅ 必须
- 所有API端点必须定义请求模型
- 使用Field进行参数约束（min_length, ge, le等）
- 字符串参数必须验证最小长度

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)
```

## 4. 内存管理

### ✅ 必须
- 全局缓存必须设置上限
- 使用LRU策略清理旧数据
- 记录清理日志

```python
_MAX_CACHE_SIZE = 100
if len(cache) >= _MAX_CACHE_SIZE:
    oldest_key = next(iter(cache))
    del cache[oldest_key]
    logger.warning(f"Cache exceeded limit, removed {oldest_key}")
```

## 5. 日志规范

### ✅ 必须
- 关键操作必须记录INFO级别日志
- 错误必须记录ERROR级别日志
- 包含上下文信息（ID、参数等）

```python
logger.info(f"Config updated for agent {agent_id}: {list(fields.keys())}")
logger.error(f"Failed to update memory {memory_id}: {e}")
```

## 6. 数据库操作

### ✅ 必须
- 使用辅助函数统一处理数据库操作
- 区分ImportError（模块不可用）和其他异常
- 提供fallback结果

```python
def _handle_db_operation(operation_name: str, operation_func, fallback_result=None):
    try:
        return operation_func()
    except ImportError as e:
        logger.debug(f"{operation_name}: module not available - {e}")
        return fallback_result
    except Exception as e:
        logger.error(f"{operation_name} failed: {e}")
        return fallback_result
```

## 7. 配置管理

### ✅ 必须
- 支持Agent隔离配置
- 空字符串agent_id应视为None
- 保存失败返回明确错误信息

```python
effective_agent_id = agent_id if agent_id else None
success = save_config(config, agent_id=effective_agent_id)
if not success:
    return {"success": False, "message": "配置保存失败"}
```

## 8. 代码复用

### ✅ 推荐
- 使用字典映射替代长if-else链
- 提取公共逻辑到辅助函数

```python
# 推荐
sleep_methods = {
    "light": "force_light_sleep",
    "rem": "force_rem",
    "deep": "force_deep_sleep"
}
method_name = sleep_methods.get(request.sleep_type)

# 不推荐
if request.sleep_type == "light":
    manager.force_light_sleep(agent_id)
elif request.sleep_type == "rem":
    manager.force_rem(agent_id)
elif request.sleep_type == "deep":
    manager.force_deep_sleep(agent_id)
```
