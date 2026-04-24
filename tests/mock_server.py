# -*- coding: utf-8 -*-
"""模拟QwenPaw服务器用于测试插件功能

这个模拟服务器实现了HumanThinking插件的所有API端点，
用于在不启动完整QwenPaw的情况下测试插件功能。
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os
from pathlib import Path

app = FastAPI(title="QwenPaw Mock Server with HumanThinking Plugin")

# 模拟数据
mock_data = {
    "stats": {
        "total_memories": 42,
        "cross_session_memories": 15,
        "frozen_memories": 8,
        "active_sessions": 3,
        "emotional_states": 5
    },
    "config": {
        "enable_cross_session": True,
        "enable_emotion": True,
        "frozen_days": 30,
        "archive_days": 90,
        "delete_days": 180,
        "max_results": 5,
        "session_idle_timeout": 180,
    },
    "emotions": {
        "current_emotion": "happy",
        "intensity": 0.75,
        "history": [
            {"emotion": "neutral", "intensity": 0.5, "timestamp": "2025-01-01T10:00:00"},
            {"emotion": "happy", "intensity": 0.8, "timestamp": "2025-01-01T11:00:00"},
        ]
    },
    "sessions": [
        {"id": "session_1", "name": "会话 1", "created_at": "2025-01-01T10:00:00", "message_count": 25},
        {"id": "session_2", "name": "会话 2", "created_at": "2025-01-01T11:00:00", "message_count": 18},
        {"id": "session_3", "name": "会话 3", "created_at": "2025-01-01T12:00:00", "message_count": 32},
    ],
    "memories": [
        {"id": "mem_1", "content": "用户喜欢编程", "importance": 0.9, "created_at": "2025-01-01T10:00:00"},
        {"id": "mem_2", "content": "用户喜欢Python", "importance": 0.85, "created_at": "2025-01-01T10:30:00"},
        {"id": "mem_3", "content": "用户正在开发插件", "importance": 0.8, "created_at": "2025-01-01T11:00:00"},
    ],
    "timeline": [
        {"date": "2025-01-01", "count": 5, "events": ["创建记忆", "更新情感"]},
        {"date": "2025-01-02", "count": 3, "events": ["搜索记忆"]},
    ],
    "dreams": [
        {"id": "dream_1", "content": "分析了用户的编程习惯", "created_at": "2025-01-01T02:00:00"},
    ]
}

# ========== HumanThinking API Routes ==========

@app.get("/plugin/humanthinking/stats")
async def humanthinking_stats():
    """Get HumanThinking memory statistics"""
    return mock_data["stats"]

@app.get("/plugin/humanthinking/config")
async def humanthinking_get_config():
    """Get HumanThinking configuration"""
    return mock_data["config"]

@app.post("/plugin/humanthinking/config")
async def humanthinking_update_config(request: Request):
    """Update HumanThinking configuration"""
    data = await request.json()
    mock_data["config"].update(data)
    return {"success": True, "config": mock_data["config"]}

@app.post("/plugin/humanthinking/search")
async def humanthinking_search(request: Request):
    """Search memories"""
    data = await request.json()
    query = data.get("query", "").lower()
    
    # 简单搜索逻辑
    results = []
    for mem in mock_data["memories"]:
        if query in mem["content"].lower():
            results.append(mem)
    
    return {
        "memories": results,
        "total": len(results),
        "query": query
    }

@app.get("/plugin/humanthinking/emotion")
async def humanthinking_emotion():
    """Get emotional state"""
    return mock_data["emotions"]

@app.get("/plugin/humanthinking/sessions")
async def humanthinking_sessions():
    """Get session list"""
    return mock_data["sessions"]

@app.get("/plugin/humanthinking/memories/recent")
async def humanthinking_recent_memories(limit: int = 20):
    """Get recent memories"""
    return {
        "memories": mock_data["memories"][:limit],
        "total": len(mock_data["memories"])
    }

@app.get("/plugin/humanthinking/memories/timeline")
async def humanthinking_timeline():
    """Get memory timeline"""
    return mock_data["timeline"]

@app.post("/plugin/humanthinking/sessions/bridge")
async def humanthinking_bridge_sessions(request: Request):
    """Bridge two sessions"""
    data = await request.json()
    return {
        "success": True,
        "source_session": data.get("source_session"),
        "target_session": data.get("target_session")
    }

@app.get("/plugin/humanthinking/dreams")
async def humanthinking_dreams(limit: int = 10):
    """Get dream records"""
    return mock_data["dreams"][:limit]

# ========== Console Static Files ==========

# 创建一个模拟的console HTML页面
console_html = '''<!DOCTYPE html>
<html>
<head>
    <title>QwenPaw Console</title>
    <script src="/console/assets/main.js"></script>
</head>
<body>
    <div id="root"></div>
</body>
</html>'''

@app.get("/console/", response_class=HTMLResponse)
async def console_index():
    return console_html

# 模拟JS文件内容（包含human_thinking注入）
js_content = '''
// QwenPaw Console Main JS
const memoryManagerOptions = [
    {value:"remelight",label:"ReMeLight"},
    {value:"human_thinking",label:"Human Thinking"}
];

// HumanThinking: Agent切换自动刷新配置
(function(){
    var lastAgent = sessionStorage.getItem("qwenpaw-agent-storage") ? JSON.parse(sessionStorage.getItem("qwenpaw-agent-storage")).state?.selectedAgent : null;
    var checkInterval = setInterval(function(){
        try {
            var storage = sessionStorage.getItem("qwenpaw-agent-storage");
            if (!storage) return;
            var data = JSON.parse(storage);
            var currentAgent = data.state?.selectedAgent;
            if (currentAgent && currentAgent !== lastAgent) {
                lastAgent = currentAgent;
                console.log("[HumanThinking] Agent switched to:", currentAgent, "- Reloading config...");
                if (window.__agentConfigFetch) {
                    window.__agentConfigFetch();
                } else {
                    window.location.reload();
                }
            }
        } catch(e) {}
    }, 500);
})();

console.log("QwenPaw Console Loaded");
'''

@app.get("/console/assets/main.js")
async def console_js():
    return js_content

@app.get("/health")
async def health_check():
    return {"status": "ok", "plugin": "humanthinking"}

if __name__ == "__main__":
    print("=" * 60)
    print("QwenPaw Mock Server with HumanThinking Plugin")
    print("=" * 60)
    print("\n可用端点:")
    print("  - http://localhost:8000/plugin/humanthinking/stats")
    print("  - http://localhost:8000/plugin/humanthinking/config")
    print("  - http://localhost:8000/plugin/humanthinking/search")
    print("  - http://localhost:8000/plugin/humanthinking/emotion")
    print("  - http://localhost:8000/plugin/humanthinking/sessions")
    print("  - http://localhost:8000/plugin/humanthinking/memories/recent")
    print("  - http://localhost:8000/plugin/humanthinking/memories/timeline")
    print("  - http://localhost:8000/plugin/humanthinking/sessions/bridge")
    print("  - http://localhost:8000/plugin/humanthinking/dreams")
    print("\nConsole页面:")
    print("  - http://localhost:8000/console/")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
