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
                return {
                    agent_id: agentId,
                    agent_name: data.state?.agents?.[agentId]?.name || '未命名Agent'
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
                React.createElement('span', null, '当前智能体:'),
                React.createElement('span', { style: { fontWeight: 600 } }, agent.agent_name),
                React.createElement('span', { style: { marginLeft: 4, fontSize: '12px', opacity: 0.6 } }, `(${agent.agent_id})`)
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
                    // 分布式数据库开关 - 开启后无法关闭（强制启用）
                    React.createElement('div', { style: { marginBottom: 16 } },
                        React.createElement('label', { style: { display: 'block', marginBottom: 8 } }, '分布式数据库'),
                        React.createElement(Switch, {
                            checked: true,
                            disabled: true,
                            checkedChildren: '已启用',
                            unCheckedChildren: '已禁用'
                        }),
                        React.createElement('div', { style: { fontSize: 12, color: '#999', marginTop: 4 } }, '分布式数据库已强制启用，不可关闭')
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
                { key: 'config', label: '⚙️ 配置信息', children: renderConfig() }
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
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
