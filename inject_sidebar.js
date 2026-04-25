// HumanThinking 侧边栏手动注入脚本
// 在浏览器控制台中执行此脚本

(function() {
    console.log('开始注入 HumanThinking 侧边栏...');

    // 等待 React 应用加载完成
    const waitForReact = setInterval(() => {
        if (window.React && document.getElementById('root')) {
            clearInterval(waitForReact);
            injectSidebar();
        }
    }, 100);

    // 超时处理
    setTimeout(() => clearInterval(waitForReact), 30000);

    function injectSidebar() {
        try {
            // 创建侧边栏容器
            const sidebarContainer = document.createElement('div');
            sidebarContainer.id = 'humanthinking-sidebar';
            sidebarContainer.style.cssText = `
                position: fixed;
                right: 0;
                top: 0;
                width: 350px;
                height: 100vh;
                background: white;
                box-shadow: -2px 0 8px rgba(0,0,0,0.1);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            `;

            // 侧边栏标题
            sidebarContainer.innerHTML = `
                <div style="padding: 16px; border-bottom: 1px solid #f0f0f0; background: #fafafa;">
                    <h2 style="margin: 0 0 8px 0; font-size: 16px; color: #333;">
                        🧠 HumanThinking 记忆管理
                    </h2>
                    <div style="font-size: 12px; color: #666;">
                        🤖 当前智能体: <span id="current-agent-name">加载中...</span>
                    </div>
                </div>
                <div style="flex: 1; overflow-y: auto; padding: 16px;">
                    <div id="sidebar-content">
                        <p style="color: #666; text-align: center;">正在加载...</p>
                    </div>
                </div>
                <div style="padding: 12px; border-top: 1px solid #f0f0f0; background: #fafafa;">
                    <button onclick="document.body.removeChild(document.getElementById('humanthinking-sidebar'))"
                            style="width: 100%; padding: 8px; background: #f5f5f5; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">
                        关闭侧边栏
                    </button>
                </div>
            `;

            // 添加到页面
            document.body.appendChild(sidebarContainer);
            console.log('✓ 侧边栏容器已添加');

            // 获取当前 Agent 信息
            updateAgentInfo();

            // 加载侧边栏内容
            loadSidebarContent();

            // 定时更新 Agent 信息
            setInterval(updateAgentInfo, 5000);

        } catch (error) {
            console.error('注入失败:', error);
            alert('HumanThinking 侧边栏注入失败: ' + error.message);
        }
    }

    function updateAgentInfo() {
        try {
            const agentStorage = sessionStorage.getItem('qwenpaw-agent-storage');
            if (agentStorage) {
                const data = JSON.parse(agentStorage);
                const agentId = data.state?.selectedAgent;
                const agentName = data.state?.agents?.[agentId]?.name || '未命名Agent';

                const nameSpan = document.getElementById('current-agent-name');
                if (nameSpan) {
                    nameSpan.textContent = `${agentName} (${agentId || '无ID'})`;
                }
            }
        } catch (e) {
            console.error('获取Agent信息失败:', e);
        }
    }

    function loadSidebarContent() {
        const contentDiv = document.getElementById('sidebar-content');
        if (!contentDiv) return;

        // 获取 API 基础 URL
        const baseUrl = (window.QwenPaw?.host?.getApiUrl?.('')) || '';
        const apiBase = baseUrl.includes('/api/')
            ? `${baseUrl}plugins/humanthinking`
            : `${baseUrl}api/plugins/humanthinking`;

        // 获取认证 Token
        const token = window.QwenPaw?.host?.getApiToken?.() || '';

        contentDiv.innerHTML = `
            <div style="margin-bottom: 16px;">
                <h3 style="font-size: 14px; margin: 0 0 12px 0; color: #333;">📊 记忆统计</h3>
                <div id="stats-container" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; text-align: center;">
                        <div style="font-size: 20px; font-weight: bold; color: #1890ff;" id="total-memories">-</div>
                        <div style="font-size: 12px; color: #666;">总记忆</div>
                    </div>
                    <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; text-align: center;">
                        <div style="font-size: 20px; font-weight: bold; color: #52c41a;" id="cross-session">-</div>
                        <div style="font-size: 12px; color: #666;">跨会话</div>
                    </div>
                    <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; text-align: center;">
                        <div style="font-size: 20px; font-weight: bold; color: #faad14;" id="frozen-memories">-</div>
                        <div style="font-size: 12px; color: #666;">冷藏</div>
                    </div>
                    <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; text-align: center;">
                        <div style="font-size: 20px; font-weight: bold; color: #722ed1;" id="active-sessions">-</div>
                        <div style="font-size: 12px; color: #666;">活跃会话</div>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 16px;">
                <h3 style="font-size: 14px; margin: 0 0 12px 0; color: #333;">🌙 睡眠状态</h3>
                <div id="sleep-container" style="background: #f5f5f5; padding: 12px; border-radius: 4px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 24px;" id="sleep-icon">☀️</span>
                        <div>
                            <div style="font-weight: bold;" id="sleep-status">活跃</div>
                            <div style="font-size: 12px; color: #666;" id="sleep-desc">Agent 正在运行</div>
                        </div>
                    </div>
                    <div style="margin-top: 12px; display: flex; gap: 8px;">
                        <button onclick="toggleSleep('light')" style="flex: 1; padding: 8px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">
                            ⭐ 浅睡
                        </button>
                        <button onclick="toggleSleep('deep')" style="flex: 1; padding: 8px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">
                            🌙 深睡
                        </button>
                        <button onclick="toggleSleep('wakeup')" style="flex: 1; padding: 8px; background: #fff; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer;">
                            ☀️ 唤醒
                        </button>
                    </div>
                </div>
            </div>

            <div style="margin-bottom: 16px;">
                <h3 style="font-size: 14px; margin: 0 0 12px 0; color: #333;">💝 情感状态</h3>
                <div id="emotion-container" style="background: #f5f5f5; padding: 12px; border-radius: 4px; text-align: center;">
                    <div style="font-size: 32px; margin-bottom: 8px;" id="emotion-icon">😊</div>
                    <div style="font-weight: bold;" id="emotion-label">开心</div>
                    <div style="font-size: 12px; color: #666;" id="emotion-intensity">强度: 0.75</div>
                </div>
            </div>

            <div style="margin-bottom: 16px;">
                <h3 style="font-size: 14px; margin: 0 0 12px 0; color: #333;">💬 会话列表</h3>
                <div id="sessions-container" style="max-height: 200px; overflow-y: auto;">
                    <p style="color: #666; text-align: center;">加载中...</p>
                </div>
            </div>

            <div style="text-align: center; margin-top: 16px;">
                <button onclick="loadSidebarContent()" style="padding: 8px 16px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 刷新数据
                </button>
            </div>
        `;

        // 加载统计数据
        fetch(`${apiBase}/stats`)
            .then(res => res.json())
            .then(data => {
                document.getElementById('total-memories').textContent = data.total_memories || 0;
                document.getElementById('cross-session').textContent = data.cross_session_memories || 0;
                document.getElementById('frozen-memories').textContent = data.frozen_memories || 0;
                document.getElementById('active-sessions').textContent = data.active_sessions || 0;
            })
            .catch(err => console.error('加载统计数据失败:', err));

        // 加载睡眠状态
        fetch(`${apiBase}/sleep/status`)
            .then(res => res.json())
            .then(data => {
                const icons = { active: '☀️', light: '⭐', rem: '💭', deep: '🌙' };
                const labels = { active: '活跃', light: '浅层睡眠', rem: 'REM睡眠', deep: '深层睡眠' };
                document.getElementById('sleep-icon').textContent = icons[data.status] || '☀️';
                document.getElementById('sleep-status').textContent = labels[data.status] || '活跃';
                document.getElementById('sleep-desc').textContent = data.status === 'active'
                    ? 'Agent 正在运行'
                    : `上次活跃: ${new Date(data.last_active_time * 1000).toLocaleString()}`;
            })
            .catch(err => console.error('加载睡眠状态失败:', err));

        // 加载情感状态
        fetch(`${apiBase}/emotion`)
            .then(res => res.json())
            .then(data => {
                const emotionIcons = { happy: '😊', sad: '😢', angry: '😠', neutral: '😐', surprised: '😮' };
                document.getElementById('emotion-icon').textContent = emotionIcons[data.current_emotion] || '😊';
                document.getElementById('emotion-label').textContent = {
                    happy: '开心', sad: '伤心', angry: '生气', neutral: '中性', surprised: '惊讶'
                }[data.current_emotion] || '开心';
                document.getElementById('emotion-intensity').textContent = `强度: ${data.intensity || 0}`;
            })
            .catch(err => console.error('加载情感状态失败:', err));

        // 加载会话列表
        fetch(`${apiBase}/sessions`)
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById('sessions-container');
                if (Array.isArray(data) && data.length > 0) {
                    container.innerHTML = data.slice(0, 5).map(session => `
                        <div style="padding: 8px; background: #fff; border-radius: 4px; margin-bottom: 8px; border-left: 3px solid #1890ff;">
                            <div style="font-weight: bold; font-size: 13px;">${session.session_name || '未命名会话'}</div>
                            <div style="font-size: 12px; color: #666;">
                                💬 ${session.memory_count || 0} 条记忆 | ${session.user_name || '未知用户'}
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<p style="color: #999; text-align: center;">暂无会话数据</p>';
                }
            })
            .catch(err => {
                console.error('加载会话列表失败:', err);
                document.getElementById('sessions-container').innerHTML =
                    '<p style="color: #f5222d; text-align: center;">加载失败</p>';
            });
    }

    // 睡眠控制函数
    window.toggleSleep = function(action) {
        const baseUrl = (window.QwenPaw?.host?.getApiUrl?.('')) || '';
        const apiBase = baseUrl.includes('/api/')
            ? `${baseUrl}plugins/humanthinking`
            : `${baseUrl}api/plugins/humanthinking`;

        let endpoint = '';
        let method = 'POST';
        let body = {};

        if (action === 'wakeup') {
            endpoint = `${apiBase}/sleep/wakeup`;
        } else {
            endpoint = `${apiBase}/sleep/force`;
            body = { sleep_type: action };
        }

        fetch(endpoint, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${window.QwenPaw?.host?.getApiToken?.() || ''}`
            },
            body: JSON.stringify(body)
        })
        .then(res => res.json())
        .then(data => {
            alert(`操作成功: ${JSON.stringify(data)}`);
            loadSidebarContent(); // 刷新内容
        })
        .catch(err => {
            console.error('睡眠操作失败:', err);
            alert('操作失败: ' + err.message);
        });
    };

    console.log('✓ HumanThinking 侧边栏注入脚本加载完成');
    console.log('请在页面右侧查看 HumanThinking 侧边栏');

})();
