# HumanThinking 性能优化开发计划

> 基于 [PERFORMANCE_ANALYSIS.md](./PERFORMANCE_ANALYSIS.md) 细化的可操作实施方案
> 版本: v1.0 | 日期: 2026-05-09

---

## 目录

- [Sprint 1：消除高频瓶颈（1-2天）](#sprint-1消除高频瓶颈)
- [Sprint 2：结构级优化（3-5天）](#sprint-2结构级优化)
- [Sprint 3：架构级改进（1-2周）](#sprint-3架构级改进)
- [任务依赖图](#任务依赖图)
- [回滚方案](#回滚方案)

---

## Sprint 1：消除高频瓶颈

> 目标：解决每次操作都会触发、影响面最广的性能问题
> 预期：I/O 延迟 -60%，时间线查询 5x+，CPU 空闲率 +30%

---

### 任务 1.1 — database.py: add_memory() 合并 3 次 commit 为 1 次

| 属性 | 值 |
|------|---|
| 文件 | `core/database.py` |
| 行号 | L876-L903 |
| 严重度 | 🔴 高 |
| 耗时 | 0.5h |
| 依赖 | 无 |

**当前代码问题**（文件 [database.py](file:///e:/项目/Human Thinking Tools/humThink/HumanThinking/core/database.py#L876-L903)）：

```python
# L876-887: 第1次 INSERT + commit
self.cursor.execute("""
    INSERT INTO qwenpaw_memory (agent_id, session_id, ...)
    VALUES (?, ?, ?, ...)
""", (...))
self.conn.commit()

memory_id = self.cursor.lastrowid

# L891-895: 第2次 INSERT + commit
self.cursor.execute(
    "INSERT INTO qwenpaw_memory_fts(content, indexed_content, memory_id, ...) VALUES(?,?,?,?,?)",
    (content, content, memory_id, agent_id, session_id)
)
self.conn.commit()

# L897-903: 第3次 INSERT + commit
if self.enable_distributed and memory_id:
    self.cursor.execute("""
        INSERT INTO qwenpaw_memory_shard_index (memory_id, shard_index, ...)
        VALUES (?, 0, 'qwenpaw_memory', ?)
    """, (memory_id, content[:200]))
    self.conn.commit()
```

**目标代码**（在文件中替换 L876-L906）：

```python
# === 修复：3次commit合并为1次 ===
self.cursor.execute("""
    INSERT INTO qwenpaw_memory 
    (agent_id, session_id, user_id, target_id, role, session_key, content, 
     importance, memory_type, metadata, tags)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    agent_id, session_id, user_id, target_id, role, session_key, content,
    importance, memory_type, 
    json.dumps(metadata or {}),
    json.dumps(tags or [])
))

memory_id = self.cursor.lastrowid

self.cursor.execute(
    "INSERT INTO qwenpaw_memory_fts(content, indexed_content, memory_id, agent_id, session_id) VALUES(?,?,?,?,?)",
    (content, content, memory_id, agent_id, session_id)
)

if self.enable_distributed and memory_id:
    self.cursor.execute("""
        INSERT INTO qwenpaw_memory_shard_index 
        (memory_id, shard_index, original_table, indexed_content)
        VALUES (?, 0, 'qwenpaw_memory', ?)
    """, (memory_id, content[:200]))

self.conn.commit()  # 仅1次commit

logger.debug(f"Added memory {memory_id}: agent={agent_id}, target={target_id}, session={session_id}")
return memory_id
```

**验收标准**：
1. 运行 `python -c "from core.database import HumanThinkingDB; import asyncio; asyncio.run(HumanThinkingDB(':memory:').initialize())"` 不报错
2. 新增一条记忆后，主表、FTS表、分片索引表都有对应记录
3. 对比优化前后 `add_memory()` 耗时（期望 -60%+）

---

### 任务 1.2 — sleep_manager.py: _get_last_activity_time() 用 MAX SQL 替代全量查询

| 属性 | 值 |
|------|---|
| 文件 | `core/sleep_manager.py` |
| 行号 | L377-L402 |
| 严重度 | 🔴 高 |
| 耗时 | 0.5h |
| 依赖 | 需要在 database.py 添加 `get_last_activity_time()` 方法 |

**当前代码问题**（文件 [sleep_manager.py](file:///e:/项目/Human Thinking Tools/humThink/HumanThinking/core/sleep_manager.py#L377-L402)）：

```python
# 查询7天数据只取1条记录——扫描大量无用行
recent = await db.get_recent_memories(agent_id, days=7, limit=1)
```

**步骤 A**：在 `core/database.py` 约 L1510 处（get_stats 附近）添加新方法：

```python
async def get_last_activity_time(self, agent_id: str) -> Optional[str]:
    """获取 Agent 最后活动时间（单条 SQL，直接返回时间戳）"""
    self.cursor.execute("""
        SELECT MAX(created_at) FROM qwenpaw_memory 
        WHERE agent_id = ? AND deleted_at IS NULL
    """, (agent_id,))
    row = self.cursor.fetchone()
    return row[0] if row and row[0] else None
```

**步骤 B**：在 `core/sleep_manager.py` L377-L402 处替换：

```python
async def _get_last_activity_time(self, agent_id: str) -> Optional[float]:
    """从数据库获取 Agent 的最后活动时间（优化版：单条 SQL）"""
    try:
        db = await self._get_or_create_db(agent_id)
        ts = await db.get_last_activity_time(agent_id)
        if ts:
            try:
                return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
            except (ValueError, TypeError):
                try:
                    return float(ts)
                except (ValueError, TypeError):
                    logger.warning(f"Cannot parse timestamp for {agent_id}: {ts}")
        return None
    except Exception as e:
        logger.warning(f"Failed to get last activity time for {agent_id}: {e}")
        return None
```

**验收标准**：
1. 在 SQLite 中执行 `EXPLAIN QUERY PLAN SELECT MAX(created_at) ...` 确认使用了索引 `(agent_id, created_at)`
2. 对比优化前后查询耗时（期望 10x+ 提升）

---

### 任务 1.3 — routes.py: get_memory_timeline() SQL GROUP BY 替代 Python 分组

| 属性 | 值 |
|------|---|
| 文件 | `api/routes.py` |
| 行号 | L744-L810 |
| 严重度 | 🔴 高 |
| 耗时 | 1h |
| 依赖 | 需要在 database.py 添加 `get_timeline_stats()` |

**当前代码问题**（文件 [routes.py](file:///e:/项目/Human Thinking Tools/humThink/HumanThinking/api/routes.py#L764-L798)）：

```python
# 全量加载后在 Python 层分组——传输+序列化开销极大
memories = await db.get_recent_memories(agent_id, days=days)
# ... Python for 循环分组 ...
grouped = defaultdict(lambda: {"count": 0, "events": []})
for m in memories:
    # ... 逐条解析时间、分组 ...
```

**步骤 A**：在 `core/database.py` 约 L1510 处添加：

```python
async def get_timeline_stats(self, agent_id: str, group_by: str = "month", 
                              days: int = 365) -> List[Dict[str, Any]]:
    """聚合时间线统计（数据库层 GROUP BY，只返回聚合结果）"""
    if group_by == "hour":
        fmt = "%Y-%m-%d %H:00"
    elif group_by == "12h":
        # 12h分组：人工拼接 hour block
        self.cursor.execute("""
            SELECT 
                strftime('%Y-%m-%d', created_at) || ' ' || 
                CASE WHEN CAST(strftime('%H', created_at) AS INTEGER) < 12 THEN '00-12' ELSE '12-24' END AS time_key,
                COUNT(*) as count,
                GROUP_CONCAT(SUBSTR(content, 1, 80), '|||') as events
            FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL 
              AND created_at > datetime('now', ?)
            GROUP BY time_key
            ORDER BY time_key DESC
        """, (agent_id, f'-{days} days'))
        return [dict(row) for row in self.cursor.fetchall()]
    elif group_by == "day":
        fmt = "%Y-%m-%d"
    else:
        fmt = "%Y-%m"
    
    self.cursor.execute(f"""
        SELECT 
            strftime('{fmt}', created_at) AS time_key,
            COUNT(*) as count,
            GROUP_CONCAT(SUBSTR(content, 1, 80), '|||') as events
        FROM qwenpaw_memory 
        WHERE agent_id = ? AND deleted_at IS NULL 
          AND created_at > datetime('now', ?)
        GROUP BY time_key
        ORDER BY time_key DESC
    """, (agent_id, f'-{days} days'))
    return [dict(row) for row in self.cursor.fetchall()]
```

**步骤 B**：在 `api/routes.py` L744-L810 处替换为：

```python
async def get_memory_timeline(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None,
    group_by: Optional[str] = None
):
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)

    days_map = {"hour": 1, "12h": 7, "day": 30}
    days = days_map.get(group_by, 365)
    
    rows = await db.get_timeline_stats(agent_id, group_by=group_by or "month", days=days)
    
    result = []
    for row in rows:
        events = []
        if row.get("events"):
            events = [e.strip() for e in str(row["events"]).split("|||") if e.strip()]
        result.append({
            "time_key": row["time_key"],
            "count": row["count"],
            "events": events[:10],
        })
    return result
```

**验收标准**：
1. 使用 `EXPLAIN QUERY PLAN` 确认 GROUP BY 使用了索引
2. 1000 条记忆时，API 响应时间对比优化前减少 5x+
3. 各分组模式（hour/12h/day/month）输出格式与原来一致

---

### 任务 1.4 — frontend.js: 消除轮询，全部改为事件驱动

| 属性 | 值 |
|------|---|
| 文件 | `frontend.js` |
| 行号 | 多处（见下文） |
| 严重度 | 🔴 高 |
| 耗时 | 2h |
| 依赖 | 无 |

**问题清单**：

| 行号 | 问题 | 操作 |
|------|------|------|
| L370-L382 | 语言检测 500ms 轮询 | 改为 MutationObserver |
| L486-L493 | Agent 切换 500ms 轮询 | 改为自定义事件 `agentChanged` |
| L647-L653 | 统计页 5s 轮询 | 改为事件驱动 + 手动刷新 |
| L1068-L1070 | 情感 5s 轮询 | 改为事件驱动 |
| L1192-L1194 | 配置 5s 轮询 | 改为事件驱动 |
| L2036-L2046 | 配置定时器无取消 | 添加 clearInterval |
| L2779-L2806 | 事件监听器未清理 | 添加 removeEventListener |

**步骤 A**（L370-L382 区域）：语言检测改为 MutationObserver

查找类似以下代码：
```javascript
// 旧：500ms轮询
setInterval(() => {
    const langEl = document.querySelector('[data-language]');
    if (langEl) { /* ... */ }
}, 500);
```

替换为：
```javascript
// 新：MutationObserver 事件驱动
const langObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
        if (m.type === 'attributes' && m.attributeName === 'data-language') {
            const lang = m.target.getAttribute('data-language');
            if (lang && lang !== currentLang) {
                currentLang = lang;
                onLanguageChanged(lang);
            }
        }
    }
});
// 在合适的根元素上 observe
langObserver.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['data-language'] });
```

**步骤 B**（L486-L493 区域）：Agent 切换改为事件驱动

查找 `setInterval` 检测 Agent 切换的代码，替换为：

```javascript
// 创建全局事件总线
if (!window.__htEventBus) {
    window.__htEventBus = {
        _listeners: {},
        on(event, fn) { (this._listeners[event] = this._listeners[event] || []).push(fn); },
        off(event, fn) { 
            if (!this._listeners[event]) return;
            this._listeners[event] = this._listeners[event].filter(f => f !== fn);
        },
        emit(event, data) { (this._listeners[event] || []).forEach(fn => fn(data)); }
    };
}

// 监听 agent 变化（不再轮询！）
window.__htEventBus.on('agentChanged', (newAgentId) => {
    currentAgentIdRef = newAgentId;
    fetchAllData();  // 触发数据刷新
});

// Agent 切换时由外部调用（或 MutationObserver 检测 select 变化）
window.__htEventBus.emit('agentChanged', newAgentId);
```

**步骤 C**（L647-L653 等 5s 轮询区域）：添加清理 + 事件驱动

所有 `setInterval` 调用前添加存储和清理逻辑：

```javascript
// 全局存储所有 interval ID
if (!window.__htIntervals) window.__htIntervals = [];

function _setSafeInterval(fn, ms) {
    const id = setInterval(fn, ms);
    window.__htIntervals.push(id);
    return id;
}

function _clearAllIntervals() {
    (window.__htIntervals || []).forEach(id => clearInterval(id));
    window.__htIntervals = [];
}

// 在组件卸载/切换时调用
window.__htEventBus.on('cleanup', () => {
    _clearAllIntervals();
    langObserver && langObserver.disconnect();
});
```

**步骤 D**：确保所有 `addEventListener` 都有对应的清理

在文件末尾搜索所有 `addEventListener` 调用，确保在 `cleanup` 事件中移除：

```javascript
// 模式：存储监听器引用
const _listeners = [];
function _on(el, event, fn) {
    el.addEventListener(event, fn);
    _listeners.push([el, event, fn]);
}
function _removeAllListeners() {
    _listeners.forEach(([el, event, fn]) => el.removeEventListener(event, fn));
    _listeners.length = 0;
}
```

**验收标准**：
1. 打开 Chrome DevTools Performance 面板，录制 30s，确认 CPU 空闲率 > 90%
2. 切换 Agent 后，Chrome Network 面板无 `net::ERR_ABORTED` 错误
3. 长时间使用（10分钟+）后，Chrome Memory 面板无持续增长

---

### 任务 1.5 — sleep_manager.py: _execute_light_sleep() 添加 limit 参数

| 属性 | 值 |
|------|---|
| 文件 | `core/sleep_manager.py` |
| 严重度 | 🔴 高 |
| 耗时 | 0.3h |
| 依赖 | 无 |

**目标**：搜索 `get_recent_memories(agent_id, days=7)` 不带 limit 的调用，统一添加 `limit=200`

```python
# 旧（文件 sleep_manager.py 约 L700-L800）
memories = await db.get_recent_memories(agent_id, days=7)

# 新
memories = await db.get_recent_memories(agent_id, days=7, limit=200)
```

**验收标准**：7天内有 1000+ 条记忆时，该调用耗时 < 100ms

---

### 任务 1.6 — frontend.js: 添加 AbortController 到所有 fetch 请求

| 属性 | 值 |
|------|---|
| 文件 | `frontend.js` |
| 严重度 | 🟡 中 |
| 耗时 | 1h |
| 依赖 | 任务 1.4 |

**目标**：创建全局的请求管理器，所有 fetch 调用统一走此管理器：

```javascript
// 全局请求管理器
if (!window.__htRequestManager) {
    window.__htRequestManager = {
        _controllers: new Map(),
        
        fetch(url, options = {}) {
            const controller = new AbortController();
            const signal = controller.signal;
            const key = url + JSON.stringify(options);
            
            this._controllers.set(key, controller);
            
            return fetch(url, { ...options, signal }).finally(() => {
                this._controllers.delete(key);
            });
        },
        
        abortAll() {
            this._controllers.forEach((ctrl, key) => {
                ctrl.abort();
                this._controllers.delete(key);
            });
        }
    };
}

// 在组件卸载时调用
window.__htEventBus.on('cleanup', () => {
    window.__htRequestManager.abortAll();
});
```

然后替换文件中所有裸 `fetch()` 调用为 `window.__htRequestManager.fetch()`。

**验收标准**：切换 Agent 后 Network 面板无挂起请求

---

### Sprint 1 完成检查清单

- [ ] `add_memory()` 只有 1 次 commit，3 条记录同时写入
- [ ] `_get_last_activity_time()` 使用 `SELECT MAX(created_at)`，< 5ms
- [ ] `get_memory_timeline()` 在数据库层 GROUP BY，不传全量数据
- [ ] 前端无 500ms/5s 轮询，全部事件驱动
- [ ] 所有 fetch 有关联的 AbortController
- [ ] 服务器重启两次后功能正常

---

## Sprint 2：结构级优化

> 目标：解决算法复杂度问题和核心数据结构低效问题
> 预期：搜索延迟 10x+，统计 API 响应 -50%，缓存操作 O(1)

---

### 任务 2.1 — database.py: get_stats() 合并 15 条 SQL 为 1 条聚合查询

| 属性 | 值 |
|------|---|
| 文件 | `core/database.py` |
| 行号 | L1512-L1600 |
| 严重度 | 🟡 中 |
| 耗时 | 1.5h |
| 依赖 | Sprint 1 完成 |

**当前代码**（文件 [database.py](file:///e:/项目/Human Thinking Tools/humThink/HumanThinking/core/database.py#L1512-L1591)）：

```python
# 15条独立查询
self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory WHERE agent_id = ? ...", (agent_id,))
stats["total_memories"] = self.cursor.fetchone()[0]

self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory WHERE agent_id = ? AND access_frozen = 1 ...", (agent_id,))
stats["frozen_memories"] = self.cursor.fetchone()[0]
# ... 13 more queries ...
```

**目标代码**（替换 L1512-L1600）：

```python
async def get_stats(self, agent_id: str) -> Dict[str, Any]:
    """获取 Agent 统计数据（优化版：单条聚合 SQL）"""
    now = datetime.utcnow()
    day_ago = (now - timedelta(days=1)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()
    
    # 核心统计：一条 SQL 搞定
    self.cursor.execute("""
        SELECT
            COUNT(*) AS total_memories,
            SUM(CASE WHEN access_frozen = 1 THEN 1 ELSE 0 END) AS frozen_memories,
            SUM(CASE WHEN created_at > ? THEN 1 ELSE 0 END) AS memories_last_24h,
            SUM(CASE WHEN created_at > ? THEN 1 ELSE 0 END) AS memories_last_7d,
            SUM(CASE WHEN created_at > ? THEN 1 ELSE 0 END) AS memories_last_30d
        FROM qwenpaw_memory
        WHERE agent_id = ? AND deleted_at IS NULL
    """, (day_ago, week_ago, month_ago, agent_id))
    row = self.cursor.fetchone()
    
    stats = dict(row)
    stats["active_memories"] = stats["total_memories"] - stats["frozen_memories"]
    
    # 分 tier 统计
    self.cursor.execute("""
        SELECT memory_tier, COUNT(*) as count 
        FROM qwenpaw_memory 
        WHERE agent_id = ? AND deleted_at IS NULL
        GROUP BY memory_tier
    """, (agent_id,))
    stats["tier_distribution"] = {
        str(r["memory_tier"] or "unknown"): r["count"]
        for r in self.cursor.fetchall()
    }
    
    # 其他表的统计（try/except 保持兼容）
    for label, table in [
        ("archived_memories", "qwenpaw_memory_archive"),
        ("insight_count", "humanthinking_insights"),
        ("dream_log_count", "humanthinking_dream_logs"),
        ("emotional_records", "session_emotional_continuity"),
    ]:
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE agent_id = ?", (agent_id,))
            stats[label] = self.cursor.fetchone()[0]
        except Exception:
            stats[label] = 0
    
    return stats
```

**验收标准**：统计页加载时间减少 50%+

---

### 任务 2.2 — cache_pool.py: LRU 淘汰改为 OrderedDict 实现 O(1)

| 属性 | 值 |
|------|---|
| 文件 | `core/cache_pool.py` |
| 行号 | L144-L200 |
| 严重度 | 🔴 高 |
| 耗时 | 1h |
| 依赖 | 无 |

**当前问题**（文件 [cache_pool.py](file:///e:/项目/Human Thinking Tools/humThink/HumanThinking/core/cache_pool.py#L156-L173)）：

```python
# O(n) 遍历找最久未访问项
for m in self._cache:
    last_access = self._item_last_access.get(m.temp_id, m.created_at)
    if last_access < oldest_time:
        oldest_time = last_access
        oldest_item = m
```

**目标**：将 `self._cache`（list）替换为 `collections.OrderedDict`（key=temp_id, value=MemoryItem），访问时 `move_to_end()`，淘汰时 `popitem(last=False)`。

修改范围涉及 `add_batch`、`search`、`get_all`、`remove`、`_evict_if_needed` 等方法。核心修改：

```python
from collections import OrderedDict

class ReadCache:
    def __init__(self, max_items=1000, max_chars=50000):
        self._cache = OrderedDict()  # 改为 OrderedDict
        # 删除 _item_last_access，不再需要
    
    def _evict_if_needed(self):
        """O(1) 淘汰：直接弹出最久未访问项"""
        while (len(self._cache) > self._max_items or 
               self._total_chars > self._max_chars) and self._cache:
            _, old_item = self._cache.popitem(last=False)
            self._total_chars -= old_item.char_count
    
    async def search(self, query, session_id=None):
        """搜索时为命中的项 move_to_end"""
        async with self._lock:
            results = []
            for m in self._cache.values():
                if session_id and m.session_id != session_id:
                    continue
                if query.lower() in m.content.lower():
                    self._cache.move_to_end(m.temp_id)  # O(1)
                    results.append(m)
            return results
```

**验收标准**：
1. 10000 条缓存时，淘汰操作 < 1μs（原来 O(n) 扫描需 ~100μs）
2. `search()` 命中后访问时间正确更新

---

### 任务 2.3 — memory_manager.py: _inject 方法复用连接池

| 属性 | 值 |
|------|---|
| 文件 | `core/memory_manager.py` |
| 严重度 | 🔴 高 |
| 耗时 | 1h |
| 依赖 | 任务 1.1 |

**目标**：搜索 `sqlite3.connect(db_path)` 调用（绕过连接池的直接连接），改为传入 db 实例：

```python
# 旧（文件 memory_manager.py 约 L750-L800）
def _inject_recent_memories(self) -> str:
    conn = sqlite3.connect(db_path)  # 独立连接，绕过连接池
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""SELECT content, role, created_at 
        FROM qwenpaw_memory WHERE agent_id = ? AND deleted_at IS NULL 
        ORDER BY created_at DESC LIMIT 10""", (self.agent_id,)).fetchall()
    conn.close()

# 新
async def _inject_recent_memories(self, db) -> str:
    db.cursor.execute("""SELECT content, role, created_at 
        FROM qwenpaw_memory WHERE agent_id = ? AND deleted_at IS NULL 
        ORDER BY created_at DESC LIMIT 10""", (self.agent_id,))
    rows = db.cursor.fetchall()
```

同步修改所有调用 `_inject_recent_memories` 的地方，传入 db 实例。

---

### 任务 2.4 — vector_store_backend.py: 集成 FAISS 向量索引

| 属性 | 值 |
|------|---|
| 文件 | `search/vector_store_backend.py`、`search/vector.py` |
| 严重度 | 🔴 高 |
| 耗时 | 3h |
| 依赖 | Sprint 1 完成 |

**当前问题**（文件 [vector_store_backend.py](file:///e:/项目/Human Thinking Tools/humThink/HumanThinking/search/vector_store_backend.py#L390-L414)）：

```python
# 全量遍历 O(n·d)
def _search_in_memory(self, query_vec, top_k):
    scores = []
    for doc_id, doc_vec in self._vectors.items():
        score = cosine_similarity(query_vec, doc_vec)
        scores.append((doc_id, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
```

**目标架构**：

```
_vector_index: faiss.IndexFlatIP  或  faiss.IndexHNSWFlat
_index_to_id: List[str]            # FAISS 内部ID → 业务 doc_id
```

**实现步骤**：

1. 安装 FAISS：`pip install faiss-cpu`

2. 在 `__init__` 中初始化索引：
```python
import faiss
import numpy as np

class VectorStoreBackend:
    def __init__(self, dim=768):
        self.dim = dim
        self._index = faiss.IndexFlatIP(dim)  # 内积相似度
        self._id_to_index: Dict[str, int] = {}
        self._index_to_id: List[str] = []
```

3. 替换 `_search_in_memory`：
```python
def _search_in_memory(self, query_vec, top_k=10):
    if self._index.ntotal == 0:
        return []
    query_np = np.array([query_vec], dtype=np.float32)
    faiss.normalize_L2(query_np)
    scores, indices = self._index.search(query_np, min(top_k, self._index.ntotal))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0 and idx < len(self._index_to_id):
            results.append((self._index_to_id[idx], float(score)))
    return results
```

4. `add_document` 时同步更新 FAISS 索引：
```python
def add_document(self, doc_id, vector):
    vec_np = np.array([vector], dtype=np.float32)
    faiss.normalize_L2(vec_np)
    idx = self._index.ntotal
    self._index.add(vec_np)
    self._id_to_index[doc_id] = idx
    self._index_to_id.append(doc_id)
```

**验收标准**：
1. 10000 条向量搜索 < 10ms（原来全量遍历需 > 200ms）
2. 搜索结果与全量遍历结果 top-10 一致性 > 95%

---

### 任务 2.5 — vector.py: TF-IDF 缓存 IDF 值

| 属性 | 值 |
|------|---|
| 文件 | `search/vector.py` |
| 行号 | L100-L125 |
| 严重度 | 🔴 高 |
| 耗时 | 0.5h |
| 依赖 | 无 |

**目标**：将 `_calculate_tfidf` 改为只在文档变更时重新计算 IDF，查询时复用缓存。

```python
class SparseVectorIndex:
    def __init__(self):
        self._idf_cache = {}
        self._idf_dirty = True  # 脏标记
    
    def _ensure_idf(self):
        if self._idf_dirty:
            self._compute_idf()
            self._idf_dirty = False
    
    def add_document(self, doc):
        self.documents.append(doc)
        self._idf_dirty = True  # 标记脏，不立即重算
    
    def search(self, query_vec, top_k):
        self._ensure_idf()  # 仅在查询时重算
        # ... 使用 self._idf_cache 计算 ...
```

**验收标准**：5 次连续搜索后，IDF 只计算 1 次（用日志验证）

---

### 任务 2.6 — routes.py: _db_cache 添加 TTL 淘汰

| 属性 | 值 |
|------|---|
| 文件 | `api/routes.py` |
| 行号 | L33-L94 |
| 严重度 | 🟡 中 |
| 耗时 | 1h |
| 依赖 | 无 |

**目标**：给 `_db_cache` 添加 TTL（30 分钟）和最大容量（50 个）：

```python
from collections import OrderedDict
import time

_db_cache = OrderedDict()
_db_cache_max_size = 50
_db_cache_ttl = 1800  # 30分钟

async def _get_db(agent_id: str):
    from ..core.database import HumanThinkingDB
    db_path = str(_get_db_path(agent_id))

    if db_path in _db_cache:
        entry = _db_cache[db_path]
        if time.time() - entry["ts"] < _db_cache_ttl:
            try:
                entry["db"].cursor.execute("SELECT 1")
                _db_cache.move_to_end(db_path)
                return entry["db"]
            except Exception:
                pass

    async with _db_lock:
        if db_path in _db_cache:
            entry = _db_cache[db_path]
            if time.time() - entry["ts"] < _db_cache_ttl:
                return entry["db"]
        
        db = HumanThinkingDB(db_path)
        await db.initialize()
        _db_cache[db_path] = {"db": db, "ts": time.time()}
        
        # LRU 淘汰
        while len(_db_cache) > _db_cache_max_size:
            _db_cache.popitem(last=False)
        
        return db
```

**验收标准**：
1. 长时间运行后 `_db_cache` 大小不超过 50
2. 闲置 30 分钟以上的连接自动重新初始化

---

### Sprint 2 完成检查清单

- [ ] `get_stats()` 一次请求只执行 2~3 条 SQL（原来 15+）
- [ ] LRU 淘汰耗时 < 1μs（原来 O(n)）
- [ ] `_inject_recent_memories` 不再创建独立 sqlite3 连接
- [ ] 向量搜索使用 FAISS，10000 条 < 10ms
- [ ] TF-IDF 查询间不重复计算 IDF
- [ ] `_db_cache` 有 TTL 和大小限制

---

## Sprint 3：架构级改进

> 目标：解决深层架构问题，实现长期可持续的性能模型
> 预期：分片 10x+，CPU 空闲率 +50%，矛盾检测 100x+

---

### 任务 3.1 — database.py: _check_and_shard() 用 ATTACH 替代 shutil.copy2

| 属性 | 值 |
|------|---|
| 文件 | `core/database.py` |
| 严重度 | 🔴 高 |
| 耗时 | 3h |
| 依赖 | Sprint 2 完成 |

**当前问题**：`shutil.copy2()` 复制整个 .db 文件（可能 > 100MB），然后 DELETE 不需要的行。

**目标方案**：使用 SQLite ATTACH DATABASE：

```python
async def _check_and_shard(self, agent_id: str, max_size_mb: int = 50):
    """使用 ATTACH 分片（不复制整个文件）"""
    db_size = os.path.getsize(self.db_path) / (1024 * 1024)
    if db_size < max_size_mb:
        return
    
    shard_path = self.db_path.replace('.db', f'.shard_{int(time.time())}.db')
    
    # 新建分片数据库
    shard_conn = sqlite3.connect(shard_path)
    shard_conn.execute("PRAGMA journal_mode=WAL")
    shard_conn.execute("PRAGMA synchronous=NORMAL")
    
    # 复制表结构
    for table in ['qwenpaw_memory', 'qwenpaw_memory_fts']:
        schema = self.conn.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'").fetchone()
        if schema:
            shard_conn.execute(schema[0])
    
    # ATTACH 主库到分片连接，INSERT ... SELECT 只迁移旧数据
    shard_conn.execute(f"ATTACH DATABASE '{self.db_path}' AS main_db")
    shard_conn.execute("""
        INSERT INTO qwenpaw_memory 
        SELECT * FROM main_db.qwenpaw_memory
        WHERE created_at < datetime('now', '-90 days') AND deleted_at IS NULL
    """)
    shard_conn.execute("""
        INSERT INTO qwenpaw_memory_fts
        SELECT * FROM main_db.qwenpaw_memory_fts
        WHERE memory_id IN (SELECT id FROM main_db.qwenpaw_memory
            WHERE created_at < datetime('now', '-90 days') AND deleted_at IS NULL)
    """)
    shard_conn.commit()
    
    # 从主库删除已迁移数据
    self.conn.execute("""
        UPDATE qwenpaw_memory SET deleted_at = CURRENT_TIMESTAMP
        WHERE created_at < datetime('now', '-90 days') AND deleted_at IS NULL
    """)
    self.conn.commit()
    
    shard_conn.close()
    logger.info(f"Shard created: {shard_path}")
```

**验收标准**：
1. 100MB 数据库分片耗时 < 2s（原来 copy2 需 > 10s）
2. 分片后主库数据量减少，查询速度提升

---

### 任务 3.2 — sleep_manager.py: 轮询改事件驱动

| 属性 | 值 |
|------|---|
| 文件 | `core/sleep_manager.py` |
| 严重度 | 🔴 高 |
| 耗时 | 2h |
| 依赖 | 任务 1.2 |

**当前问题**：每 30s 轮询所有 Agent 的活跃状态。

**目标方案**：
1. 每次 `add_memory()` 时记录 `last_activity` 时间
2. 注册"下次检查时间" = `last_activity + idle_threshold`
3. 用 `asyncio.create_task` + `asyncio.sleep` 在预期时间点触发检查，而非轮询

```python
class SleepManager:
    def __init__(self):
        self._scheduled_checks: Dict[str, asyncio.Task] = {}
        self._agent_last_active: Dict[str, float] = {}
    
    def on_agent_activity(self, agent_id: str):
        """Agent 有活动时调用（由 add_memory 触发）"""
        now = time.time()
        self._agent_last_active[agent_id] = now
        
        config = self._get_config(agent_id)
        idle_threshold = config.get('light_sleep_after_idle_minutes', 30) * 60
        
        # 取消旧的定时检查
        if agent_id in self._scheduled_checks:
            self._scheduled_checks[agent_id].cancel()
        
        # 注册新的定时检查
        self._scheduled_checks[agent_id] = asyncio.create_task(
            self._check_after_delay(agent_id, idle_threshold)
        )
    
    async def _check_after_delay(self, agent_id: str, delay: float):
        """延迟 delay 秒后检查是否需要进入睡眠"""
        await asyncio.sleep(delay)
        await self._update_sleep_state(agent_id)
```

**验收标准**：
1. `_background_sleep_loop` 被移除，CPU 不再有空转轮询
2. Agent 不活跃后，在正确的延迟时间点触发睡眠检查

---

### 任务 3.3 — contradiction_detector.py: 语义哈希预筛选 + O(n²) 压缩

| 属性 | 值 |
|------|---|
| 文件 | `core/contradiction_detector.py` |
| 行号 | L557-L562 |
| 严重度 | 🔴 高 |
| 耗时 | 3h |
| 依赖 | Sprint 2 完成 |

**目标方案**：使用 SimHash 将语义相近的文本映射到同一个桶，只在桶内做 O(n²) 比较：

```python
import hashlib

class ContradictionDetector:
    def _simhash(self, text: str) -> int:
        """SimHash：相似文本产生相近的哈希值"""
        # 简化版：使用内容的前几个 token 做分桶
        tokens = text.lower().split()[:20]
        fingerprint = ' '.join(sorted(set(tokens)))
        return hash(fingerprint) % 1000  # 1000 个桶
    
    def detect_batch(self, memories):
        """O(n) 分桶 + 桶内 O(k²) 比较，k << n"""
        buckets = defaultdict(list)
        for m in memories:
            bucket = self._simhash(m['content'][:200])
            buckets[bucket].append(m)
        
        contradictions = []
        for bucket_id, bucket_mems in buckets.items():
            # 桶内比较：每个桶通常只有 1~5 条
            for i in range(len(bucket_mems)):
                for j in range(i + 1, len(bucket_mems)):
                    if self._has_contradiction(bucket_mems[i], bucket_mems[j]):
                        contradictions.append((bucket_mems[i], bucket_mems[j]))
        
        return contradictions
```

**验收标准**：
1. 1000 条记忆的矛盾检测 < 1s（原来 O(n²) 需 > 30s）
2. 检测结果与原方法一致性 > 90%

---

### 任务 3.4 — frontend.js: 建立全局事件总线 + 状态管理

| 属性 | 值 |
|------|---|
| 文件 | `frontend.js` |
| 严重度 | 🔴 高 |
| 耗时 | 4h |
| 依赖 | 任务 1.4, 1.6 |

**目标**：将分散的 querySelector + innerHTML 操作统一为状态驱动的渲染：

```javascript
// 全局状态管理
if (!window.__htState) {
    window.__htState = {
        _state: {},
        _watchers: {},
        
        set(key, value) {
            const old = this._state[key];
            this._state[key] = value;
            (this._watchers[key] || []).forEach(fn => {
                try { fn(value, old); } catch(e) { console.error('Watcher error:', e); }
            });
        },
        
        get(key) { return this._state[key]; },
        
        watch(key, fn) {
            (this._watchers[key] = this._watchers[key] || []).push(fn);
            return () => this.unwatch(key, fn);
        },
        
        unwatch(key, fn) {
            if (this._watchers[key]) {
                this._watchers[key] = this._watchers[key].filter(f => f !== fn);
            }
        }
    };
}

// 示例：情感面板的数据驱动渲染
function initEmotionPanel(container) {
    // 渲染函数 - 只在数据变化时调用
    function render(data) {
        if (!data) return;
        container.innerHTML = `
            <div class="emotion-card">
                <h3>情感状态</h3>
                <div class="emotion-mood">${data.mood || 'neutral'}</div>
                <div class="emotion-intensity">${data.intensity || 0}</div>
            </div>
        `;
    }
    
    // 监听状态变化
    const unwatch = window.__htState.watch('emotionData', render);
    
    // 初始渲染
    render(window.__htState.get('emotionData'));
    
    // 返回清理函数
    return () => { unwatch(); container.innerHTML = ''; };
}
```

**验收标准**：
1. 代码中 `querySelector` + `innerHTML` 调用减少 80%+
2. Chrome Performance 录制中无 "Forced reflow" 警告
3. 组件切换时所有 watcher 正确清理

---

### 任务 3.5 — database.py: rebuild_fts_index 改为增量更新

| 属性 | 值 |
|------|---|
| 文件 | `core/database.py` |
| 严重度 | 🟡 中 |
| 耗时 | 1h |
| 依赖 | 任务 1.1 |

**目标**：不再全量重建 FTS 索引，改为维护增量触发器：

```python
# 在 initialize() 中创建触发器（替代 rebuild_fts_index）
async def _create_fts_triggers(self):
    """创建 FTS 增量更新触发器"""
    self.cursor.executescript("""
        CREATE TRIGGER IF NOT EXISTS memory_fts_insert AFTER INSERT ON qwenpaw_memory
        BEGIN
            INSERT INTO qwenpaw_memory_fts(content, indexed_content, memory_id, agent_id, session_id)
            VALUES (NEW.content, NEW.content, NEW.id, NEW.agent_id, NEW.session_id);
        END;
        
        CREATE TRIGGER IF NOT EXISTS memory_fts_delete AFTER DELETE ON qwenpaw_memory
        BEGIN
            DELETE FROM qwenpaw_memory_fts WHERE memory_id = OLD.id;
        END;
        
        CREATE TRIGGER IF NOT EXISTS memory_fts_update AFTER UPDATE ON qwenpaw_memory
        WHEN NEW.content != OLD.content
        BEGIN
            DELETE FROM qwenpaw_memory_fts WHERE memory_id = OLD.id;
            INSERT INTO qwenpaw_memory_fts(content, indexed_content, memory_id, agent_id, session_id)
            VALUES (NEW.content, NEW.content, NEW.id, NEW.agent_id, NEW.session_id);
        END;
    """)
```

同时，`add_memory()` 中的手动 FTS 插入可以移除，由触发器自动完成。

---

### Sprint 3 完成检查清单

- [ ] 分片使用 ATTACH + INSERT SELECT，100MB 数据库 < 2s
- [ ] 睡眠管理完全事件驱动，无后台轮询循环
- [ ] 矛盾检测使用 SimHash 分桶，1000 条 < 1s
- [ ] 前端状态管理统一，querySelector/innerHTML 减少 80%+
- [ ] FTS 增量更新通过触发器维护

---

## 任务依赖图

```
Sprint 1                          Sprint 2                          Sprint 3
─────────────────────────────────────────────────────────────────────────────

[1.1] commit合并 ──────────────── [2.3] 连接池复用 ──────────── [3.1] 分片 ATTACH
  │                                  │                               │
  ├── [1.2] MAX SQL ←────────────────┤                               │
  │     │                            │                               │
  │     └── [1.5] limit参数          │                               │
  │                                  │                               │
  ├── [1.3] GROUP BY ────────────── [2.1] 聚合统计                 │
  │                                  │                               │
  └── [1.4] 前端轮询清理 ────────── [2.6] 缓存TTL ────────────── [3.2] 事件驱动
        │                            │                               │
        └── [1.6] AbortController    │                               │
                                     │                               │
                    [2.2] LRU O(1) ──┤                               │
                    [2.4] FAISS     ─┤                               │
                    [2.5] IDF缓存   ─┘                               │
                                                                     │
                                          [3.3] SimHash矛盾检测 ──────┤
                                          [3.4] 前端状态管理 ────────┤
                                          [3.5] FTS触发器 ───────────┘
```

---

## 回滚方案

每个 Sprint 开始前：

```bash
# 1. 创建备份分支
git checkout -b backup/sprint-N-$(date +%Y%m%d)
git push origin backup/sprint-N-$(date +%Y%m%d)

# 2. 记录当前性能基线
python scripts/benchmark.py --save-baseline sprint-N-before.json
```

每个任务完成后：

```bash
# 3. 运行基准测试对比
python scripts/benchmark.py --compare sprint-N-before.json
```

回滚命令：

```bash
git checkout <previous-commit>
qwenpaw shutdown
# 上传文件到服务器
qwenpaw app
qwenpaw shutdown
qwenpaw app
```

---

## 附录：新增文件清单

| 文件 | 用途 |
|------|------|
| `scripts/benchmark.py` | 性能基准测试脚本 |
| `core/__init__.py` 更新 | 导出新方法 |
| 无需新增其他文件 | 所有改动均在现有文件中进行 |

---

*开发计划结束。共 3 个 Sprint、16 个任务，预期总耗时 20~30 小时。*