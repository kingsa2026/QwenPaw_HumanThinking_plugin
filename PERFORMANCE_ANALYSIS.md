# HumanThinking 项目性能分析报告

> 生成时间：2026-05-09 | 分析范围：全部源码（core/、search/、api/、frontend.js）

---

## 一、问题总览

| 层级 | 高严重度 | 中严重度 | 低严重度 | 合计 |
|------|---------|---------|---------|------|
| 数据库层 (database.py) | 6 | 7 | 2 | 15 |
| 记忆管理层 (memory_manager.py) | 2 | 3 | 1 | 6 |
| 睡眠管理层 (sleep_manager.py) | 4 | 3 | 1 | 8 |
| API 路由层 (routes.py) | 3 | 5 | 2 | 10 |
| 核心模块 (core/*) | 4 | 6 | 4 | 14 |
| 检索模块 (search/*) | 5 | 4 | 1 | 10 |
| 前端 (frontend.js) | 5 | 7 | 8 | 20 |
| **合计** | **29** | **35** | **19** | **83** |

---

## 二、数据库层 — database.py (2194 行)

### 高严重度 🔴

#### 1. [L560-L580] add_memory 单次操作执行 3 次 commit
**问题**：每次 `add_memory()` 依次插入主表、FTS 索引、分片索引，各执行一次 `self.conn.commit()`。3 次 fsync 操作极大地增加了 I/O 延迟。
```python
self.cursor.execute("INSERT INTO qwenpaw_memory ...")
self.conn.commit()  # 第1次
self.cursor.execute("INSERT INTO qwenpaw_memory_fts ...")
self.conn.commit()  # 第2次
if self.enable_distributed:
    self.cursor.execute("INSERT INTO qwenpaw_memory_shard_index ...")
    self.conn.commit()  # 第3次
```
**建议**：合并为单次 commit，或使用事务包裹。

#### 2. [L1400-L1450] get_stats() 执行约 15 条独立 SELECT
**问题**：统计接口逐条执行总数、今日数、类型分布、温度分布等查询，串行执行 15+ 次 SQL 往返。
**建议**：使用 UNION ALL 合并查询，或使用一条聚合 SQL 返回所有统计维度。

#### 3. [L850-L950] search_memories() 4 级回退搜索
**问题**：搜索逻辑依次尝试 FTS5 → active → frozen → shards → archived，每级失败才回退，最坏情况执行 5 次独立查询。
**建议**：使用 UNION ALL 一次性跨层搜索，或基于查询上下文预判搜索范围。

#### 4. [L1200-L1280] _check_and_shard() 复制整个数据库文件
**问题**：`shutil.copy2()` 复制整个 .db 文件后再执行 DELETE 清理，对大型数据库（>100MB）极其低效。
**建议**：使用 ATTACH DATABASE + INSERT INTO ... SELECT 仅迁移目标数据。

#### 5. [L1050-L1120] _merge_similar_memories() O(n²) 嵌套循环
**问题**：对所有记忆两两比较 Jaccard 相似度，复杂度 O(n²)。1000 条记忆就需要 50 万次比较。
**建议**：使用 MinHash/LSH 等近似去重算法，或分批处理 + 增量合并。

#### 6. [L450-L500] _search_shards() 每个分片打开独立连接
**问题**：搜索分片时对每个 .shard.db 文件调用 `sqlite3.connect()`，打开和关闭连接开销大。
**建议**：使用连接池复用，或 ATTACH 分片到主连接。

### 中严重度 🟡

#### 7. [L300-L350] _row_to_record() 逐字段调用辅助函数
**问题**：每行数据的每个字段都调用 `_get_row_value()` + `_safe_json_loads()`，JSON 解析开销在批量场景下放大。
**建议**：对已知非 JSON 字段跳过 `_safe_json_loads()`，批量场景使用列表推导预判类型。

#### 8. [L1300-L1350] rebuild_fts_index() 全表扫描
**问题**：`INSERT INTO qwenpaw_memory_fts SELECT ... FROM qwenpaw_memory` 全表读取重建索引。
**建议**：改为增量更新 FTS 索引而非全量重建。

#### 9. [L1400-L1450] get_stats() SQL 中使用 datetime('now', ...) 
**问题**：每个统计查询在 SQL 中重复计算 `datetime('now', '-1 day')` 等函数。
**建议**：在 Python 层预计算时间边界，以参数形式传入 SQL。

#### 10. [L200-L250] 缺少复合索引
**问题**：频繁按 `(agent_id, created_at)`、`(agent_id, memory_type)` 等组合查询但可能缺少对应索引。
**建议**：审查查询模式，建立覆盖索引避免回表。

#### 11. [L380-L420] _get_or_create_db() 每次完整 initialize()
**问题**：获取数据库实例时执行完整的表结构检查和初始化。
**建议**：使用轻量级健康检查（如检查 sqlite_master 中表是否存在）替代完整初始化。

#### 12. [L600-L650] 批量写入未使用 executemany
**问题**：批量操作场景下逐条 execute + commit。
**建议**：使用 `executemany()` + 单次 commit。

#### 13. [L750-L800] 内存评分计算重复查询
**问题**：计算六维评分时多次查询同一记忆的不同维度的历史数据。
**建议**：一次性加载相关历史数据，在内存中计算。

### 低严重度 🟢

#### 14. [L100-L130] 连接初始化时的 PRAGMA 串行执行
**问题**：多个 PRAGMA 设置逐个执行。
**建议**：合并为单次 execute 的多语句。

#### 15. [L1600-L1650] 导出功能全量加载到内存
**问题**：导出所有记忆时将全部内容拼接为一个大字符串再写入文件。
**建议**：使用流式写入，逐批处理。

---

## 三、记忆管理层 — memory_manager.py (1523 行)

### 高严重度 🔴

#### 1. [L750-L800] _inject_recent_memories() 打开独立 SQLite 连接
**问题**：绕过连接池直接调用 `sqlite3.connect(db_path)`，每次上下文注入都新建/关闭连接。高频调用（每次 LLM 对话）。
```python
conn = sqlite3.connect(db_path)
rows = conn.execute("SELECT ... LIMIT 10", (self.agent_id,)).fetchall()
conn.close()
```
**建议**：复用 database.py 的连接池，传入已有的 db 实例。

#### 2. [L900-L980] _llm_compact_memory() 同步阻塞 LLM 调用
**问题**：记忆压缩调用 LLM API 是 await 同步等待，在对话流程中阻塞响应生成。
**建议**：异步后台执行记忆压缩，不阻塞当前对话。

### 中严重度 🟡

#### 3. [L500-L550] _init_system_memory() 每次启动检查 + 可能插入
**问题**：启动时检查系统记忆是否存在，不存在则插入约 3KB 内容。
**建议**：减少检查频率，或缓存检查结果。

#### 4. [L600-L680] _build_long_term_memory() 构建大文本注入
**问题**：构建最多 3000 字符的记忆指南文本注入到每次 LLM 上下文中，增加 token 消耗和处理时间。
**建议**：根据对话主题动态裁剪注入内容，只注入相关部分。

#### 5. [L1100-L1150] summarize() 每次对话结束都写记忆
**问题**：每轮对话结束时都存储一条 `importance=4, memory_type="conversation"` 的摘要记忆。
**建议**：合并短对话的摘要，或根据重要性阈值决定是否存储。

### 低严重度 🟢

#### 6. [L700-L730] check_context() 逐条计算 token
**问题**：遍历所有消息逐条估算 token 数量。
**建议**：使用滑动窗口维护累计 token 数，增量更新。

---

## 四、睡眠管理层 — sleep_manager.py (1440 行)

### 高严重度 🔴

#### 1. [L1000-L1100] _background_sleep_loop() 高频轮询所有 Agent
**问题**：每 30 秒轮询所有已注册 Agent 的活跃状态，Agent 数量增长后轮询开销线性增长。
**建议**：使用事件驱动替代轮询；Agent 最后一次活动时注册"预期唤醒"时间，到时再检查。

#### 2. [L600-L650] _get_last_activity_time() 查询 7 天数据只取最新一条
**问题**：`get_recent_memories(agent_id, days=7, limit=1)` 扫描 7 天的全部记忆只为了获取最新时间戳。
```python
recent = await db.get_recent_memories(agent_id, days=7, limit=1)
```
**建议**：使用 `SELECT MAX(created_at) FROM qwenpaw_memory WHERE agent_id=?` 一条 SQL 搞定。

#### 3. [L700-L800] _execute_light_sleep() 无限制查询
**问题**：`get_recent_memories(agent_id, days=7)` 不传 limit 参数，可能返回数千条记录。
**建议**：明确 limit 参数，只加载必需数量的记忆。

#### 4. [L850-L920] _merge_similar_memories() O(n²) Jaccard 相似度
**问题**：对所有记忆对计算字符级 Jaccard 相似度，复杂度 O(n²·m)（m=文本长度）。
```python
def _calculate_text_similarity(self, text1, text2):
    set1 = set(text1)
    set2 = set(text2)
    return len(set1 & set2) / len(set1 | set2)
```
**建议**：使用 SimHash/MinHash 近似算法，或设置最小长度阈值跳过短文本。

### 中严重度 🟡

#### 5. [L300-L350] 配置保存/加载使用 inspect.signature()
**问题**：每次保存或加载配置都调用 `inspect.signature()` 做参数校验，反射调用开销大。
**建议**：在模块初始化时缓存签名信息。

#### 6. [L200-L250] _get_or_create_db() 每个 Agent 完整初始化
**问题**：为每个 Agent 创建独立的 DB 实例并执行完整的 `initialize()`。
**建议**：使用已有的全局 DB 实例，通过 agent_id 区分数据。

#### 7. [L500-L550] _update_sleep_status() 逐条更新
**问题**：批量更新 Agent 睡眠状态时逐条 UPDATE + commit。
**建议**：批量 executemany + 单次 commit。

### 低严重度 🟢

#### 8. [L100-L150] 参数校验逻辑过于复杂
**问题**：多层嵌套的 if/else 校验逻辑。
**建议**：使用声明式校验（Pydantic/dataclass）。

---

## 五、API 路由层 — routes.py (1659 行)

### 高严重度 🔴

#### 1. [L50-L80] _db_cache 无限增长
**问题**：全局字典 `_db_cache = {}` 缓存所有 Agent 的 DB 实例，永不过期、永不清理。Agent 不删除则内存持续增长。
```python
_db_cache = {}
async def _get_db(agent_id: str):
    if agent_id not in _db_cache:
        db = HumanThinkingDB(...)
        await db.initialize()
        _db_cache[agent_id] = db
```
**建议**：加入 TTL 或 LRU 淘汰策略，限制缓存大小。

#### 2. [L350-L420] get_memory_timeline() 全量加载后 Python 分组
**问题**：获取时间段内全部记忆，然后在 Python 中按月份/日期分组，而非在 SQL 层用 GROUP BY。
```python
memories = await db.get_recent_memories(agent_id, days=365)
timeline = {}
for m in memories:
    key = m['created_at'][:7]  # Python 分组
```
**建议**：使用 SQL `GROUP BY strftime('%Y-%m', created_at)` 在数据库层聚合。

#### 3. [L1200-L1430] /uninstall 端点 200+ 行操作
**问题**：卸载接口串行执行文件删除、子进程调用、配置清理等大量阻塞操作。
**建议**：异步后台任务 + 进度反馈，避免 HTTP 超时。

### 中严重度 🟡

#### 4. [L60-L70] _get_db() 每次访问 SELECT 1 健康检查
**问题**：获取缓存 DB 时执行 `SELECT 1` 检查连接健康，高频 API 调用下产生额外查询。
**建议**：使用惰性健康检查（仅在操作失败时重连）。

#### 5. [L150-L200] get_memory_manager() 使用 threading.Lock()
**问题**：创建 MemoryManager 时持有全局锁，并发 API 请求被串行化。
**建议**：使用 asyncio.Lock 或按 agent_id 粒度加锁。

#### 6. [L500-L550] Session 重命名/删除绕过连接池
**问题**：直接使用 `db.cursor.execute()` 而非连接池方法，可能导致连接泄漏。
**建议**：统一使用 `db.execute()` 方法走连接池。

#### 7. [L250-L280] /config POST 创建完整 MemoryManager
**问题**：配置接口创建 `HumanThinkingMemoryManager` 实例仅为了调用 `create_db_if_not_exists()`，开销大。
**建议**：提取轻量级的 DB 存在性检查函数。

#### 8. [L650-L720] update_config 双重保存
**问题**：睡眠配置更新同时调用 `_save_global_config_to_file()` 和 `save_agent_sleep_config()`。
**建议**：合并为单次原子写入。

### 低严重度 🟢

#### 9. [L800-L880] export_memories_to_md() 全量拼接
**问题**：将所有记忆内容拼接为一个字符串后一次性写入文件。
**建议**：分批写入文件流。

#### 10. [L30-L50] 缺少请求超时和速率限制
**问题**：API 路由没有请求超时保护和速率限制。
**建议**：添加中间件级别的 timeout 和 rate limiting。

---

## 六、核心模块 — core/*.py

### 高严重度 🔴

#### 1. [cache_pool.py:L144-L174] LRU 淘汰 O(n) 线性扫描
**问题**：每次触发淘汰时遍历整个缓存找最久未访问项，复杂度 O(n)。
**建议**：使用 `collections.OrderedDict` 或双向链表 + 哈希表实现 O(1) 淘汰。

#### 2. [contradiction_detector.py:L557-L562] 批量检测 O(n²) 全量比较
**问题**：双循环对所有记忆两两进行矛盾检测，没有预过滤。
```python
for i in range(len(memories)):
    for j in range(i+1, len(memories)):
        # 全量比较
```
**建议**：先按主题/标签聚类，仅在同类记忆间检测；使用语义哈希预筛选候选对。

#### 3. [session_buffer.py:L104-L106] add() 无内存上限检查
**问题**：`SessionBuffer.add()` 更新 `total_chars` 但不检查上限，可能导致 buffer 无限增长。
**建议**：添加 max_chars 检查，超出时触发淘汰或刷写。

#### 4. [memory_lifecycle.py:L200-L241] 状态检查 O(n) 全量遍历
**问题**：`check_and_update_lifecycle()` 遍历所有生命周期记录检查状态转换。10000+ 条记录时显著延迟。
**建议**：使用 SQL 层批量状态更新（`UPDATE ... WHERE ...`），不在 Python 层逐条判断。

### 中严重度 🟡

#### 5. [session_bridge.py:L178-L185] 原始 SQL 拼接
**问题**：构建情感桥接时使用字符串拼接构造 SQL，既存在注入风险，也无法利用 SQLite 的预编译缓存。
**建议**：使用参数化查询。

#### 6. [memory_lifecycle.py:L417-L427] 后台循环无重试机制
**问题**：`_background_lifecycle_check` 的 while 循环只记录错误，不重试也不恢复。
**建议**：添加指数退避重试逻辑。

#### 7. [memory_temperature.py:L151-L173] calculate_batch 逐条计算
**问题**：`calculate_batch()` 对列表中的每个记忆项逐一调用 `calculate()`，无法利用向量化计算。
**建议**：批量加载记忆元数据，一次计算多条的衰减值。

#### 8. [channel_adapter.py:L644-L646] 缺少输入校验
**问题**：`get_adapter()` 直接从静态字典取值，不校验 channel_id 合法性。
**建议**：添加参数校验 + 返回默认适配器或抛出明确异常。

#### 9. [session_buffer.py:L166-L174] remove_by_temp_ids O(n) 遍历
**问题**：遍历整个 `_buffer` 列表查找待移除项。
**建议**：使用 `set` 或 `dict` 维护 temp_id 到 buffer 位置的映射。

#### 10. [emotional_engine.py] 情感计算串行执行
**问题**：情感分析逐维度串行计算。
**建议**：将独立的维度计算并行化（asyncio.gather）。

### 低严重度 🟢

#### 11. [memory_lifecycle.py:L276-L284] 归档计数 O(n) 遍历
**问题**：`_should_delete()` 遍历 `self._lifecycle_records.values()` 计算归档数。
**建议**：维护计数器变量，增量更新。

#### 12. [memory_lifecycle.py:L365-L376] 统计信息 O(n) 遍历
**问题**：`get_lifecycle_stats()` 遍历所有记录计算统计。
**建议**：使用 SQL COUNT/GROUP BY 在数据库层统计。

#### 13. [memory_temperature.py:L194-L200] filter_by_temperature O(n) 循环
**问题**：纯 Python 循环过滤。
**建议**：在 SQL 查询中直接添加 WHERE temperature 条件。

#### 14. [cache_pool.py:L181-L200] 搜索 O(n) 线性扫描
**问题**：缓存搜索遍历所有缓存项。
**建议**：建立内存索引（按 agent_id/session_id 哈希）。

---

## 七、检索模块 — search/*.py

### 高严重度 🔴

#### 1. [vector.py:L90-L98] 每次搜索遍历所有文档
**问题**：`search()` 方法遍历 `self.documents`（全部文档）逐条计算相似度。无 ANN 近似搜索，O(n·d)（n=文档数，d=向量维度）。
**建议**：集成 FAISS、Annoy、ScaNN 等向量索引库，或切换到支持 HNSW 的向量数据库。

#### 2. [vector_store_backend.py:L390-L414] _search_in_memory() 全量相似度计算
**问题**：在内存中遍历所有文档计算向量相似度，无高效索引结构。
**建议**：使用 FAISS 的 IndexFlatIP 或 IndexHNSWFlat 加速检索。

#### 3. [vector_store_backend.py:L532-L565] _keyword_search() 无索引逐条匹配
**问题**：关键词搜索遍历所有文档做 `if keyword in doc['content']`，O(n) 复杂度无索引加速。
**建议**：使用 SQLite FTS5 倒排索引，或 Whoosh/Elasticsearch。

#### 4. [cross_session_searcher.py:L80-L131] search() 无预过滤全遍历
**问题**：遍历所有向量索引文档后再在 Python 层做元数据过滤，应先过滤再计算相似度。
**建议**：在向量索引层支持元数据过滤（如 FAISS + IDSelector）。

#### 5. [vector.py:L100-L125] _calculate_tfidf 重复 IDF 计算
**问题**：每次 TF-IDF 查询都重新计算全部文档的 IDF 值，无缓存复用。
**建议**：IDF 值仅在文档集变更时更新，缓存到实例变量。

### 中严重度 🟡

#### 6. [relevance_ranker.py:L69-L91] rank() 逐条多维度计算
**问题**：对每个结果依次计算 BM25 分数、重要性加权、时间衰减，然后嵌入结果中，重复深拷贝开销。
**建议**：批量计算各维度分数，最后一次性组装结果。

#### 7. [agentic_retriever.py:L197-L231] 意图分析正则匹配
**问题**：`_analyze_intent()` 使用多层正则表达式匹配，对复杂查询效率低。
**建议**：如果 LLM 意图分析已实现，跳过正则阶段；否则编译正则对象缓存。

#### 8. [vector_store_backend.py:L567-L606] _merge_results() 简单合并
**问题**：向量结果和关键词结果合并时未根据实际权重做归一化处理。
**建议**：使用加权倒数排名融合（RRF）或线性加权合并。

#### 9. [specialized_retrievers.py:L76-L77] 检索后重复过滤
**问题**：`BaseRetriever.retrieve()` 在数据库搜索返回结果后又做一次 Python 层类型过滤，如果 DB 已筛选则是冗余操作。
**建议**：将类型过滤下推到 SQL WHERE 子句。

### 低严重度 🟢

#### 10. [vector.py:L25-L68] add_document/remove_document 实时 IDF 更新
**问题**：文档增删时立即重算 IDF，批量操作场景下大量重复计算。
**建议**：标记 IDF 为脏（dirty），延迟到下次查询时再重算。

---

## 八、前端 — frontend.js

### 高严重度 🔴

#### 1. [L370-L382] [L486-L493] 多个 500ms 高频轮询
**问题**：语言检测、Agent 切换各用一个 `setInterval` 每 500ms 轮询，持续消耗 CPU。
```
语言检测轮询(500ms) + Agent切换轮询(500ms) + 多处数据轮询(5s)
```
**建议**：全部改为事件驱动（MutationObserver / 自定义事件），消除轮询。

#### 2. [L647-L653] [L1068-L1070] [L1192-L1194] 多处 5 秒定时器未清理
**问题**：统计页、情感模块、配置面板各自设置了 5 秒循环 `setInterval`，组件切换时未 `clearInterval`，导致后台持续发请求。
**建议**：在组件卸载钩子中清理所有定时器。

#### 3. [L2779-L2786] [L2831-L2835] 事件监听器未清理
**问题**：多处 `addEventListener` 绑定事件但缺少对应的 `removeEventListener`，组件切换后旧监听器泄漏。
**建议**：在组件的清理阶段（destroy/unmount）中注销所有监听器。

#### 4. [L1561-L1570] [L3133-L3140] [L3289-L3297] 大量 innerHTML 操作
**问题**：直接用 `innerHTML` 替换大片 DOM 内容，触发完整的解析、布局、绘制流程。
**建议**：使用虚拟 DOM diff（React），或 `insertAdjacentHTML` + DocumentFragment。

#### 5. [L2078-L2086] [L2853-L2860] 大量 querySelector + DOM 直接操作
**问题**：绕过组件框架直接用 `querySelector` 查找和修改 DOM，触发强制同步布局（layout thrashing）。
```javascript
const el = document.querySelector('.xxx');
el.innerHTML = '...';
el.style.display = '...';
```
**建议**：统一使用组件状态驱动渲染，不直接操作 DOM。

### 中严重度 🟡

#### 6. [L2033-L2037] 部分请求缺少 AbortController
**问题**：部分 fetch 调用未关联 AbortController，组件卸载后请求继续执行。
**建议**：所有 fetch 调用关联 AbortController，卸载时 abort。

#### 7. [L2016-L2020] [L1434-L1437] 缺少防抖/节流
**问题**：配置获取、时间线刷新在短时间内可能重复触发，产生冗余请求。
**建议**：对高频触发的操作添加 debounce（300ms）或 throttle。

#### 8. [L2799-L2810] [L2973-L2985] select 元素遍历操作
**问题**：循环处理所有 `ant-select` 元素，查找和操作 DOM 节点，无虚拟滚动。
**建议**：如确实需要批量操作，缓存 NodeList 后操作。

#### 9. [L1750-L1755] 相对时间戳 interval 更新
**问题**：用 `setInterval` 每秒更新"几分钟前"显示，无实际必要。
**建议**：仅首次渲染计算相对时间，不持续更新；或降低频率至每分钟。

#### 10. [L1073-L1080] setTimeout 递归循环
**问题**：用 `setTimeout` 实现循环任务，无明确终止条件。
**建议**：保存 timeoutId，组件卸载时 `clearTimeout`。

#### 11. [L3030-L3070] Tabs 切换逻辑复杂度高
**问题**：Tabs 切换涉及大量 DOM 查询、插入、属性设置。
**建议**：使用组件框架的 Tabs 组件（Ant Design / Headless UI）。

#### 12. [L3268-L3276] 配置保存含大量 DOM 操作
**问题**：保存配置时从 DOM 读取值、验证、再更新 DOM。
**建议**：使用状态驱动的表单库（Formik / React Hook Form）。

### 低严重度 🟢

#### 13. [L1215-L1224] Agent 切换轮询非事件驱动
#### 14. [L2036-L2046] 配置组件缺少定时器取消机制
#### 15. [L3204-L3216] setTimeout 无生命周期管理
#### 16. [L2871-L2880] 动态 DOM 插入无虚拟化
#### 17. [L3053-L3067] DOM 更新 + 组件渲染混合
#### 18. [L3259-L3265] 页面加载状态未优化渲染
#### 19. [L2780-L2786] 延迟重试无终止条件
#### 20. [L3201-L3210] 状态更新与 DOM 操作混合

---

## 九、优化优先级路线图

### 第一阶段（立即见效）— 1~2 天
| 优先级 | 问题 | 预期提升 |
|--------|------|---------|
| 1 | database.py: add_memory 合并 commit | I/O 延迟 -60% |
| 2 | sleep_manager.py: _get_last_activity_time 改用 MAX SQL | 查询速度 10x+ |
| 3 | routes.py: get_memory_timeline SQL GROUP BY | 时间线加载 5x+ |
| 4 | frontend.js: 清理轮询 + 改为事件驱动 | CPU 空闲率 +30% |

### 第二阶段（结构优化）— 3~5 天
| 优先级 | 问题 | 预期提升 |
|--------|------|---------|
| 5 | database.py: get_stats() 合并为单条聚合 SQL | API 响应 -50% |
| 6 | cache_pool.py: LRU 使用 OrderedDict | 淘汰操作 O(1) |
| 7 | memory_manager.py: _inject_recent_memories 复用连接池 | 连接开销消除 |
| 8 | vector_store_backend: _search_in_memory 集成 FAISS | 搜索延迟 10x+ |

### 第三阶段（架构改进）— 1~2 周
| 优先级 | 问题 | 预期提升 |
|--------|------|---------|
| 9 | database.py: _check_and_shard 使用 ATTACH + INSERT | 分片操作 10x+ |
| 10 | sleep_manager.py: 轮询改事件驱动 | CPU 空闲率 +50% |
| 11 | contradiction_detector.py: 语义哈希预筛选 | 矛盾检测 100x+ (大数据) |
| 12 | frontend.js: 全面状态管理重构 | 整体流畅度显著提升 |

---

## 十、监控建议

1. **添加慢查询日志**：记录 >100ms 的 SQL 查询
2. **添加 API 耗时中间件**：记录每个端点的 P50/P95/P99 延迟
3. **添加前端性能埋点**：FCP、LCP、TBT 指标
4. **添加数据库大小监控**：.db 文件大小告警（>50MB）
5. **添加缓存命中率监控**：_db_cache 的命中/未命中比

---

*报告结束。共发现 83 个性能问题，其中高严重度 29 个、中严重度 35 个、低严重度 19 个。*