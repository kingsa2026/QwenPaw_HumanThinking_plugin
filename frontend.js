/**
 * HumanThinking 插件前端入口 - 简化可靠版
 */

(function() {
    'use strict';

    console.log('[HumanThinking] 前端插件加载中...');

    const PLUGIN_ID = 'humanthinking';

    // 注入原生风格CSS
    const injectNativeStyles = () => {
        if (document.getElementById('humanthinking-native-styles')) return;
        const style = document.createElement('style');
        style.id = 'humanthinking-native-styles';
        style.textContent = `
            /* HumanThinking 原生风格CSS - 参照QwenPaw Console */
            .ht-page-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
                padding: 20px;
                border-bottom: 1px solid #eae9e7;
                flex-shrink: 0;
            }
            .dark-mode .ht-page-header {
                border-bottom-color: rgba(255, 255, 255, 0.12);
            }
            .ht-page-title {
                font-size: 20px;
                font-weight: 600;
                color: #333;
                line-height: 1.4;
            }
            .dark-mode .ht-page-title {
                color: rgba(255, 255, 255, 0.85);
            }
            .ht-page-subtitle {
                font-size: 13px;
                color: #999;
                margin-top: 2px;
            }
            .dark-mode .ht-page-subtitle {
                color: rgba(255, 255, 255, 0.45);
            }
            .ht-content {
                flex: 1;
                overflow: auto;
                padding: 16px 20px 0;
            }
            .ht-form-actions {
                display: flex;
                gap: 8px;
                border-top: 1px solid #eae9e7;
                padding-top: 16px;
                margin-top: 8px;
            }
            .dark-mode .ht-form-actions {
                border-top-color: rgba(255, 255, 255, 0.12);
            }
            .ht-card {
                background: #fff;
                border-radius: 8px;
                border: 1px solid #eae9e7;
                padding: 16px;
            }
            .dark-mode .ht-card {
                background: rgba(255, 255, 255, 0.04);
                border-color: rgba(255, 255, 255, 0.12);
            }
            .ht-stat-card {
                background: #fff;
                border-radius: 8px;
                border: 1px solid #eae9e7;
                padding: 16px;
                transition: all 0.3s;
            }
            .ht-stat-card:hover {
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }
            .dark-mode .ht-stat-card {
                background: rgba(255, 255, 255, 0.04);
                border-color: rgba(255, 255, 255, 0.12);
            }
            .ht-divider {
                border: none;
                border-top: 1px solid #eae9e7;
                margin: 16px 0;
            }
            .dark-mode .ht-divider {
                border-top-color: rgba(255, 255, 255, 0.12);
            }
            .ht-agent-bar {
                font-size: 13px;
                color: inherit;
                opacity: 0.75;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .ht-status-light {
                transition: all 0.5s ease;
            }
            .ht-status-light.active {
                animation: ht-pulse 2s infinite;
            }
            .ht-status-light.light {
                animation: ht-breathe 3s infinite;
            }
            .ht-status-light.rem {
                animation: ht-wave 2s infinite;
            }
            .ht-status-light.deep {
                animation: ht-flicker 4s infinite;
            }
            @keyframes ht-pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            @keyframes ht-breathe {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(0.95); opacity: 0.8; }
            }
            @keyframes ht-wave {
                0%, 100% { transform: translateY(0); }
                25% { transform: translateY(-5px); }
                75% { transform: translateY(5px); }
            }
            @keyframes ht-flicker {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
        `;
        document.head.appendChild(style);
        console.log('[HumanThinking] 原生风格CSS已注入');
    };

    // 页面加载完成后注入CSS
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectNativeStyles);
    } else {
        injectNativeStyles();
    }

    // 获取API基础URL
    const getApiBase = () => {
        const baseUrl = window.QwenPaw?.host?.getApiUrl?.('') || '';
        return baseUrl.includes('/api/')
            ? `${baseUrl}plugins/humanthinking`
            : `${baseUrl}api/plugins/humanthinking`;
    };

    // 获取请求头
    const getHeaders = () => {
        const headers = {};
        const token = window.QwenPaw?.host?.getApiToken?.();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    };

    // API请求封装
    const apiRequest = async (endpoint, options = {}) => {
        const url = `${getApiBase()}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: { ...getHeaders(), ...options.headers }
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    };

    // 获取当前Agent信息（支持sessionStorage和localStorage）
    const getCurrentAgent = () => {
        try {
            // 优先从sessionStorage读取
            let agentStorage = sessionStorage.getItem('qwenpaw-agent-storage');
            // 如果sessionStorage没有，尝试从localStorage读取
            if (!agentStorage) {
                agentStorage = localStorage.getItem('qwenpaw-agent-storage');
            }
            if (agentStorage) {
                const data = JSON.parse(agentStorage);
                const agentId = data.state?.selectedAgent;
                const agents = data.state?.agents;
                
                // 支持数组格式和对象格式
                let agentName = '';
                if (Array.isArray(agents)) {
                    const found = agents.find(a => a.id === agentId || a.agent_id === agentId);
                    agentName = found?.name || found?.agent_name || '';
                } else if (agents && typeof agents === 'object') {
                    agentName = agents[agentId]?.name || agents[agentId]?.agent_name || '';
                }
                
                return {
                    agent_id: agentId,
                    agent_name: agentName || ''
                };
            }
        } catch (e) {
            console.error('[HumanThinking] 获取Agent信息失败:', e);
        }
        return { agent_id: '', agent_name: '未选择Agent' };
    };

    // 等待依赖
    const waitForDependencies = () => {
        return new Promise((resolve) => {
            const check = () => {
                if (window.QwenPaw?.host?.React && window.QwenPaw?.host?.antd) {
                    resolve();
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    };

    // 创建组件
    const createComponents = () => {
        const React = window.QwenPaw.host.React;
        const { useState, useEffect, useCallback } = React;
        const { Card, Tabs, Button, List, Statistic, Row, Col, Progress, message, Input, Space, Tag, Timeline, Switch, Slider, Form, Select, Popconfirm, Modal, Empty, Checkbox, Radio, Divider } = window.QwenPaw.host.antd;

        // 智能体信息栏 - 使用原生CSS类
        const AgentInfoBar = () => {
            const [agent, setAgent] = useState({ agent_id: '', agent_name: '加载中...' });

            useEffect(() => {
                const updateAgent = () => {
                    setAgent(getCurrentAgent());
                };
                updateAgent();
                const interval = setInterval(updateAgent, 1000);
                return () => clearInterval(interval);
            }, []);

            return React.createElement('div', { className: 'ht-agent-bar' },
                React.createElement('span', { style: { fontSize: '14px' } }, '🤖'),
                React.createElement('span', null, '当前智能体：'),
                React.createElement('span', { style: { fontWeight: 600 } }, agent.agent_name || '未选择')
            );
        };

        // 记忆管理侧边栏
        const MemoryManagementSidebar = () => {
            const [activeTab, setActiveTab] = useState('stats');
            const [stats, setStats] = useState(null);
            const [sessions, setSessions] = useState([]);

            useEffect(() => {
                const fetchData = async () => {
                    try {
                        const [statsRes, sessionsRes] = await Promise.all([
                            apiRequest('/stats'),
                            apiRequest('/sessions')
                        ]);
                        setStats(statsRes);
                        setSessions(Array.isArray(sessionsRes) ? sessionsRes : []);
                    } catch (e) {
                        console.error('[HumanThinking] 获取数据失败:', e);
                    }
                };
                fetchData();
                const interval = setInterval(fetchData, 5000);
                return () => clearInterval(interval);
            }, []);

            const renderStats = () => {
                if (!stats) return React.createElement(Empty, { description: '加载中...' });
                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Row, { gutter: [16, 16] },
                        React.createElement(Col, { span: 12 },
                            React.createElement(Card, { size: 'small' },
                                React.createElement(Statistic, { title: '总记忆', value: stats.total_memories || 0, valueStyle: { color: '#1890ff' } })
                            )
                        ),
                        React.createElement(Col, { span: 12 },
                            React.createElement(Card, { size: 'small' },
                                React.createElement(Statistic, { title: '跨会话', value: stats.cross_session_memories || 0, valueStyle: { color: '#52c41a' } })
                            )
                        ),
                        React.createElement(Col, { span: 12 },
                            React.createElement(Card, { size: 'small' },
                                React.createElement(Statistic, { title: '冷藏', value: stats.frozen_memories || 0, valueStyle: { color: '#faad14' } })
                            )
                        ),
                        React.createElement(Col, { span: 12 },
                            React.createElement(Card, { size: 'small' },
                                React.createElement(Statistic, { title: '活跃会话', value: stats.active_sessions || 0, valueStyle: { color: '#722ed1' } })
                            )
                        )
                    )
                );
            };

            // 记忆搜索
            const [searchQuery, setSearchQuery] = useState('');
            const [searchResults, setSearchResults] = useState([]);
            const [searchLoading, setSearchLoading] = useState(false);
            const [selectedMemories, setSelectedMemories] = useState([]);
            const [editingMemory, setEditingMemory] = useState(null);
            const [editContent, setEditContent] = useState('');
            const [editType, setEditType] = useState('fact');
            const [editImportance, setEditImportance] = useState(3);
            const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);

            const handleSearch = async () => {
                if (!searchQuery.trim()) return;
                setSearchLoading(true);
                try {
                    const data = await apiRequest('/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: searchQuery, limit: 10 })
                    });
                    setSearchResults(data.memories || []);
                    setSelectedMemories([]);
                } catch (e) {
                    message.error('搜索失败');
                } finally {
                    setSearchLoading(false);
                }
            };

            const handleSelectAll = (e) => {
                if (e.target.checked) {
                    setSelectedMemories(searchResults.map(m => m.id));
                } else {
                    setSelectedMemories([]);
                }
            };

            const handleSelectMemory = (memoryId) => {
                setSelectedMemories(prev =>
                    prev.includes(memoryId)
                        ? prev.filter(id => id !== memoryId)
                        : [...prev, memoryId]
                );
            };

            const handleBatchDelete = async () => {
                setDeleteConfirmVisible(true);
            };

            const handleConfirmDelete = async () => {
                try {
                    await apiRequest('/memories/batch', {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ memory_ids: selectedMemories })
                    });
                    message.success('已删除 ' + selectedMemories.length + ' 条记忆');
                    setSearchResults(prev => prev.filter(m => !selectedMemories.includes(m.id)));
                    setSelectedMemories([]);
                    setDeleteConfirmVisible(false);
                } catch (e) {
                    message.error('删除失败');
                }
            };

            const handleEdit = (memory) => {
                setEditingMemory(memory);
                setEditContent(memory.content || '');
                setEditType(memory.memory_type || 'fact');
                setEditImportance(memory.importance || 3);
            };

            const handleSaveEdit = async () => {
                try {
                    await apiRequest('/memories/' + editingMemory.id, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            content: editContent,
                            memory_type: editType,
                            importance: editImportance
                        })
                    });
                    message.success('保存成功');
                    setSearchResults(prev => prev.map(m =>
                        m.id === editingMemory.id
                            ? { ...m, content: editContent, memory_type: editType, importance: editImportance }
                            : m
                    ));
                    setEditingMemory(null);
                } catch (e) {
                    message.error('保存失败');
                }
            };

            const renderSearch = () => {
                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Input.Search, {
                        placeholder: '输入关键词搜索记忆...',
                        value: searchQuery,
                        onChange: e => setSearchQuery(e.target.value),
                        onSearch: handleSearch,
                        loading: searchLoading,
                        enterButton: '搜索',
                        style: { marginBottom: 16 }
                    }),
                    searchResults.length > 0 && React.createElement('div', { style: { marginBottom: 16, padding: '8px 0' } },
                        React.createElement(Space, null,
                            React.createElement(Checkbox, {
                                checked: selectedMemories.length === searchResults.length && searchResults.length > 0,
                                indeterminate: selectedMemories.length > 0 && selectedMemories.length < searchResults.length,
                                onChange: handleSelectAll
                            }, '全选 (' + selectedMemories.length + '/' + searchResults.length + ')'),
                            selectedMemories.length > 0 && React.createElement(Button, { danger: true, size: 'small', onClick: handleBatchDelete }, '批量删除(' + selectedMemories.length + ')')
                        )
                    ),
                    searchResults.length > 0 && React.createElement(List, {
                        size: 'small',
                        dataSource: searchResults,
                        renderItem: (item) => React.createElement(List.Item, {
                            actions: [
                                React.createElement(Button, { type: 'primary', size: 'small', onClick: () => handleEdit(item) }, '编辑')
                            ]
                        },
                            React.createElement('div', { style: { width: '100%' } },
                                React.createElement('div', { style: { display: 'flex', alignItems: 'flex-start', gap: 8 } },
                                    React.createElement(Checkbox, {
                                        checked: selectedMemories.includes(item.id),
                                        onChange: () => handleSelectMemory(item.id)
                                    }),
                                    React.createElement('div', { style: { flex: 1 } },
                                        React.createElement('div', { style: { marginBottom: 4 } }, item.content || '无内容'),
                                        React.createElement('div', null,
                                            React.createElement(Tag, { size: 'small', color: 'blue' }, item.memory_type || '记忆'),
                                            React.createElement(Tag, { size: 'small' }, '重要性: ' + (item.importance || 3)),
                                            React.createElement('span', { style: { fontSize: 12, color: '#999', marginLeft: 8 } },
                                                item.timestamp ? new Date(item.timestamp).toLocaleString() : ''
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    }),
                    React.createElement(Modal, {
                        title: '编辑记忆',
                        open: !!editingMemory,
                        onOk: handleSaveEdit,
                        onCancel: () => setEditingMemory(null)
                    },
                        React.createElement('div', { style: { marginBottom: 16 } },
                            React.createElement('label', null, '记忆内容'),
                            React.createElement(Input.TextArea, {
                                value: editContent,
                                onChange: e => setEditContent(e.target.value),
                                rows: 4
                            })
                        ),
                        React.createElement('div', { style: { marginBottom: 16 } },
                            React.createElement('label', null, '记忆类型'),
                            React.createElement(Select, {
                                value: editType,
                                onChange: value => setEditType(value),
                                style: { width: '100%' },
                                options: [
                                    { value: 'fact', label: '📋 事实' },
                                    { value: 'emotion', label: '💝 情感' },
                                    { value: 'preference', label: '⭐ 偏好' },
                                    { value: 'order', label: '🛒 订单' },
                                    { value: 'address', label: '📍 地址' },
                                    { value: 'contact', label: '📞 联系' },
                                    { value: 'other', label: '📦 其他' }
                                ]
                            })
                        ),
                        React.createElement('div', null,
                            React.createElement('label', null, '重要性'),
                            React.createElement(Radio.Group, {
                                value: editImportance,
                                onChange: e => setEditImportance(e.target.value)
                            }, [1, 2, 3, 4, 5].map(i =>
                                React.createElement(Radio.Button, { key: i, value: i }, '⭐'.repeat(i))
                            ))
                        )
                    ),
                    React.createElement(Modal, {
                        title: '⚠️ 确认批量删除',
                        open: deleteConfirmVisible,
                        onOk: handleConfirmDelete,
                        onCancel: () => setDeleteConfirmVisible(false),
                        okText: '确认删除',
                        cancelText: '取消',
                        okButtonProps: { danger: true }
                    },
                        React.createElement('div', { style: { marginBottom: 16 } },
                            '确定要删除以下 ',
                            selectedMemories.length,
                            ' 条记忆吗？此操作不可恢复！'
                        ),
                        React.createElement('div', {
                            style: {
                                maxHeight: 200,
                                overflow: 'auto',
                                background: 'rgba(128,128,128,0.08)',
                                padding: 12,
                                borderRadius: 4
                            }
                        },
                            searchResults
                                .filter(m => selectedMemories.includes(m.id))
                                .map(m =>
                                    React.createElement('div', {
                                        key: m.id,
                                        style: {
                                            marginBottom: 8,
                                            fontSize: 13,
                                            color: '#666'
                                        }
                                    }, '• ' + (m.content || '无内容').substring(0, 50) + ((m.content || '').length > 50 ? '...' : ''))
                                )
                        )
                    )
                );
            };

            // 情感状态
            const [emotion, setEmotion] = useState(null);

            useEffect(() => {
                const fetchEmotion = async () => {
                    try {
                        const data = await apiRequest('/emotion');
                        setEmotion(data);
                    } catch (e) {
                        console.error('[HumanThinking] 获取情感失败:', e);
                    }
                };
                fetchEmotion();
                const interval = setInterval(fetchEmotion, 5000);
                return () => clearInterval(interval);
            }, []);

            const renderEmotion = () => {
                const emotionConfig = {
                    happy: { icon: '😊', label: '开心', color: '#52c41a' },
                    sad: { icon: '😢', label: '伤心', color: '#1890ff' },
                    angry: { icon: '😠', label: '生气', color: '#ff4d4f' },
                    neutral: { icon: '😐', label: '中性', color: '#999' },
                    surprised: { icon: '😮', label: '惊讶', color: '#faad14' }
                };
                const current = emotionConfig[emotion?.current_emotion] || emotionConfig.neutral;
                const history = (emotion?.history || []).slice().reverse();

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement('div', { style: { textAlign: 'center', padding: '24px 0', borderBottom: '1px solid #eae9e7', marginBottom: 16 } },
                        React.createElement('div', {
                            style: {
                                width: 120,
                                height: 120,
                                borderRadius: '50%',
                                background: current.color + '20',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                margin: '0 auto 16px',
                                fontSize: 60
                            }
                        }, current.icon),
                        React.createElement('div', { style: { fontSize: 24, fontWeight: 'bold', color: current.color } },
                            current.label
                        ),
                        React.createElement('div', { style: { fontSize: 14, color: '#666', marginTop: 8 } },
                            '强度: ' + ((emotion?.intensity || 0) * 100).toFixed(0) + '%'
                        )
                    ),
                    React.createElement('h4', { style: { marginBottom: 12 } }, '最近情感变化'),
                    history.length === 0
                        ? React.createElement(Empty, { description: '暂无情感历史' })
                        : React.createElement(List, {
                            size: 'small',
                            dataSource: history,
                            renderItem: (item) => {
                                const cfg = emotionConfig[item.emotion] || emotionConfig.neutral;
                                return React.createElement(List.Item, null,
                                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, width: '100%' } },
                                        React.createElement('span', { style: { fontSize: 20 } }, cfg.icon),
                                        React.createElement('div', { style: { flex: 1 } },
                                            React.createElement('div', { style: { fontWeight: 'bold', color: cfg.color } }, cfg.label),
                                            React.createElement('div', { style: { fontSize: 12, color: '#999' } },
                                                item.timestamp ? new Date(item.timestamp).toLocaleString() : ''
                                            )
                                        ),
                                        React.createElement('div', { style: { color: cfg.color, fontWeight: 'bold' } },
                                            ((item.intensity || 0) * 100).toFixed(0) + '%'
                                        )
                                    )
                                );
                            }
                        })
                );
            };

            // 配置面板
            const [config, setConfig] = useState(null);
            const currentAgentIdRef = React.useRef('');

            useEffect(() => {
                const fetchConfig = async () => {
                    try {
                        const agent = getCurrentAgent();
                        // 只在有agent_id时传入，避免空字符串
                        const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                        const data = await apiRequest('/config' + queryParam);
                        setConfig(data);
                        currentAgentIdRef.current = agent.agent_id;
                        console.log('[HumanThinking] 配置已加载，agent:', agent.agent_id || 'global');
                    } catch (e) {
                        console.error('[HumanThinking] 获取配置失败:', e);
                        // 加载失败时使用默认配置
                        setConfig({
                            enable_cross_session: true,
                            enable_emotion: true,
                            frozen_days: 30,
                            archive_days: 90,
                            delete_days: 180,
                            max_results: 5,
                            session_idle_timeout: 180,
                            refresh_interval: 5,
                            max_memory_chars: 150,
                            enable_distributed_db: false,
                            db_size_threshold_mb: 800,
                            disable_file_memory: true,
                        });
                    }
                };
                fetchConfig();

                // Agent切换检测：storage事件监听（跨标签页实时响应）+ 小interval保底（同标签页内检测）
                const handleStorageChange = (e) => {
                    if (e.key === 'qwenpaw-agent-storage' && e.newValue) {
                        try {
                            const data = JSON.parse(e.newValue);
                            const newAgentId = data.state?.selectedAgent;
                            if (newAgentId !== currentAgentIdRef.current) {
                                console.log('[HumanThinking] Agent切换 detected (storage):', currentAgentIdRef.current, '->', newAgentId);
                                fetchConfig();
                            }
                        } catch (err) {
                            console.error('[HumanThinking] 解析storage事件失败:', err);
                        }
                    }
                };
                window.addEventListener('storage', handleStorageChange);

                // 同标签页内保底检测（5秒间隔）
                const interval = setInterval(() => {
                    const agent = getCurrentAgent();
                    if (agent.agent_id !== currentAgentIdRef.current) {
                        console.log('[HumanThinking] Agent切换 detected (interval):', currentAgentIdRef.current, '->', agent.agent_id);
                        fetchConfig();
                    }
                }, 5000);

                return () => {
                    window.removeEventListener('storage', handleStorageChange);
                    clearInterval(interval);
                };
            }, []);

            const handleSaveConfig = async () => {
                try {
                    const agent = getCurrentAgent();
                    // 只在有agent_id时传入，避免空字符串
                    const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                    await apiRequest('/config' + queryParam, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
                    message.success('配置已保存');
                } catch (e) {
                    message.error('保存失败');
                }
            };

            const renderConfig = () => {
                if (!config) return React.createElement(Empty, { description: '加载中...' });

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '跨会话记忆'),
                        React.createElement(Switch, {
                            checked: config.enable_cross_session,
                            onChange: checked => setConfig({ ...config, enable_cross_session: checked }),
                            checkedChildren: '开启',
                            unCheckedChildren: '关闭'
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '情感跟踪'),
                        React.createElement(Switch, {
                            checked: config.enable_emotion,
                            onChange: checked => setConfig({ ...config, enable_emotion: checked }),
                            checkedChildren: '开启',
                            unCheckedChildren: '关闭'
                        })
                    ),
                    // 分布式数据库开关 - 默认关闭，开启后无法关闭
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '分布式数据库'),
                        React.createElement(Switch, {
                            checked: config.enable_distributed_db || false,
                            disabled: config.enable_distributed_db || false,
                            onChange: checked => {
                                if (!config.enable_distributed_db) {
                                    setConfig({ ...config, enable_distributed_db: checked });
                                }
                            },
                            checkedChildren: '已启用',
                            unCheckedChildren: '已禁用'
                        }),
                        React.createElement('div', { style: { fontSize: 12, color: '#999', marginTop: 4 } }, 
                            config.enable_distributed_db ? '分布式数据库已启用，不可关闭' : '开启后将启用分布式数据库（开启后不可关闭）'
                        )
                    ),
                    React.createElement(Divider, null),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '会话空闲超时（秒）'),
                        React.createElement(Slider, {
                            min: 60,
                            max: 600,
                            value: config.session_idle_timeout || 300,
                            onChange: value => setConfig({ ...config, session_idle_timeout: value }),
                            marks: { 60: '60s', 300: '300s', 600: '600s' }
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '单条记忆最大字符数'),
                        React.createElement(Slider, {
                            min: 100,
                            max: 500,
                            value: config.max_memory_chars || 300,
                            onChange: value => setConfig({ ...config, max_memory_chars: value }),
                            marks: { 100: '100', 300: '300', 500: '500' }
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '搜索限制（条）'),
                        React.createElement(Slider, {
                            min: 5,
                            max: 50,
                            value: config.max_results || 10,
                            onChange: value => setConfig({ ...config, max_results: value }),
                            marks: { 5: '5', 25: '25', 50: '50' }
                        })
                    ),
                    React.createElement(Divider, null),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '冷藏天数'),
                        React.createElement(Slider, {
                            min: 7,
                            max: 90,
                            value: config.frozen_days || 30,
                            onChange: value => setConfig({ ...config, frozen_days: value }),
                            marks: { 7: '7天', 30: '30天', 90: '90天' }
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '归档天数'),
                        React.createElement(Slider, {
                            min: 30,
                            max: 365,
                            value: config.archive_days || 180,
                            onChange: value => setConfig({ ...config, archive_days: value }),
                            marks: { 30: '30天', 180: '180天', 365: '365天' }
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '删除天数'),
                        React.createElement(Slider, {
                            min: 90,
                            max: 730,
                            value: config.delete_days || 365,
                            onChange: value => setConfig({ ...config, delete_days: value }),
                            marks: { 90: '90天', 365: '1年', 730: '2年' }
                        })
                    ),
                    // 保存按钮区域 - 使用原生CSS类
                    React.createElement('div', { className: 'ht-form-actions' },
                        React.createElement(Button, { type: 'primary', size: 'large', onClick: handleSaveConfig }, '保存配置')
                    )
                );
            };

            // 时间线
            const [timelineData, setTimelineData] = useState([]);
            const [timeFilter, setTimeFilter] = useState('all');

            useEffect(() => {
                const fetchTimeline = async () => {
                    try {
                        const data = await apiRequest('/memories/timeline');
                        setTimelineData(Array.isArray(data) ? data : []);
                    } catch (e) {
                        console.error('[HumanThinking] 获取时间线失败:', e);
                    }
                };
                fetchTimeline();
            }, []);

            const getFilteredTimeline = () => {
                if (timeFilter === 'all') return timelineData;
                const now = new Date();
                const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                return timelineData.filter(item => {
                    const itemDate = new Date(item.date);
                    if (timeFilter === 'today') return itemDate >= today;
                    if (timeFilter === 'week') {
                        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                        return itemDate >= weekAgo;
                    }
                    if (timeFilter === 'month') {
                        const monthAgo = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
                        return itemDate >= monthAgo;
                    }
                    return true;
                });
            };

            const renderTimeline = () => {
                const filtered = getFilteredTimeline();
                const filterButtons = [
                    { key: 'all', label: '全部' },
                    { key: 'today', label: '今天' },
                    { key: 'week', label: '本周' },
                    { key: 'month', label: '本月' }
                ];

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement(Space, null,
                            filterButtons.map(btn =>
                                React.createElement(Button, {
                                    key: btn.key,
                                    type: timeFilter === btn.key ? 'primary' : 'default',
                                    size: 'small',
                                    onClick: () => setTimeFilter(btn.key)
                                }, btn.label)
                            )
                        )
                    ),
                    filtered.length === 0
                        ? React.createElement(Empty, { description: '该时间段暂无记忆事件' })
                        : React.createElement(Timeline, null,
                            filtered.map((item, index) =>
                                React.createElement(Timeline.Item, {
                                    key: index,
                                    color: item.count > 5 ? 'red' : item.count > 2 ? 'blue' : 'green'
                                },
                                    React.createElement('div', { style: { fontWeight: 'bold', marginBottom: 4 } },
                                        item.date,
                                        React.createElement(Tag, { color: 'blue', style: { marginLeft: 8 } }, item.count + ' 条')
                                    ),
                                    React.createElement('div', null,
                                        (item.events || []).map((evt, i) =>
                                            React.createElement('div', {
                                                key: i,
                                                style: { fontSize: 13, color: '#666', marginBottom: 2 }
                                            }, '• ' + evt)
                                        )
                                    )
                                )
                            )
                        )
                );
            };

            const tabItems = [
                { key: 'stats', label: '📊 记忆统计', children: renderStats() },
                { key: 'search', label: '🔍 记忆搜索', children: renderSearch() },
                { key: 'emotion', label: '💝 情感状态', children: renderEmotion() },
                { key: 'timeline', label: '📅 时间线', children: renderTimeline() },
                { key: 'config', label: '⚙️ 记忆配置', children: renderConfig() }
            ];

            return React.createElement('div', { style: { height: '100%', display: 'flex', flexDirection: 'column' } },
                // 标题栏 - 使用原生CSS类
                React.createElement('div', { className: 'ht-page-header' },
                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } },
                        React.createElement('span', { style: { fontSize: '20px' } }, '🧠'),
                        React.createElement('div', null,
                            React.createElement('div', { className: 'ht-page-title' }, 'HumanThinking 记忆管理'),
                            React.createElement('div', { className: 'ht-page-subtitle' }, '跨会话记忆保持与情感计算')
                        )
                    ),
                    React.createElement(AgentInfoBar)
                ),
                // 内容区域 - 使用原生CSS类
                React.createElement('div', { className: 'ht-content' },
                    React.createElement(Tabs, {
                        items: tabItems,
                        activeKey: activeTab,
                        onChange: setActiveTab
                    })
                )
            );
        };

        // 睡眠管理侧边栏 - 简化版
        const SleepManagementSidebar = () => {
            const [activeTab, setActiveTab] = useState('status');
            const [sleepStatus, setSleepStatus] = useState(null);

            useEffect(() => {
                const fetchStatus = async () => {
                    try {
                        const data = await apiRequest('/sleep/status');
                        setSleepStatus(data);
                    } catch (e) {
                        console.error('[HumanThinking] 获取睡眠状态失败:', e);
                    }
                };
                fetchStatus();
                const interval = setInterval(fetchStatus, 5000);
                return () => clearInterval(interval);
            }, []);

            const handleSleepAction = async (action) => {
                try {
                    const endpoint = action === 'wakeup' ? '/sleep/wakeup' : '/sleep/force';
                    const body = action === 'wakeup' ? {} : { sleep_type: action };
                    await apiRequest(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    message.success('操作成功');
                } catch (e) {
                    message.error('操作失败');
                }
            };

            const statusConfig = {
                active: { icon: '☀️', label: '活跃', color: '#52c41a' },
                light: { icon: '⭐', label: '浅层睡眠', color: '#faad14' },
                rem: { icon: '💭', label: 'REM睡眠', color: '#1890ff' },
                deep: { icon: '🌙', label: '深层睡眠', color: '#722ed1' }
            };

            const current = statusConfig[sleepStatus?.sleep_type] || statusConfig.active;

            // 状态灯样式 - 使用原生CSS类
            const getStatusLightClass = () => {
                const type = sleepStatus?.sleep_type || 'active';
                return 'ht-status-light ' + type;
            };

            const getStatusLightStyle = () => {
                const baseStyle = {
                    width: 140,
                    height: 140,
                    borderRadius: '50%',
                    background: current.color + '20',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 20px',
                    fontSize: 72,
                    border: '4px solid ' + current.color + '40',
                    transition: 'all 0.5s ease'
                };
                
                // 根据状态添加阴影
                if (sleepStatus?.sleep_type === 'active') {
                    baseStyle.boxShadow = `0 0 20px ${current.color}60, 0 0 40px ${current.color}40`;
                } else if (sleepStatus?.sleep_type === 'light') {
                    baseStyle.boxShadow = `0 0 15px ${current.color}50`;
                } else if (sleepStatus?.sleep_type === 'rem') {
                    baseStyle.boxShadow = `0 0 20px ${current.color}60`;
                } else if (sleepStatus?.sleep_type === 'deep') {
                    baseStyle.boxShadow = `0 0 10px ${current.color}40`;
                }
                
                return baseStyle;
            };

            const renderStatus = () => {
                return React.createElement('div', { style: { padding: 24, textAlign: 'center' } },
                    React.createElement('div', {
                        className: getStatusLightClass(),
                        style: getStatusLightStyle()
                    }, current.icon),
                    React.createElement('div', { style: { fontSize: 24, fontWeight: 'bold', color: current.color } },
                        current.label
                    ),
                    React.createElement('div', { style: { marginTop: 24 } },
                        React.createElement(Button, { size: 'large', onClick: () => handleSleepAction('light') }, '⭐ 浅睡'),
                        React.createElement(Button, { size: 'large', onClick: () => handleSleepAction('deep'), style: { marginLeft: 8 } }, '🌙 深睡'),
                        React.createElement(Button, { type: 'primary', size: 'large', onClick: () => handleSleepAction('wakeup'), style: { marginLeft: 8 } }, '☀️ 唤醒')
                    )
                );
            };

            // 睡眠配置
            const [sleepConfig, setSleepConfig] = useState(null);
            const sleepCurrentAgentIdRef = React.useRef('');

            useEffect(() => {
                const fetchConfig = async () => {
                    try {
                        const agent = getCurrentAgent();
                        const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                        const data = await apiRequest('/sleep/config' + queryParam);
                        setSleepConfig(data);
                        sleepCurrentAgentIdRef.current = agent.agent_id;
                        console.log('[HumanThinking] 睡眠配置已加载，agent:', agent.agent_id || 'global');
                    } catch (e) {
                        console.error('[HumanThinking] 获取睡眠配置失败:', e);
                        // 加载失败时使用默认配置
                        setSleepConfig({
                            enable_agent_sleep: true,
                            light_sleep_minutes: 30,
                            rem_minutes: 60,
                            deep_sleep_minutes: 120,
                            consolidate_days: 7,
                            frozen_days: 30,
                            archive_days: 90,
                            delete_days: 180,
                            enable_insight: true,
                            enable_dream_log: true,
                        });
                    }
                };
                fetchConfig();

                // Agent切换检测：storage事件监听（跨标签页实时响应）+ 小interval保底（同标签页内检测）
                const handleStorageChange = (e) => {
                    if (e.key === 'qwenpaw-agent-storage' && e.newValue) {
                        try {
                            const data = JSON.parse(e.newValue);
                            const newAgentId = data.state?.selectedAgent;
                            if (newAgentId !== sleepCurrentAgentIdRef.current) {
                                console.log('[HumanThinking] Agent切换 detected (storage):', sleepCurrentAgentIdRef.current, '->', newAgentId);
                                fetchConfig();
                            }
                        } catch (err) {
                            console.error('[HumanThinking] 解析storage事件失败:', err);
                        }
                    }
                };
                window.addEventListener('storage', handleStorageChange);

                // 同标签页内保底检测（5秒间隔）
                const interval = setInterval(() => {
                    const agent = getCurrentAgent();
                    if (agent.agent_id !== sleepCurrentAgentIdRef.current) {
                        console.log('[HumanThinking] Agent切换 detected (interval):', sleepCurrentAgentIdRef.current, '->', agent.agent_id);
                        fetchConfig();
                    }
                }, 5000);

                return () => {
                    window.removeEventListener('storage', handleStorageChange);
                    clearInterval(interval);
                };
            }, []);

            const handleSaveConfig = async (values) => {
                try {
                    const agent = getCurrentAgent();
                    const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                    await apiRequest('/sleep/config' + queryParam, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(values)
                    });
                    message.success('配置已保存');
                } catch (e) {
                    message.error('保存失败');
                }
            };

            const renderConfig = () => {
                if (!sleepConfig) return React.createElement(Empty, { description: '加载中...' });

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '启用Agent睡眠'),
                        React.createElement(Switch, {
                            checked: sleepConfig.enable_agent_sleep,
                            onChange: checked => setSleepConfig({ ...sleepConfig, enable_agent_sleep: checked }),
                            checkedChildren: '开启',
                            unCheckedChildren: '关闭'
                        })
                    ),
                    React.createElement(Divider, null),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '进入睡眠（分钟）'),
                        React.createElement(Slider, {
                            min: 5,
                            max: 120,
                            value: sleepConfig.light_sleep_minutes || 30,
                            onChange: value => setSleepConfig({ ...sleepConfig, light_sleep_minutes: value }),
                            marks: { 5: '5分', 30: '30分', 120: '120分' }
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '浅睡持续（分钟）'),
                        React.createElement(Slider, {
                            min: 15,
                            max: 180,
                            value: sleepConfig.rem_minutes || 60,
                            onChange: value => setSleepConfig({ ...sleepConfig, rem_minutes: value }),
                            marks: { 15: '15分', 60: '60分', 180: '180分' }
                        })
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '深睡进入（分钟）'),
                        React.createElement(Slider, {
                            min: 30,
                            max: 240,
                            value: sleepConfig.deep_sleep_minutes || 120,
                            onChange: value => setSleepConfig({ ...sleepConfig, deep_sleep_minutes: value }),
                            marks: { 30: '30分', 120: '120分', 240: '240分' }
                        })
                    ),
                    React.createElement(Divider, null),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '自动整合记忆'),
                        React.createElement(Switch, {
                            checked: sleepConfig.enable_insight,
                            onChange: checked => setSleepConfig({ ...sleepConfig, enable_insight: checked }),
                            checkedChildren: '开启',
                            unCheckedChildren: '关闭'
                        }),
                        React.createElement('div', { style: { fontSize: 12, color: '#999', marginTop: 4 } }, '开启后自动整合记忆，扫描N天内记忆')
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '洞察灯'),
                        React.createElement(Switch, {
                            checked: sleepConfig.enable_insight_light !== false,
                            onChange: checked => setSleepConfig({ ...sleepConfig, enable_insight_light: checked }),
                            checkedChildren: '开启',
                            unCheckedChildren: '关闭'
                        }),
                        React.createElement('div', { style: { fontSize: 12, color: '#999', marginTop: 4 } }, '开启后生成记忆洞察和反思摘要')
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '梦境日志'),
                        React.createElement(Switch, {
                            checked: sleepConfig.enable_dream_log,
                            onChange: checked => setSleepConfig({ ...sleepConfig, enable_dream_log: checked }),
                            checkedChildren: '开启',
                            unCheckedChildren: '关闭'
                        }),
                        React.createElement('div', { style: { fontSize: 12, color: '#999', marginTop: 4 } }, '记录睡眠各阶段处理日志')
                    ),
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '记忆整合天数'),
                        React.createElement(Slider, {
                            min: 1,
                            max: 30,
                            value: sleepConfig.consolidate_days || 7,
                            onChange: value => setSleepConfig({ ...sleepConfig, consolidate_days: value }),
                            marks: { 1: '1天', 7: '7天', 30: '30天' }
                        })
                    ),
                    // 保存按钮区域 - 使用原生CSS类
                    React.createElement('div', { className: 'ht-form-actions' },
                        React.createElement(Button, {
                            type: 'primary',
                            size: 'large',
                            onClick: () => handleSaveConfig(sleepConfig)
                        }, '保存配置')
                    )
                );
            };

            // 功能说明
            const renderEnergy = () => {
                const sleepStates = [
                    { icon: '☀️', name: '活跃状态', energy: '高', color: '#52c41a', desc: 'Agent处于完全活跃状态，正常响应用户请求。' },
                    { icon: '⭐', name: '浅层睡眠', energy: '中-高', color: '#faad14', desc: 'Agent进入轻度休息状态，降低功耗但仍保持基本响应能力。' },
                    { icon: '💭', name: 'REM阶段', energy: '中', color: '#1890ff', desc: '模拟人类的REM睡眠，进行记忆重组和模式识别。' },
                    { icon: '🌙', name: '深层睡眠', energy: '低', color: '#722ed1', desc: 'Agent进入深度整合状态，对候选记忆进行六维加权评分，执行遗忘曲线算法。' }
                ];

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement('h4', { style: { marginBottom: 16 } }, '睡眠状态功能说明'),
                    React.createElement(List, {
                        dataSource: sleepStates,
                        renderItem: (item) => React.createElement(List.Item, null,
                            React.createElement('div', { style: { width: '100%' } },
                                React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 } },
                                    React.createElement('span', { style: { fontSize: 32 } }, item.icon),
                                    React.createElement('div', null,
                                        React.createElement('div', { style: { fontWeight: 'bold', color: item.color } }, item.name)
                                    ),
                                    React.createElement(Tag, { color: item.color }, '能量: ' + item.energy)
                                ),
                                React.createElement('div', { style: { fontSize: 13, color: '#666', paddingLeft: 44 } }, item.desc)
                            )
                        )
                    }),
                    React.createElement(Divider, null),
                    React.createElement('h4', { style: { marginBottom: 16 } }, '六维评分系统'),
                    React.createElement(Row, { gutter: [8, 8] },
                        [
                            { name: '相关性', weight: '30%', color: '#1890ff' },
                            { name: '频率', weight: '24%', color: '#52c41a' },
                            { name: '时效性', weight: '15%', color: '#faad14' },
                            { name: '多样性', weight: '15%', color: '#722ed1' },
                            { name: '整合度', weight: '10%', color: '#eb2f96' },
                            { name: '概念丰富度', weight: '6%', color: '#13c2c2' }
                        ].map(item =>
                            React.createElement(Col, { span: 8, key: item.name },
                                React.createElement(Card, { size: 'small', style: { textAlign: 'center' } },
                                    React.createElement('div', { style: { color: item.color, fontWeight: 'bold' } }, item.weight),
                                    React.createElement('div', { style: { fontSize: 12 } }, item.name)
                                )
                            )
                        )
                    )
                );
            };

            const tabItems = [
                { key: 'status', label: '🌙 睡眠状态', children: renderStatus() },
                { key: 'config', label: '⚙️ 参数配置', children: renderConfig() },
                { key: 'energy', label: '📖 功能说明', children: renderEnergy() }
            ];

            return React.createElement('div', { style: { height: '100%', display: 'flex', flexDirection: 'column' } },
                // 标题栏 - 使用原生CSS类
                React.createElement('div', { className: 'ht-page-header' },
                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } },
                        React.createElement('span', { style: { fontSize: '20px' } }, '🌙'),
                        React.createElement('div', null,
                            React.createElement('div', { className: 'ht-page-title' }, 'HumanThinking 睡眠管理'),
                            React.createElement('div', { className: 'ht-page-subtitle' }, 'Agent睡眠周期与记忆整合')
                        )
                    ),
                    React.createElement(AgentInfoBar)
                ),
                // 内容区域 - 使用原生CSS类
                React.createElement('div', { className: 'ht-content' },
                    React.createElement(Tabs, {
                        items: tabItems,
                        activeKey: activeTab,
                        onChange: setActiveTab
                    })
                )
            );
        };

        return { MemoryManagementSidebar, SleepManagementSidebar };
    };

    // 初始化
    const init = async () => {
        try {
            await waitForDependencies();
            console.log('[HumanThinking] 依赖已加载，开始注册...');

            const { MemoryManagementSidebar, SleepManagementSidebar } = createComponents();

            if (window.QwenPaw?.registerRoutes) {
                window.QwenPaw.registerRoutes(PLUGIN_ID, [
                    {
                        path: '/humanthinking/memory',
                        component: MemoryManagementSidebar,
                        label: '记忆管理',
                        icon: '🧠',
                        priority: 10
                    },
                    {
                        path: '/humanthinking/sleep',
                        component: SleepManagementSidebar,
                        label: '睡眠管理',
                        icon: '🌙',
                        priority: 20
                    }
                ]);
                console.log('[HumanThinking] ✓ 路由注册成功');
            } else {
                console.error('[HumanThinking] ✗ window.QwenPaw.registerRoutes 不可用');
            }

            console.log('[HumanThinking] ✓ 前端插件加载完成');

            // 注入记忆管理器下拉菜单选项和HT配置tab
            injectMemoryManagerDropdown();
        } catch (err) {
            console.error('[HumanThinking] 初始化失败:', err);
        }

        // 暴露全局API供调试和外部调用（无论初始化是否成功）
        window.HumanThinkingAPI = {
            showHTConfigTab: showHTConfigTab,
            hideHTConfigTab: hideHTConfigTab,
            checkAndShowHTTab: checkAndShowHTTab,
            addHumanThinkingOption: addHumanThinkingOption,
            injectDropdownOption: injectDropdownOption
        };
        console.log('[HumanThinking] ✓ 全局API已暴露: window.HumanThinkingAPI');

        // 尝试动态修改 MEMORY_MANAGER_BACKEND_MAPPINGS
        injectBackendMapping();
    };

    // 动态修改 MEMORY_MANAGER_BACKEND_MAPPINGS 以支持 human_thinking
    function injectBackendMapping() {
        try {
            // 查找 QwenPaw 的模块系统
            const modules = window.QwenPaw?.modules;
            if (!modules) {
                console.log('[HumanThinking] QwenPaw modules not found, trying alternative approach');
                return;
            }

            // 查找 backendMappings 模块
            for (const [key, mod] of Object.entries(modules)) {
                if (key.includes('backendMappings') || key.includes('constants')) {
                    console.log('[HumanThinking] Found potential backendMappings module:', key);
                    if (mod.MEMORY_MANAGER_BACKEND_MAPPINGS) {
                        mod.MEMORY_MANAGER_BACKEND_MAPPINGS['human_thinking'] = {
                            configField: 'human_thinking_config',
                            component: HTMemoryConfigComponent,
                            label: 'human_thinking',
                            tabKey: 'htMemoryConfig'
                        };
                        console.log('[HumanThinking] ✓ Added human_thinking to MEMORY_MANAGER_BACKEND_MAPPINGS');
                    }
                }
            }
        } catch (e) {
            console.error('[HumanThinking] Failed to inject backend mapping:', e);
        }
    }

    // HT 记忆配置组件
    function HTMemoryConfigComponent() {
        const baseUrl = getApiBase();
        const token = window.QwenPaw?.host?.getApiToken?.() || '';
        const [config, setConfig] = React.useState({
            enable_cross_session: true,
            enable_emotion: true,
            session_idle_timeout: 180,
            max_memory_chars: 150,
            max_results: 5,
            frozen_days: 30,
            archive_days: 90,
            delete_days: 180,
        });
        const [loading, setLoading] = React.useState(true);
        const [saving, setSaving] = React.useState(false);

        React.useEffect(() => {
            fetch(`${baseUrl}/config`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            .then(res => res.json())
            .then(data => {
                setConfig(prev => ({ ...prev, ...data }));
                setLoading(false);
            })
            .catch(err => {
                console.error('[HumanThinking] Failed to load config:', err);
                setLoading(false);
            });
        }, []);

        const handleSave = () => {
            setSaving(true);
            fetch(`${baseUrl}/config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(config)
            })
            .then(res => res.json())
            .then(() => {
                setSaving(false);
                alert('配置保存成功');
            })
            .catch(err => {
                console.error('[HumanThinking] Failed to save config:', err);
                setSaving(false);
                alert('配置保存失败');
            });
        };

        const updateConfig = (key, value) => {
            setConfig(prev => ({ ...prev, [key]: value }));
        };

        if (loading) {
            return React.createElement('div', { style: { padding: '40px', textAlign: 'center' } }, '加载中...');
        }

        return React.createElement('div', { style: { padding: '16px' } },
            React.createElement('h3', { style: { marginBottom: '16px' } }, '🧠 HumanThinking 记忆配置'),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, '跨会话记忆'),
                React.createElement('input', {
                    type: 'checkbox',
                    checked: config.enable_cross_session,
                    onChange: (e) => updateConfig('enable_cross_session', e.target.checked),
                    style: { marginRight: '8px' }
                }),
                React.createElement('span', null, '启用跨会话记忆保持')
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, '情感跟踪'),
                React.createElement('input', {
                    type: 'checkbox',
                    checked: config.enable_emotion,
                    onChange: (e) => updateConfig('enable_emotion', e.target.checked),
                    style: { marginRight: '8px' }
                }),
                React.createElement('span', null, '启用情感状态计算')
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, '分布式数据库'),
                React.createElement('input', {
                    type: 'checkbox',
                    checked: config.distributed_db || false,
                    onChange: (e) => updateConfig('distributed_db', e.target.checked),
                    style: { marginRight: '8px' }
                }),
                React.createElement('span', null, '启用分布式数据库（开启后不可关闭）')
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, `会话空闲超时: ${config.session_idle_timeout}秒`),
                React.createElement('input', {
                    type: 'range',
                    min: 60,
                    max: 600,
                    value: config.session_idle_timeout,
                    onChange: (e) => updateConfig('session_idle_timeout', parseInt(e.target.value)),
                    style: { width: '100%' }
                })
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, `单条记忆最大字符数: ${config.max_memory_chars}字符`),
                React.createElement('input', {
                    type: 'range',
                    min: 100,
                    max: 500,
                    value: config.max_memory_chars,
                    onChange: (e) => updateConfig('max_memory_chars', parseInt(e.target.value)),
                    style: { width: '100%' }
                })
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, `搜索限制: ${config.max_results}条记录`),
                React.createElement('input', {
                    type: 'range',
                    min: 5,
                    max: 50,
                    value: config.max_results,
                    onChange: (e) => updateConfig('max_results', parseInt(e.target.value)),
                    style: { width: '100%' }
                })
            ),
            React.createElement('div', { style: { marginBottom: '16px', borderTop: '1px solid #eae9e7', paddingTop: '16px' } },
                React.createElement('h4', { style: { marginBottom: '12px' } }, '记忆生命周期'),
                React.createElement('div', { style: { marginBottom: '12px' } },
                    React.createElement('label', { style: { display: 'block', marginBottom: '4px' } }, `冷藏天数: ${config.frozen_days}天`),
                    React.createElement('input', {
                        type: 'range',
                        min: 7,
                        max: 90,
                        value: config.frozen_days,
                        onChange: (e) => updateConfig('frozen_days', parseInt(e.target.value)),
                        style: { width: '100%' }
                    })
                ),
                React.createElement('div', { style: { marginBottom: '12px' } },
                    React.createElement('label', { style: { display: 'block', marginBottom: '4px' } }, `归档天数: ${config.archive_days}天`),
                    React.createElement('input', {
                        type: 'range',
                        min: 30,
                        max: 365,
                        value: config.archive_days,
                        onChange: (e) => updateConfig('archive_days', parseInt(e.target.value)),
                        style: { width: '100%' }
                    })
                ),
                React.createElement('div', { style: { marginBottom: '12px' } },
                    React.createElement('label', { style: { display: 'block', marginBottom: '4px' } }, `删除天数: ${config.delete_days}天`),
                    React.createElement('input', {
                        type: 'range',
                        min: 90,
                        max: 730,
                        value: config.delete_days,
                        onChange: (e) => updateConfig('delete_days', parseInt(e.target.value)),
                        style: { width: '100%' }
                    })
                )
            ),
            React.createElement('div', { style: { marginTop: '24px' } },
                React.createElement('button', {
                    onClick: handleSave,
                    disabled: saving,
                    style: {
                        padding: '8px 24px',
                        background: '#1890ff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer'
                    }
                }, saving ? '保存中...' : '保存配置')
            )
        );
    }

    // 注入记忆管理器下拉菜单选项和HT配置tab
    function injectMemoryManagerDropdown() {
        console.log('[HumanThinking] 开始注入记忆管理器下拉菜单...');

        // 等待页面加载完成
        const startInject = () => {
            // 1. 向下拉菜单添加 human_thinking 选项
            addHumanThinkingOption();

            // 2. 监听下拉菜单变化，动态添加HT配置tab
            watchMemoryBackendChange();

            // 3. 定期检查和修复（防止页面重新渲染后丢失）
            setInterval(() => {
                addHumanThinkingOption();
                checkAndShowHTTab();
            }, 2000);
        };

        // 延迟执行，确保QwenPaw页面已渲染
        setTimeout(startInject, 3000);

        // 自动测试：页面加载后10秒自动显示HT tab（用于验证功能）
        setTimeout(() => {
            console.log('[HumanThinking] Auto-test: calling showHTConfigTab');
            showHTConfigTab();
        }, 10000);
    }

    // 向下拉菜单添加 human_thinking 选项
    function addHumanThinkingOption() {
        try {
            // 查找所有Select组件，找到记忆管理器后端下拉框
            const allSelects = document.querySelectorAll('.ant-select');
            let targetSelect = null;

            for (const select of allSelects) {
                const parent = select.closest('.ant-form-item');
                if (parent) {
                    const label = parent.textContent || '';
                    if (label.includes('记忆管理') || label.includes('Memory Manager') || label.includes('memory_manager_backend')) {
                        targetSelect = select;
                        break;
                    }
                }
            }

            if (!targetSelect) {
                const inputs = document.querySelectorAll('input[name="memory_manager_backend"]');
                if (inputs.length > 0) {
                    targetSelect = inputs[0].closest('.ant-select');
                }
            }

            if (!targetSelect) return;

            // 检查是否已经添加过（通过标记）
            if (targetSelect.dataset.htInjected === 'true') return;

            // 标记已注入
            targetSelect.dataset.htInjected = 'true';

            // 监听下拉框点击事件，在打开时注入选项
            const trigger = targetSelect.querySelector('.ant-select-selector');
            if (trigger) {
                trigger.addEventListener('click', function() {
                    setTimeout(injectDropdownOption, 100);
                });
                trigger.addEventListener('mousedown', function() {
                    setTimeout(injectDropdownOption, 100);
                });
            }

            // 也监听键盘事件
            targetSelect.addEventListener('keydown', function() {
                setTimeout(injectDropdownOption, 100);
            });

            console.log('[HumanThinking] ✓ 已绑定下拉框事件');
        } catch (e) {
            console.error('[HumanThinking] 添加下拉选项失败:', e);
        }
    }

    // 实际注入下拉选项到打开的列表中
    function injectDropdownOption() {
        try {
            const dropdown = document.querySelector('.ant-select-dropdown:not([style*="display: none"]):not([style*="display:none"])');
            if (!dropdown) return;

            const list = dropdown.querySelector('.rc-virtual-list-holder-inner');
            if (!list) return;

            // 检查是否已有 human_thinking 选项
            const existingOptions = list.querySelectorAll('.ant-select-item-option-content');
            for (const opt of existingOptions) {
                if (opt.textContent === 'human_thinking') return;
            }

            // 创建新的选项元素
            const newOption = document.createElement('div');
            newOption.className = 'ant-select-item ant-select-item-option';
            newOption.setAttribute('data-value', 'human_thinking');
            newOption.setAttribute('title', 'human_thinking');
            newOption.setAttribute('aria-selected', 'false');
            newOption.innerHTML = '<div class="ant-select-item-option-content">human_thinking</div>';

            // 点击事件 - 选择此选项
            newOption.addEventListener('click', function(e) {
                e.stopPropagation();
                e.preventDefault();

                // 找到对应的select
                const allSelects = document.querySelectorAll('.ant-select');
                let targetSelect = null;
                for (const select of allSelects) {
                    const parent = select.closest('.ant-form-item');
                    if (parent) {
                        const label = parent.textContent || '';
                        if (label.includes('记忆管理') || label.includes('Memory Manager')) {
                            targetSelect = select;
                            break;
                        }
                    }
                }

                if (targetSelect) {
                    // 更新显示文本
                    const titleEl = targetSelect.querySelector('.ant-select-selection-item');
                    if (titleEl) {
                        titleEl.textContent = 'human_thinking';
                        titleEl.setAttribute('title', 'human_thinking');
                    }

                    // 更新input值
                    const input = targetSelect.querySelector('input.ant-select-selection-search-input');
                    if (input) {
                        input.value = 'human_thinking';
                        // 触发React onChange
                        const tracker = input._valueTracker;
                        if (tracker) {
                            tracker.setValue('');
                        }
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('blur', { bubbles: true }));
                    }

                    // 更新aria属性
                    targetSelect.setAttribute('aria-activedescendant', '');
                }

                // 关闭下拉框
                document.body.click();

                // 触发HT tab显示
                setTimeout(showHTConfigTab, 200);

                console.log('[HumanThinking] ✓ 已选择 human_thinking');
            });

            // 鼠标悬停效果
            newOption.addEventListener('mouseenter', function() {
                this.classList.add('ant-select-item-option-active');
            });
            newOption.addEventListener('mouseleave', function() {
                this.classList.remove('ant-select-item-option-active');
            });

            list.appendChild(newOption);
            console.log('[HumanThinking] ✓ 已添加 human_thinking 下拉选项');
        } catch (e) {
            console.error('[HumanThinking] 注入下拉选项失败:', e);
        }
    }

    // 监听记忆管理后端选择变化
    function watchMemoryBackendChange() {
        // 使用MutationObserver监听页面变化
        const observer = new MutationObserver((mutations) => {
            checkAndShowHTTab();
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['value', 'class', 'textContent']
        });

        // 同时定期检查
        setInterval(checkAndShowHTTab, 1000);
    }

    // 检查并显示HT配置tab
    function checkAndShowHTTab() {
        try {
            let currentValue = '';

            // 方法1: 通过input的value
            const inputs = document.querySelectorAll('input[name="memory_manager_backend"]');
            for (const input of inputs) {
                if (input.value) {
                    currentValue = input.value;
                    break;
                }
            }

            // 方法2: 通过显示文本
            if (!currentValue) {
                const selects = document.querySelectorAll('.ant-select');
                for (const select of selects) {
                    const parent = select.closest('.ant-form-item');
                    if (parent) {
                        const label = parent.textContent || '';
                        if (label.includes('记忆管理') || label.includes('Memory Manager')) {
                            const title = select.querySelector('.ant-select-selection-item');
                            if (title) {
                                const text = title.textContent.trim();
                                if (text === 'human_thinking') {
                                    currentValue = 'human_thinking';
                                    break;
                                }
                            }
                        }
                    }
                }
            }

            // 方法3: 通过aria-label或title
            if (!currentValue) {
                const selects = document.querySelectorAll('.ant-select');
                for (const select of selects) {
                    const parent = select.closest('.ant-form-item');
                    if (parent) {
                        const label = parent.textContent || '';
                        if (label.includes('记忆管理') || label.includes('Memory Manager')) {
                            const title = select.querySelector('.ant-select-selection-item');
                            if (title) {
                                const text = title.getAttribute('title') || title.textContent.trim();
                                if (text === 'human_thinking') {
                                    currentValue = 'human_thinking';
                                    break;
                                }
                            }
                        }
                    }
                }
            }

            if (currentValue === 'human_thinking') {
                console.log('[HumanThinking] Detected human_thinking, showing HT tab');
                showHTConfigTab();
            } else {
                hideHTConfigTab();
            }
        } catch (e) {
            console.error('[HumanThinking] checkAndShowHTTab error:', e);
        }
    }

    // HT配置tab的容器
    let htTabContainer = null;
    let htTabBtn = null;

    // 显示HT配置tab
    function showHTConfigTab() {
        console.log('[HumanThinking] showHTConfigTab called');
        try {
            // 如果已经存在，显示即可
            if (htTabContainer && htTabBtn) {
                console.log('[HumanThinking] HT tab already exists, showing');
                htTabBtn.style.display = 'inline-flex';
                htTabContainer.style.display = 'block';
                return;
            }

            // 查找Tabs容器
            const tabsNav = document.querySelector('.ant-tabs-nav');
            const tabsContent = document.querySelector('.ant-tabs-content-holder');
            console.log('[HumanThinking] tabsNav found:', !!tabsNav, 'tabsContent found:', !!tabsContent);
            if (!tabsNav || !tabsContent) {
                console.log('[HumanThinking] 未找到Tabs容器');
                return;
            }

            // 创建HT Tab按钮
            htTabBtn = document.createElement('div');
            htTabBtn.className = 'ant-tabs-tab';
            htTabBtn.setAttribute('data-node-key', 'htMemoryConfig');
            htTabBtn.innerHTML = '<div class="ant-tabs-tab-btn" role="tab" aria-selected="false" tabindex="-1">HT记忆配置</div>';

            // 添加到tab列表（在"长期记忆"tab之后）
            const tabList = tabsNav.querySelector('.ant-tabs-nav-list');
            const allTabs = tabsNav.querySelectorAll('.ant-tabs-tab');
            console.log('[HumanThinking] tabList found:', !!tabList, 'allTabs count:', allTabs.length);

            let inserted = false;
            for (let i = 0; i < allTabs.length; i++) {
                const tabText = allTabs[i].textContent || '';
                if (tabText.includes('长期记忆')) {
                    if (allTabs[i + 1] && tabList) {
                        tabList.insertBefore(htTabBtn, allTabs[i + 1]);
                        inserted = true;
                        console.log('[HumanThinking] ✓ HT tab inserted after 长期记忆');
                        break;
                    }
                }
            }
            if (!inserted && tabList) {
                tabList.appendChild(htTabBtn);
                console.log('[HumanThinking] ✓ HT tab appended to list');
            }

            // 创建HT配置内容面板
            htTabContainer = document.createElement('div');
            htTabContainer.className = 'ant-tabs-tabpane ant-tabs-tabpane-active';
            htTabContainer.setAttribute('role', 'tabpanel');
            htTabContainer.setAttribute('tabindex', '-1');
            htTabContainer.style.cssText = 'padding: 16px;';

            // 渲染HT配置内容
            renderHTConfigContent(htTabContainer);

            // 添加到tab内容区
            tabsContent.appendChild(htTabContainer);

            // Tab点击事件
            htTabBtn.addEventListener('click', function() {
                // 隐藏所有tab内容
                const allPanes = tabsContent.querySelectorAll('.ant-tabs-tabpane');
                for (const pane of allPanes) {
                    pane.style.display = 'none';
                    pane.classList.remove('ant-tabs-tabpane-active');
                }
                // 显示HT内容
                htTabContainer.style.display = 'block';
                htTabContainer.classList.add('ant-tabs-tabpane-active');

                // 更新tab样式
                const allTabEls = tabsNav.querySelectorAll('.ant-tabs-tab');
                for (const tab of allTabEls) {
                    tab.classList.remove('ant-tabs-tab-active');
                    tab.setAttribute('aria-selected', 'false');
                }
                htTabBtn.classList.add('ant-tabs-tab-active');
                htTabBtn.setAttribute('aria-selected', 'true');
            });

            console.log('[HumanThinking] ✓ HT记忆配置tab已创建');
        } catch (err) {
            console.error('[HumanThinking] showHTConfigTab error:', err);
        }
    }

    // 隐藏HT配置tab
    function hideHTConfigTab() {
        if (htTabContainer) {
            htTabContainer.style.display = 'none';
        }
        if (htTabBtn) {
            htTabBtn.style.display = 'none';
        }
    }

    // 渲染HT配置内容
    function renderHTConfigContent(container) {
        const baseUrl = getApiBase();
        const token = window.QwenPaw?.host?.getApiToken?.() || '';

        container.innerHTML = `
            <div style="padding: 16px;">
                <h3 style="margin-bottom: 16px;">🧠 HumanThinking 记忆配置</h3>
                <div id="ht-config-loading" style="text-align: center; padding: 40px;">
                    加载中...
                </div>
                <div id="ht-config-content" style="display: none;">
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">跨会话记忆</label>
                        <input type="checkbox" id="ht-cross-session" checked style="margin-right: 8px;">
                        <span>启用跨会话记忆保持</span>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">情感跟踪</label>
                        <input type="checkbox" id="ht-emotion" checked style="margin-right: 8px;">
                        <span>启用情感状态计算</span>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">会话空闲超时（秒）</label>
                        <input type="range" id="ht-timeout" min="60" max="600" value="180" style="width: 100%;">
                        <span id="ht-timeout-value">180</span>秒
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">单条记忆最大字符数</label>
                        <input type="range" id="ht-max-chars" min="100" max="500" value="150" style="width: 100%;">
                        <span id="ht-max-chars-value">150</span>字符
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">搜索限制（条）</label>
                        <input type="range" id="ht-max-results" min="5" max="50" value="5" style="width: 100%;">
                        <span id="ht-max-results-value">5</span>条
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">冷藏天数</label>
                        <input type="range" id="ht-frozen-days" min="7" max="90" value="30" style="width: 100%;">
                        <span id="ht-frozen-days-value">30</span>天
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">归档天数</label>
                        <input type="range" id="ht-archive-days" min="30" max="365" value="90" style="width: 100%;">
                        <span id="ht-archive-days-value">90</span>天
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">删除天数</label>
                        <input type="range" id="ht-delete-days" min="90" max="730" value="180" style="width: 100%;">
                        <span id="ht-delete-days-value">180</span>天
                    </div>
                    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eae9e7;">
                        <button id="ht-save-config" style="padding: 8px 24px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            保存配置
                        </button>
                        <span id="ht-save-status" style="margin-left: 16px; color: #52c41a;"></span>
                    </div>
                </div>
            </div>
        `;

        // 绑定range输入事件
        const ranges = ['timeout', 'max-chars', 'max-results', 'frozen-days', 'archive-days', 'delete-days'];
        for (const id of ranges) {
            const input = container.querySelector(`#ht-${id}`);
            const display = container.querySelector(`#ht-${id}-value`);
            if (input && display) {
                input.addEventListener('input', function() {
                    display.textContent = this.value;
                });
            }
        }

        // 加载配置
        loadHTConfig(container, baseUrl, token);

        // 保存按钮事件
        const saveBtn = container.querySelector('#ht-save-config');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                saveHTConfig(container, baseUrl, token);
            });
        }
    }

    // 加载HT配置
    function loadHTConfig(container, apiBase, token) {
        fetch(`${apiBase}/config`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.json())
        .then(data => {
            const contentDiv = container.querySelector('#ht-config-content');
            const loadingDiv = container.querySelector('#ht-config-loading');
            if (contentDiv) contentDiv.style.display = 'block';
            if (loadingDiv) loadingDiv.style.display = 'none';

            // 设置表单值
            const crossSession = container.querySelector('#ht-cross-session');
            const emotion = container.querySelector('#ht-emotion');
            const timeout = container.querySelector('#ht-timeout');
            const maxChars = container.querySelector('#ht-max-chars');
            const maxResults = container.querySelector('#ht-max-results');
            const frozenDays = container.querySelector('#ht-frozen-days');
            const archiveDays = container.querySelector('#ht-archive-days');
            const deleteDays = container.querySelector('#ht-delete-days');

            if (crossSession) crossSession.checked = data.enable_cross_session !== false;
            if (emotion) emotion.checked = data.enable_emotion !== false;
            if (timeout) { timeout.value = data.session_idle_timeout || 180; container.querySelector('#ht-timeout-value').textContent = timeout.value; }
            if (maxChars) { maxChars.value = data.max_memory_chars || 150; container.querySelector('#ht-max-chars-value').textContent = maxChars.value; }
            if (maxResults) { maxResults.value = data.max_results || 5; container.querySelector('#ht-max-results-value').textContent = maxResults.value; }
            if (frozenDays) { frozenDays.value = data.frozen_days || 30; container.querySelector('#ht-frozen-days-value').textContent = frozenDays.value; }
            if (archiveDays) { archiveDays.value = data.archive_days || 90; container.querySelector('#ht-archive-days-value').textContent = archiveDays.value; }
            if (deleteDays) { deleteDays.value = data.delete_days || 180; container.querySelector('#ht-delete-days-value').textContent = deleteDays.value; }
        })
        .catch(err => {
            console.error('[HumanThinking] 加载配置失败:', err);
            const loadingDiv = container.querySelector('#ht-config-loading');
            if (loadingDiv) loadingDiv.innerHTML = '加载失败，使用默认配置';
            const contentDiv = container.querySelector('#ht-config-content');
            if (contentDiv) contentDiv.style.display = 'block';
        });
    }

    // 保存HT配置
    function saveHTConfig(container, apiBase, token) {
        const config = {
            enable_cross_session: container.querySelector('#ht-cross-session')?.checked ?? true,
            enable_emotion: container.querySelector('#ht-emotion')?.checked ?? true,
            session_idle_timeout: parseInt(container.querySelector('#ht-timeout')?.value || '180'),
            max_memory_chars: parseInt(container.querySelector('#ht-max-chars')?.value || '150'),
            max_results: parseInt(container.querySelector('#ht-max-results')?.value || '5'),
            frozen_days: parseInt(container.querySelector('#ht-frozen-days')?.value || '30'),
            archive_days: parseInt(container.querySelector('#ht-archive-days')?.value || '90'),
            delete_days: parseInt(container.querySelector('#ht-delete-days')?.value || '180'),
        };

        fetch(`${apiBase}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(config)
        })
        .then(res => res.json())
        .then(data => {
            const status = container.querySelector('#ht-save-status');
            if (status) {
                status.textContent = '✓ 保存成功';
                setTimeout(() => { status.textContent = ''; }, 3000);
            }
        })
        .catch(err => {
            console.error('[HumanThinking] 保存配置失败:', err);
            const status = container.querySelector('#ht-save-status');
            if (status) {
                status.textContent = '✗ 保存失败';
                status.style.color = '#ff4d4f';
                setTimeout(() => { status.textContent = ''; status.style.color = '#52c41a'; }, 3000);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
