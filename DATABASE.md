# HumanThinking 数据库使用说明

## 数据库文件位置

每个 Agent 独立的数据库文件：
```
/root/.qwenpaw/workspaces/{agent_id}/memory/human_thinking.db
```

## 表结构

### 1. qwenpaw_memory (记忆主表)

存储所有对话记忆的核心表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| agent_id | TEXT | Agent 标识（必填） |
| session_id | TEXT | 会话 ID（必填） |
| user_id | TEXT | 用户 ID |
| target_id | TEXT | 对话对象 ID（隔离不同用户） |
| role | TEXT | 角色：`user` / `assistant` / `system` |
| session_key | TEXT | 自动生成的会话唯一键 |
| content | TEXT | 记忆内容（必填） |
| importance | INTEGER | 重要性 1-5，默认 3 |
| memory_type | TEXT | 记忆类型：`general` / `fact` / `preference` / `emotion` |
| metadata | TEXT | JSON 扩展字段 |
| tags | TEXT | JSON 标签数组 |
| access_count | INTEGER | 访问次数 |
| last_accessed_at | DATETIME | 最后访问时间 |
| access_frozen | INTEGER | 是否冷藏（1=已冷藏） |
| frozen_at | DATETIME | 冷藏时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| deleted_at | DATETIME | 删除时间（软删除） |

**索引**：
- `idx_memory_agent` - 按 agent_id 查询
- `idx_memory_session` - 按 session_id 查询
- `idx_memory_user` - 按 user_id 查询
- `idx_memory_target` - 按 target_id 隔离
- `idx_memory_importance` - 按重要性排序

---

### 2. qwenpaw_memory_relations (记忆关联表)

记录记忆之间的语义关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| memory_id1 | INTEGER | 记忆1 ID |
| memory_id2 | INTEGER | 记忆2 ID |
| relation_type | TEXT | 关系类型：`similar` / `related` / `contradict` |
| similarity_score | REAL | 相似度分数 0-1 |
| created_at | DATETIME | 创建时间 |

---

### 3. session_relationships (会话关系表)

记录跨会话的关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| source_session | TEXT | 源会话 |
| target_session | TEXT | 目标会话 |
| agent_id | TEXT | Agent 标识 |
| relationship_type | TEXT | 关系类型 |
| confidence | REAL | 置信度 0-1 |
| evidence | TEXT | 证据内容 |
| created_at | DATETIME | 创建时间 |

---

### 4. session_emotional_continuity (情感连续性表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| session_id | TEXT | 会话 ID |
| agent_id | TEXT | Agent 标识 |
| user_id | TEXT | 用户 ID |
| emotional_state | TEXT | 情感状态 JSON |
| emotional_history | TEXT | 情感历史 JSON |
| context_summary | TEXT | 上下文摘要 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

---

### 5. qwenpaw_memory_version (版本管理表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| db_version | TEXT | 数据库版本 |
| schema_version | TEXT | Schema 版本 |
| min_compatible_version | TEXT | 最低兼容版本 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| upgrade_history | TEXT | 升级历史 JSON |

---

## 常用查询示例

### 查询当前会话的记忆
```sql
SELECT * FROM qwenpaw_memory
WHERE agent_id = 'default'
  AND session_id = 'web:user123'
  AND deleted_at IS NULL
ORDER BY created_at DESC;
```

### 跨会话查询（所有历史）
```sql
SELECT * FROM qwenpaw_memory
WHERE agent_id = 'default'
  AND deleted_at IS NULL
ORDER BY importance DESC, created_at DESC
LIMIT 20;
```

### 按关键词搜索
```sql
SELECT * FROM qwenpaw_memory
WHERE agent_id = 'default'
  AND content LIKE '%关键词%'
  AND deleted_at IS NULL
ORDER BY importance DESC
LIMIT 10;
```

### 清理不活跃会话
```sql
-- 删除 30 天前且访问次数少于 5 次的记忆
DELETE FROM qwenpaw_memory
WHERE agent_id = 'default'
  AND access_count < 5
  AND created_at < datetime('now', '-30 days')
  AND deleted_at IS NULL;
```

### 冷藏低重要性记忆
```sql
UPDATE qwenpaw_memory
SET access_frozen = 1, frozen_at = datetime('now')
WHERE agent_id = 'default'
  AND importance < 2
  AND access_count < 3
  AND deleted_at IS NULL;
```

---

## 注意事项

1. **软删除**：所有删除操作都是软删除（设置 `deleted_at` 时间戳）
2. **会话隔离**：通过 `agent_id + session_id + target_id` 实现三层隔离
3. **自动索引**：所有常用查询字段都已建立索引
4. **重要性排序**：查询时默认按 `importance DESC` 排序，优先返回重要记忆
