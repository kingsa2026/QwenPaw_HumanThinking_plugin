/**
 * HumanThinking 插件前端入口 - 简化可靠版
 */

(function() {
    'use strict';

    console.log('[HumanThinking] 前端插件加载中...');

    const PLUGIN_ID = 'humanthinking';

    // 注入原生风格CSS - 使用QwenPaw原生变量和类名
    const injectNativeStyles = () => {
        if (document.getElementById('humanthinking-native-styles')) return;
        const style = document.createElement('style');
        style.id = 'humanthinking-native-styles';
        style.textContent = `
            /* HumanThinking 原生风格CSS - 与QwenPaw Console保持一致 */
            .ht-page-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
                padding: 20px;
                border-bottom: 1px solid var(--color-border-secondary, #eae8e7);
                flex-shrink: 0;
            }
            .dark-mode .ht-page-header {
                border-bottom-color: rgba(255, 255, 255, 0.12);
            }
            .ht-page-title {
                font-size: 20px;
                font-weight: 600;
                color: var(--colorText, rgba(0, 0, 0, 0.88));
                line-height: 1.4;
            }
            .dark-mode .ht-page-title {
                color: rgba(255, 255, 255, 0.85);
            }
            .ht-page-subtitle {
                font-size: 13px;
                color: var(--colorTextSecondary, rgba(0, 0, 0, 0.45));
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
                border-top: 1px solid var(--color-border-secondary, #eae8e7);
                padding-top: 16px;
                margin-top: 8px;
            }
            .dark-mode .ht-form-actions {
                border-top-color: rgba(255, 255, 255, 0.12);
            }
            /* 使用qwenpaw-card样式的卡片 */
            .ht-card {
                background: var(--color-bg-base, #ffffff);
                border-radius: var(--border-radius, 8px);
                border: 1px solid var(--color-border-secondary, #eae8e7);
                padding: 16px;
            }
            .dark-mode .ht-card {
                background: rgba(255, 255, 255, 0.04);
                border-color: rgba(255, 255, 255, 0.12);
            }
            .ht-stat-card {
                background: var(--color-bg-base, #ffffff);
                border-radius: var(--border-radius, 8px);
                border: 1px solid var(--color-border-secondary, #eae8e7);
                padding: 16px;
                transition: all 0.3s;
            }
            .ht-stat-card:hover {
                border-color: #ff7f16;
                box-shadow: 0 12px 32px rgba(0,0,0,0.08);
            }
            .dark-mode .ht-stat-card {
                background: rgba(255, 255, 255, 0.04);
                border-color: rgba(255, 255, 255, 0.12);
            }
            .dark-mode .ht-stat-card:hover {
                border-color: #ff7f16;
            }
            .ht-divider {
                border: none;
                border-top: 1px solid var(--color-border-secondary, #eae8e7);
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
            .ht-status-light img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            /* 统一列表项样式 - 使用原生变量 */
            .ht-list-item {
                background: var(--color-bg-base, #ffffff);
                border-radius: var(--border-radius, 8px);
                margin-bottom: 8px;
                padding: 12px 16px;
                border: 1px solid var(--color-border, #d9d9d9);
                transition: all 0.3s;
            }
            .ht-list-item:hover {
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                border-color: #ff7f16;
            }
            .dark-mode .ht-list-item {
                background: rgba(255, 255, 255, 0.04);
                border-color: rgba(255, 255, 255, 0.12);
            }
            /* 统一卡片标题样式 */
            .ht-section-card .ant-card-head {
                background: #fafafa;
                border-bottom: 1px solid var(--color-border, #d9d9d9);
            }
            .dark-mode .ht-section-card .ant-card-head {
                background: rgba(255, 255, 255, 0.04);
                border-bottom-color: rgba(255, 255, 255, 0.12);
            }
            /* Tab 样式优化 - 与qwenpaw-tabs保持一致 */
            .ht-tabs .ant-tabs-nav {
                margin-bottom: 16px;
            }
            .ht-tabs .ant-tabs-tab {
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            .ht-tabs .ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn {
                color: #ff7f16 !important;
                font-weight: 600;
            }
            .ht-tabs .ant-tabs-ink-bar {
                background: #ff7f16 !important;
                height: 3px;
                border-radius: 2px;
            }
            /* 配置项标签样式 */
            .ht-config-label {
                font-weight: 500;
                color: var(--colorText, rgba(0, 0, 0, 0.88));
                font-size: 14px;
            }
            .dark-mode .ht-config-label {
                color: rgba(255, 255, 255, 0.85);
            }
            .ht-config-desc {
                font-size: 12px;
                color: var(--colorTextSecondary, rgba(0, 0, 0, 0.45));
                margin-top: 4px;
            }
            .dark-mode .ht-config-desc {
                color: rgba(255, 255, 255, 0.45);
            }
            /* 滑块样式 */
            .ht-slider .ant-slider-track {
                background: #ff7f16;
            }
            .ht-slider .ant-slider-handle {
                border-color: #ff7f16;
            }
            /* 按钮样式 - 与qwenpaw-btn保持一致 */
            .ht-btn-primary {
                background: #ff7f16;
                border-color: #ff7f16;
            }
            .ht-btn-primary:hover {
                background: #f07e26;
                border-color: #f07e26;
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

    // ==================== 多语言支持（优化版） ====================
    const getCurrentLanguage = () => {
        // 从localStorage获取语言设置（与QwenPaw一致）
        const lang = localStorage.getItem('language') || 'en';
        // 支持 zh, en, ja, ru
        if (lang.startsWith('zh')) return 'zh';
        if (lang.startsWith('ja')) return 'ja';
        if (lang.startsWith('ru')) return 'ru';
        return 'en';
    };

    // 加载语言包
    const loadTranslations = async () => {
        const lang = getCurrentLanguage();
        try {
            const response = await fetch(`/api/plugins/humanthinking/files/locales/${lang}.json?v=${Date.now()}`);
            if (response.ok) {
                const data = await response.json();
                console.log('[HumanThinking] Translations loaded:', lang);
                return data;
            }
        } catch (e) {
            console.warn('[HumanThinking] Failed to load translations:', e);
        }
        // 回退到默认语言
        return {
            plugin: { name: 'Human Thinking', description: 'Memory Management Plugin' },
            nav: { memory: 'Memory', sleep: 'Sleep', stats: 'Stats', search: 'Search', emotion: 'Emotion', timeline: 'Timeline', config: 'Config', about: 'About' },
            common: { save: 'Save', cancel: 'Cancel', confirm: 'Confirm', delete: 'Delete', edit: 'Edit', create: 'Create', refresh: 'Refresh', loading: 'Loading...', success: 'Success', error: 'Error', close: 'Close' }
        };
    };

    // 翻译函数（支持插值 {key}）
    let translations = null;
    const t = (key, defaultValue = '', params = {}) => {
        if (!translations) {
            let result = defaultValue || key;
            Object.keys(params).forEach(k => {
                result = result.replace(new RegExp(`{${k}}`, 'g'), params[k]);
            });
            return result;
        }
        const keys = key.split('.');
        let value = translations;
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                let result = defaultValue || key;
                Object.keys(params).forEach(pk => {
                    result = result.replace(new RegExp(`{${pk}}`, 'g'), params[pk]);
                });
                return result;
            }
        }
        let result = typeof value === 'string' ? value : (defaultValue || key);
        Object.keys(params).forEach(k => {
            result = result.replace(new RegExp(`{${k}}`, 'g'), params[k]);
        });
        return result;
    };

    // 全局语言状态管理
    let currentLang = getCurrentLanguage();
    const langListeners = new Set();

    const subscribeLang = (callback) => {
        langListeners.add(callback);
        return () => langListeners.delete(callback);
    };

    const notifyLangChange = (newLang) => {
        currentLang = newLang;
        langListeners.forEach(cb => cb(newLang));
    };

    // 监听语言变化（跨标签页）
    window.addEventListener('storage', (e) => {
        if (e.key === 'language') {
            const rawLang = e.newValue || 'en';
            let newLang = 'en';
            if (rawLang.startsWith('zh')) newLang = 'zh';
            else if (rawLang.startsWith('ja')) newLang = 'ja';
            else if (rawLang.startsWith('ru')) newLang = 'ru';
            console.log('[HumanThinking] Language changed to:', newLang);
            loadTranslations().then(data => {
                translations = data;
                notifyLangChange(newLang);
                if (typeof resetHtInjectedMarkers === 'function') resetHtInjectedMarkers();
            });
        }
    });

    // 轮询检测语言变化（同一标签页内）
    setInterval(() => {
        const detectedLang = getCurrentLanguage();
        if (detectedLang !== currentLang) {
            console.log('[HumanThinking] Language detected change:', detectedLang);
            loadTranslations().then(data => {
                translations = data;
                notifyLangChange(detectedLang);
                if (typeof resetHtInjectedMarkers === 'function') resetHtInjectedMarkers();
            });
        }
    }, 500);

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

    // ==================== Agent 隔离支持（优化版） ====================
    // 获取当前Agent信息（支持 qwenpaw-last-used-agent 和 storage 轮询）
    const getCurrentAgent = () => {
        try {
            // 优先读取 qwenpaw-last-used-agent（QwenPaw 官方存储 key）
            const qwLastUsed = localStorage.getItem('qwenpaw-last-used-agent');
            if (qwLastUsed) {
                // 尝试从 agent storage 获取名称
                let agentStorage = sessionStorage.getItem('qwenpaw-agent-storage');
                if (!agentStorage) {
                    agentStorage = localStorage.getItem('qwenpaw-agent-storage');
                }
                let agentName = '';
                if (agentStorage) {
                    const data = JSON.parse(agentStorage);
                    const agents = data.state?.agents;
                    if (Array.isArray(agents)) {
                        const found = agents.find(a => a.id === qwLastUsed || a.agent_id === qwLastUsed);
                        agentName = found?.name || found?.agent_name || '';
                    } else if (agents && typeof agents === 'object') {
                        agentName = agents[qwLastUsed]?.name || agents[qwLastUsed]?.agent_name || '';
                    }
                }
                return { agent_id: qwLastUsed, agent_name: agentName || '' };
            }

            // 兼容旧版读取方式
            let agentStorage = sessionStorage.getItem('qwenpaw-agent-storage');
            if (!agentStorage) {
                agentStorage = localStorage.getItem('qwenpaw-agent-storage');
            }
            if (agentStorage) {
                const data = JSON.parse(agentStorage);
                const agentId = data.state?.selectedAgent;
                const agents = data.state?.agents;
                let agentName = '';
                if (Array.isArray(agents)) {
                    const found = agents.find(a => a.id === agentId || a.agent_id === agentId);
                    agentName = found?.name || found?.agent_name || '';
                } else if (agents && typeof agents === 'object') {
                    agentName = agents[agentId]?.name || agents[agentId]?.agent_name || '';
                }
                return { agent_id: agentId, agent_name: agentName || '' };
            }
        } catch (e) {
            console.error('[HumanThinking] 获取Agent信息失败:', e);
        }
        return { agent_id: '', agent_name: t('agent.selectAgent', 'No Agent Selected') };
    };

    // 全局 Agent 状态管理
    let currentAgentId = getCurrentAgent().agent_id;
    const agentListeners = new Set();

    const subscribeAgent = (callback) => {
        agentListeners.add(callback);
        return () => agentListeners.delete(callback);
    };

    const notifyAgentChange = (newAgentId) => {
        currentAgentId = newAgentId;
        agentListeners.forEach(cb => cb(newAgentId));
    };

    // 监听 Agent 切换（跨标签页）
    window.addEventListener('storage', (e) => {
        if (e.key === 'qwenpaw-last-used-agent') {
            const newAgentId = e.newValue || 'default';
            console.log('[HumanThinking] Agent changed to:', newAgentId);
            notifyAgentChange(newAgentId);
        }
    });

    // 轮询检测 Agent 切换（同一标签页内）
    setInterval(() => {
        const detectedAgent = getCurrentAgent().agent_id || 'default';
        if (detectedAgent !== currentAgentId) {
            console.log('[HumanThinking] Agent detected change:', detectedAgent);
            notifyAgentChange(detectedAgent);
        }
    }, 500);

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

        // useTranslation Hook - 响应式翻译
        const useTranslation = () => {
            const [lang, setLang] = useState(() => currentLang);

            useEffect(() => {
                // 立即同步当前语言（处理组件挂载时语言已变化的情况）
                setLang(currentLang);
                return subscribeLang((newLang) => {
                    setLang(newLang);
                });
            }, []);

            // 强制重新渲染的辅助函数
            const forceUpdate = () => {
                setLang(getCurrentLanguage());
            };

            return { t, lang, forceUpdate };
        };

        // useAgent Hook - 响应式 Agent
        const useAgent = () => {
            const [agent, setAgent] = useState(getCurrentAgent());

            useEffect(() => {
                const updateAgent = () => {
                    setAgent(getCurrentAgent());
                };
                updateAgent();
                return subscribeAgent((newAgentId) => {
                    updateAgent();
                });
            }, []);

            return agent;
        };

        // 智能体信息栏 - 使用原生CSS类
        const AgentInfoBar = () => {
            const { t } = useTranslation();
            const agent = useAgent();

            return React.createElement('div', { className: 'ht-agent-bar' },
                React.createElement('span', { style: { fontSize: '14px' } }, '🤖'),
                React.createElement('span', null, t('agent.current', 'Current Agent') + '：'),
                React.createElement('span', { style: { fontWeight: 600 } }, agent.agent_name || t('agent.notSelected', 'Not Selected'))
            );
        };

        // 记忆管理侧边栏
        const MemoryManagementSidebar = () => {
            const { t } = useTranslation();
            const agent = useAgent();
            const [activeTab, setActiveTab] = useState('stats');
            const [stats, setStats] = useState(null);
            const [sessions, setSessions] = useState([]);

            // 记忆搜索状态
            const [searchQuery, setSearchQuery] = useState('');
            const [searchResults, setSearchResults] = useState([]);
            const [searchLoading, setSearchLoading] = useState(false);
            const [selectedMemories, setSelectedMemories] = useState([]);
            const [editingMemory, setEditingMemory] = useState(null);
            const [editContent, setEditContent] = useState('');
            const [editType, setEditType] = useState('fact');
            const [editImportance, setEditImportance] = useState(3);
            const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);

            // 情感状态
            const [emotion, setEmotion] = useState(null);

            // 配置面板
            const [config, setConfig] = useState(null);
            const currentAgentIdRef = React.useRef('');

            // 时间线
            const [timelineData, setTimelineData] = useState([]);
            const [timeFilter, setTimeFilter] = useState('all');

            // Agent 切换时重置状态
            useEffect(() => {
                setStats(null);
                setSessions([]);
                setSearchResults([]);
                setSelectedMemories([]);
                setEmotion(null);
                setConfig(null);
                setTimelineData([]);
            }, [agent.agent_id]);

            useEffect(() => {
                const fetchData = async () => {
                    try {
                        const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                        const [statsRes, sessionsRes] = await Promise.all([
                            apiRequest('/stats' + queryParam),
                            apiRequest('/sessions' + queryParam)
                        ]);
                        setStats(statsRes);
                        setSessions(Array.isArray(sessionsRes) ? sessionsRes : []);
                    } catch (e) {
                        console.warn('[HumanThinking] API 暂不可用，使用离线模式:', e.message || e);
                        setStats({
                            total_memories: 0,
                            cross_session_memories: 0,
                            frozen_memories: 0,
                            active_sessions: 0
                        });
                        setSessions([]);
                    }
                };
                fetchData();
                const interval = setInterval(fetchData, 5000);
                return () => clearInterval(interval);
            }, [agent.agent_id]);

            const renderStats = () => {
                if (!stats) return React.createElement(Empty, { description: t('common.loading', 'Loading...') });

                const statItems = [
                    { title: t('stats.totalMemories', 'Total Memories'), value: stats.total_memories || 0, color: '#1890ff', icon: '📊' },
                    { title: t('stats.crossSession', 'Cross-Session'), value: stats.cross_session_memories || 0, color: '#52c41a', icon: '🔗' },
                    { title: t('stats.frozen', 'Frozen'), value: stats.frozen_memories || 0, color: '#faad14', icon: '❄️' },
                    { title: t('stats.activeSessions', 'Active Sessions'), value: stats.active_sessions || 0, color: '#722ed1', icon: '🔌' }
                ];

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Row, { gutter: [12, 12] },
                        statItems.map((item, index) =>
                            React.createElement(Col, { span: 12, key: index },
                                React.createElement('div', { className: 'ht-stat-card' },
                                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12 } },
                                        React.createElement('div', {
                                            style: {
                                                width: 40,
                                                height: 40,
                                                borderRadius: 8,
                                                background: item.color + '15',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: 20
                                            }
                                        }, item.icon),
                                        React.createElement(Statistic, {
                                            title: item.title,
                                            value: item.value,
                                            valueStyle: { color: item.color, fontSize: 24, fontWeight: 'bold' },
                                            style: { marginBottom: 0 }
                                        })
                                    )
                                )
                            )
                        )
                    )
                );
            };

            const handleSearch = async () => {
                if (!searchQuery.trim()) return;
                setSearchLoading(true);
                try {
                    const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                    const data = await apiRequest('/search' + queryParam, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: searchQuery, limit: 10 })
                    });
                    setSearchResults(data.memories || []);
                    setSelectedMemories([]);
                } catch (e) {
                    message.error(t('common.searchError', 'Search failed'));
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
                    const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                    const result = await apiRequest('/memories/batch' + queryParam, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ memory_ids: selectedMemories })
                    });
                    if (result && result.success === false) {
                        message.error(result.error || t('common.deleteError', 'Delete failed'));
                    } else {
                        message.success(t('common.deleteSuccess', 'Deleted {count} memories', { count: selectedMemories.length }));
                        setSearchResults(prev => prev.filter(m => !selectedMemories.includes(m.id)));
                        setSelectedMemories([]);
                    }
                    setDeleteConfirmVisible(false);
                } catch (e) {
                    message.error(t('common.deleteError', 'Delete failed'));
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
                    const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                    const result = await apiRequest('/memories/' + editingMemory.id + queryParam, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            content: editContent,
                            memory_type: editType,
                            importance: editImportance
                        })
                    });
                    if (result && result.success === false) {
                        message.error(result.error || t('common.saveError', 'Save failed'));
                    } else {
                        message.success(t('common.saveSuccess', 'Save successful'));
                        setSearchResults(prev => prev.map(m =>
                            m.id === editingMemory.id
                                ? { ...m, content: editContent, memory_type: editType, importance: editImportance }
                                : m
                        ));
                        setEditingMemory(null);
                    }
                } catch (e) {
                    message.error(t('common.saveError', 'Save failed'));
                }
            };

            const renderSearch = () => {
                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Card, {
                        size: 'small',
                        style: { marginBottom: 16 },
                        bodyStyle: { padding: '16px 20px' }
                    },
                        React.createElement(Input.Search, {
                            placeholder: t('memory.searchPlaceholder', 'Search memories...'),
                            value: searchQuery,
                            onChange: e => setSearchQuery(e.target.value),
                            onSearch: handleSearch,
                            loading: searchLoading,
                            enterButton: t('memory.search', 'Search'),
                            size: 'large'
                        })
                    ),
                    searchResults.length > 0 && React.createElement('div', { style: { marginBottom: 16, padding: '8px 0' } },
                        React.createElement(Space, null,
                            React.createElement(Checkbox, {
                                checked: selectedMemories.length === searchResults.length && searchResults.length > 0,
                                indeterminate: selectedMemories.length > 0 && selectedMemories.length < searchResults.length,
                                onChange: handleSelectAll
                            }, t('memory.selectAll', 'Select All') + ' (' + selectedMemories.length + '/' + searchResults.length + ')'),
                            selectedMemories.length > 0 && React.createElement(Button, { danger: true, size: 'small', onClick: handleBatchDelete }, t('memory.batchDelete', 'Batch Delete') + '(' + selectedMemories.length + ')')
                        )
                    ),
                    searchResults.length > 0 && React.createElement(List, {
                        size: 'small',
                        dataSource: searchResults,
                        style: { background: 'transparent' },
                        renderItem: (item) => {
                            const typeColors = {
                                fact: 'blue',
                                emotion: 'magenta',
                                preference: 'gold',
                                order: 'cyan',
                                address: 'geekblue',
                                contact: 'purple',
                                other: 'default'
                            };
                            return React.createElement(List.Item, {
                                className: 'ht-list-item',
                                actions: [
                                    React.createElement(Button, {
                                        type: 'text',
                                        size: 'small',
                                        icon: React.createElement('span', null, '✏️'),
                                        onClick: () => handleEdit(item)
                                    }, t('common.edit', 'Edit'))
                                ]
                            },
                                React.createElement('div', { style: { width: '100%' } },
                                    React.createElement('div', { style: { display: 'flex', alignItems: 'flex-start', gap: 12 } },
                                        React.createElement(Checkbox, {
                                            checked: selectedMemories.includes(item.id),
                                            onChange: () => handleSelectMemory(item.id),
                                            style: { marginTop: 4 }
                                        }),
                                        React.createElement('div', { style: { flex: 1, minWidth: 0 } },
                                            React.createElement('div', {
                                                style: {
                                                    marginBottom: 8,
                                                    fontSize: 14,
                                                    lineHeight: 1.6,
                                                    color: '#262626',
                                                    wordBreak: 'break-word'
                                                }
                                            }, item.content || t('memory.noContent', 'No content')),
                                            React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' } },
                                                React.createElement(Tag, {
                                                    size: 'small',
                                                    color: typeColors[item.memory_type] || 'default',
                                                    style: { borderRadius: 4 }
                                                }, item.memory_type || t('memory.memoryType', 'Memory')),
                                                React.createElement(Tag, {
                                                    size: 'small',
                                                    style: { borderRadius: 4, background: '#f5f5f5', borderColor: '#d9d9d9', color: '#595959' }
                                                }, '⭐ ' + (item.importance || 3)),
                                                React.createElement('span', { style: { fontSize: 12, color: '#8c8c8c' } },
                                                    item.timestamp ? new Date(item.timestamp).toLocaleString() : ''
                                                )
                                            )
                                        )
                                    )
                                )
                            );
                        }
                    }),
                    React.createElement(Modal, {
                        title: t('memory.edit', 'Edit Memory'),
                        open: !!editingMemory,
                        onOk: handleSaveEdit,
                        onCancel: () => setEditingMemory(null)
                    },
                        React.createElement('div', { style: { marginBottom: 16 } },
                            React.createElement('label', null, t('memory.content', 'Content')),
                            React.createElement(Input.TextArea, {
                                value: editContent,
                                onChange: e => setEditContent(e.target.value),
                                rows: 4
                            })
                        ),
                        React.createElement('div', { style: { marginBottom: 16 } },
                            React.createElement('label', null, t('memory.memoryType', 'Memory Type')),
                            React.createElement(Select, {
                                value: editType,
                                onChange: value => setEditType(value),
                                style: { width: '100%' },
                                options: [
                                    { value: 'fact', label: t('memory.types.fact', '📋 Fact') },
                                    { value: 'emotion', label: t('memory.types.emotion', '💝 Emotion') },
                                    { value: 'preference', label: t('memory.types.preference', '⭐ Preference') },
                                    { value: 'order', label: t('memory.types.order', '🛒 Order') },
                                    { value: 'address', label: t('memory.types.address', '📍 Address') },
                                    { value: 'contact', label: t('memory.types.contact', '📞 Contact') },
                                    { value: 'other', label: t('memory.types.other', '📦 Other') }
                                ]
                            })
                        ),
                        React.createElement('div', null,
                            React.createElement('label', null, t('memory.importance', 'Importance')),
                            React.createElement(Radio.Group, {
                                value: editImportance,
                                onChange: e => setEditImportance(e.target.value)
                            }, [1, 2, 3, 4, 5].map(i =>
                                React.createElement(Radio.Button, { key: i, value: i }, '⭐'.repeat(i))
                            ))
                        )
                    ),
                    React.createElement(Modal, {
                        title: '⚠️ ' + t('memory.batchDeleteConfirm', 'Confirm Batch Delete'),
                        open: deleteConfirmVisible,
                        onOk: handleConfirmDelete,
                        onCancel: () => setDeleteConfirmVisible(false),
                        okText: t('common.confirm', 'Confirm'),
                        cancelText: t('common.cancel', 'Cancel'),
                        okButtonProps: { danger: true }
                    },
                        React.createElement('div', { style: { marginBottom: 16 } },
                            t('memory.deleteWarning', 'Are you sure you want to delete {count} memories? This action cannot be undone!', { count: selectedMemories.length })
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
                                    }, '• ' + (m.content || t('memory.noContent', 'No content')).substring(0, 50) + ((m.content || '').length > 50 ? '...' : ''))
                                )
                        )
                    )
                );
            };

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
                    happy: { icon: '😊', label: t('emotion.happy', 'Happy'), color: '#52c41a' },
                    sad: { icon: '😢', label: t('emotion.sad', 'Sad'), color: '#1890ff' },
                    angry: { icon: '😠', label: t('emotion.angry', 'Angry'), color: '#ff4d4f' },
                    neutral: { icon: '😐', label: t('emotion.neutral', 'Neutral'), color: '#999' },
                    surprised: { icon: '😮', label: t('emotion.surprised', 'Surprised'), color: '#faad14' }
                };
                const current = emotionConfig[emotion?.current_emotion] || emotionConfig.neutral;
                const history = (emotion?.history || []).slice().reverse();

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Card, {
                        size: 'small',
                        style: { marginBottom: 16, textAlign: 'center' },
                        bodyStyle: { padding: '32px 24px' }
                    },
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
                            t('emotion.intensity', 'Intensity') + ': ' + ((emotion?.intensity || 0) * 100).toFixed(0) + '%'
                        )
                    ),
                    React.createElement(Card, {
                        size: 'small',
                        title: React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                            React.createElement('span', null, '📈'),
                            React.createElement('span', { style: { fontWeight: 600 } }, t('emotion.history', 'Recent Emotion Changes'))
                        ),
                        headStyle: { background: '#fafafa', borderBottom: '1px solid #f0f0f0' }
                    },
                        history.length === 0
                            ? React.createElement(Empty, { description: t('emotion.noHistory', 'No emotion history') })
                            : React.createElement(List, {
                                size: 'small',
                                dataSource: history,
                                style: { background: 'transparent' },
                                renderItem: (item) => {
                                    const cfg = emotionConfig[item.emotion] || emotionConfig.neutral;
                                    return React.createElement(List.Item, {
                                        className: 'ht-list-item',
                                        style: { padding: '10px 16px' }
                                    },
                                        React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, width: '100%' } },
                                            React.createElement('div', {
                                                style: {
                                                    width: 32,
                                                    height: 32,
                                                    borderRadius: 6,
                                                    background: cfg.color + '15',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    fontSize: 16
                                                }
                                            }, cfg.icon),
                                            React.createElement('div', { style: { flex: 1 } },
                                                React.createElement('div', { style: { fontWeight: 'bold', color: cfg.color, fontSize: 14 } }, cfg.label),
                                                React.createElement('div', { style: { fontSize: 12, color: '#8c8c8c' } },
                                                    item.timestamp ? new Date(item.timestamp).toLocaleString() : ''
                                                )
                                            ),
                                            React.createElement('div', { style: { color: cfg.color, fontWeight: 'bold', fontSize: 14 } },
                                                ((item.intensity || 0) * 100).toFixed(0) + '%'
                                            )
                                        )
                                    );
                                }
                            })
                    )
                );
            };

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
                    const result = await apiRequest('/config' + queryParam, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
                    if (result && result.success === false) {
                        message.error(result.error || t('common.saveError', 'Save failed'));
                    } else {
                        message.success(t('common.saveSuccess', 'Save successful'));
                    }
                } catch (e) {
                    message.error(t('common.saveError', 'Save failed'));
                }
            };

            const renderConfig = () => {
                if (!config) return React.createElement(Empty, { description: t('common.loading', 'Loading...') });

                const ConfigSection = ({ title, icon, children }) => React.createElement(Card, {
                    size: 'small',
                    title: React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                        React.createElement('span', null, icon),
                        React.createElement('span', { style: { fontWeight: 600 } }, title)
                    ),
                    style: { marginBottom: 16 },
                    headStyle: { background: '#fafafa', borderBottom: '1px solid #f0f0f0' }
                }, children);

                const ConfigItem = ({ label, description, children }) => React.createElement('div', { style: { marginBottom: 20 } },
                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 } },
                        React.createElement('label', { className: 'ht-config-label' }, label),
                        children && children.type === Switch && React.createElement('div', null, children)
                    ),
                    children && children.type !== Switch && React.createElement('div', { style: { marginBottom: 4 } }, children),
                    description && React.createElement('div', { className: 'ht-config-desc' }, description)
                );

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(ConfigSection, { title: t('config.basicFeatures', 'Basic Features'), icon: '⚙️' },
                        React.createElement(ConfigItem, {
                            label: t('config.crossSession', 'Cross-Session Memory'),
                            description: t('config.crossSessionDesc', 'Enable memory sharing across sessions')
                        },
                            React.createElement(Switch, {
                                checked: config.enable_cross_session,
                                onChange: checked => setConfig({ ...config, enable_cross_session: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('config.emotion', 'Emotion Tracking'),
                            description: t('config.emotionDesc', 'Track and analyze emotional changes')
                        },
                            React.createElement(Switch, {
                                checked: config.enable_emotion,
                                onChange: checked => setConfig({ ...config, enable_emotion: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('config.distributedDb', 'Distributed Database'),
                            description: config.enable_distributed_db
                                ? t('config.distributedDbEnabled', 'Distributed database is enabled and cannot be disabled')
                                : t('config.distributedDbDisabled', 'Enable distributed database (cannot be disabled after enabling)')
                        },
                            React.createElement(Switch, {
                                checked: config.enable_distributed_db || false,
                                disabled: config.enable_distributed_db || false,
                                onChange: checked => {
                                    if (!config.enable_distributed_db) {
                                        setConfig({ ...config, enable_distributed_db: checked });
                                    }
                                },
                                checkedChildren: t('config.enabled', 'Enabled'),
                                unCheckedChildren: t('config.disabled', 'Disabled')
                            })
                        )
                    ),

                    React.createElement(ConfigSection, { title: t('config.sessionSettings', 'Session Settings'), icon: '⏱️' },
                        React.createElement(ConfigItem, {
                            label: t('config.sessionIdleTimeout', 'Session Idle Timeout'),
                            description: t('config.sessionIdleTimeoutDesc', 'Time before session becomes idle')
                        },
                            React.createElement(Slider, {
                                min: 60,
                                max: 600,
                                value: config.session_idle_timeout || 300,
                                onChange: value => setConfig({ ...config, session_idle_timeout: value }),
                                marks: { 60: '60' + t('common.secondUnit', 's'), 300: '300' + t('common.secondUnit', 's'), 600: '600' + t('common.secondUnit', 's') }
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('config.maxMemoryChars', 'Max Memory Characters'),
                            description: t('config.maxMemoryCharsDesc', 'Maximum characters per memory entry')
                        },
                            React.createElement(Slider, {
                                min: 100,
                                max: 500,
                                value: config.max_memory_chars || 300,
                                onChange: value => setConfig({ ...config, max_memory_chars: value }),
                                marks: { 100: '100', 300: '300', 500: '500' }
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('config.maxResults', 'Search Limit'),
                            description: t('config.maxResultsDesc', 'Maximum search results to return')
                        },
                            React.createElement(Slider, {
                                min: 5,
                                max: 50,
                                value: config.max_results || 10,
                                onChange: value => setConfig({ ...config, max_results: value }),
                                marks: { 5: '5', 25: '25', 50: '50' }
                            })
                        )
                    ),

                    React.createElement(ConfigSection, { title: t('config.lifecycleSettings', 'Lifecycle Settings'), icon: '📅' },
                        React.createElement(ConfigItem, {
                            label: t('config.frozenDays', 'Frozen Days'),
                            description: t('config.frozenDaysDesc', 'Days before memories are frozen')
                        },
                            React.createElement(Slider, {
                                min: 7,
                                max: 90,
                                value: config.frozen_days || 30,
                                onChange: value => setConfig({ ...config, frozen_days: value }),
                                marks: { 7: '7' + t('common.day', 'days'), 30: '30' + t('common.day', 'days'), 90: '90' + t('common.day', 'days') }
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('config.archiveDays', 'Archive Days'),
                            description: t('config.archiveDaysDesc', 'Days before memories are archived')
                        },
                            React.createElement(Slider, {
                                min: 30,
                                max: 365,
                                value: config.archive_days || 180,
                                onChange: value => setConfig({ ...config, archive_days: value }),
                                marks: { 30: '30' + t('common.day', 'days'), 180: '180' + t('common.day', 'days'), 365: '365' + t('common.day', 'days') }
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('config.deleteDays', 'Delete Days'),
                            description: t('config.deleteDaysDesc', 'Days before memories are deleted')
                        },
                            React.createElement(Slider, {
                                min: 90,
                                max: 730,
                                value: config.delete_days || 365,
                                onChange: value => setConfig({ ...config, delete_days: value }),
                                marks: { 90: '90' + t('common.day', 'days'), 365: '1' + t('common.year', 'year'), 730: '2' + t('common.year', 'year') }
                            })
                        )
                    ),

                    // 保存按钮区域 - 使用原生CSS类
                    React.createElement('div', { className: 'ht-form-actions' },
                        React.createElement(Button, { type: 'primary', size: 'large', onClick: handleSaveConfig }, t('config.save', 'Save Config'))
                    )
                );
            };

            useEffect(() => {
                const fetchTimeline = async () => {
                    try {
                        const queryParam = agent.agent_id ? '?agent_id=' + agent.agent_id : '';
                        const data = await apiRequest('/memories/timeline' + queryParam);
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
                    { key: 'all', label: t('timeline.all', 'All') },
                    { key: 'today', label: t('timeline.today', 'Today') },
                    { key: 'week', label: t('timeline.week', 'This Week') },
                    { key: 'month', label: t('timeline.month', 'This Month') }
                ];

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Card, {
                        size: 'small',
                        style: { marginBottom: 16 },
                        bodyStyle: { padding: '12px 20px' }
                    },
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
                        ? React.createElement(Empty, { description: t('timeline.noEvents', 'No memory events in this period') })
                        : React.createElement(Timeline, null,
                            filtered.map((item, index) =>
                                React.createElement(Timeline.Item, {
                                    key: index,
                                    color: item.count > 5 ? 'red' : item.count > 2 ? 'blue' : 'green'
                                },
                                    React.createElement(Card, {
                                        size: 'small',
                                        style: { marginBottom: 8 },
                                        bodyStyle: { padding: '12px 16px' }
                                    },
                                        React.createElement('div', { style: { fontWeight: 'bold', marginBottom: 8, fontSize: 14 } },
                                            item.date,
                                            React.createElement(Tag, { color: 'blue', size: 'small', style: { marginLeft: 8 } }, item.count + ' ' + t('timeline.count', 'items'))
                                        ),
                                        React.createElement('div', null,
                                            (item.events || []).map((evt, i) =>
                                                React.createElement('div', {
                                                    key: i,
                                                    style: { fontSize: 13, color: '#595959', marginBottom: 4, lineHeight: 1.5 }
                                                }, '• ' + evt)
                                            )
                                        )
                                    )
                                )
                            )
                        )
                );
            };

            // 关于/卸载页面 - 使用传统DOM操作避免Hook问题
            const renderAbout = () => {
                const isDark = document.body.classList.contains('dark-mode');
                const isDarkMode = isDark || document.documentElement.classList.contains('dark-mode');
                
                const themeStyles = {
                    cardBg: isDarkMode ? '#1f1f1f' : '#f5f5f5',
                    cardBorder: isDarkMode ? 'rgba(255,255,255,0.08)' : '#eae9e7',
                    textColor: isDarkMode ? 'rgba(255,255,255,0.85)' : '#333',
                    textSecondary: isDarkMode ? 'rgba(255,255,255,0.45)' : '#666',
                    featureBg: isDarkMode ? 'rgba(82,196,26,0.06)' : '#f6ffed',
                    featureBorder: isDarkMode ? 'rgba(82,196,26,0.2)' : '#b7eb8f',
                    dangerBg: isDarkMode ? 'rgba(255,77,79,0.06)' : '#fff2f0',
                    dangerBorder: isDarkMode ? 'rgba(255,77,79,0.2)' : '#ffccc7',
                    dangerText: isDarkMode ? '#ff7875' : '#cf1322',
                    linkColor: isDarkMode ? '#ff7f16' : '#1890ff',
                    modalBg: isDarkMode ? '#141414' : '#fff',
                    modalOverlay: isDarkMode ? 'rgba(0,0,0,0.7)' : 'rgba(0,0,0,0.5)',
                    btnDanger: isDarkMode ? '#ff4d4f' : '#ff4d4f'
                };

                // 使用DOM操作创建弹窗，避免React状态问题
                const showUninstallModal = () => {
                    const modalId = 'ht-uninstall-modal-' + Date.now();
                    const keepDataId = 'ht-keep-data-' + Date.now();
                    
                    const modalHtml = `
                        <div id="${modalId}" style="position:fixed;top:0;left:0;right:0;bottom:0;background:${themeStyles.modalOverlay};display:flex;align-items:center;justify-content:center;z-index:1000;" onclick="if(event.target===this)document.getElementById('${modalId}').remove()">
                            <div style="background:${themeStyles.modalBg};border-radius:8px;padding:24px;max-width:500px;width:90%;box-shadow:0 4px 12px rgba(0,0,0,0.15);border:1px solid ${themeStyles.cardBorder};color:${themeStyles.textColor};">
                                <h3 style="margin-bottom:16px;color:${themeStyles.dangerText};">${t('about.uninstall.warning', '⚠️ Confirm Uninstall')}</h3>
                                <div style="margin-bottom:16px;">${t('about.uninstall.confirmMessage', 'Are you sure you want to uninstall the HumanThinking plugin? This action cannot be undone.')}</div>
                                
                                <div style="margin-bottom:16px;padding:12px;background:${themeStyles.cardBg};border-radius:4px;border:1px solid ${themeStyles.cardBorder};">
                                    <label style="display:flex;align-items:center;cursor:pointer;">
                                        <input type="checkbox" id="${keepDataId}" checked style="margin-right:8px;">
                                        <span>${t('about.uninstall.keepData', 'Keep data (config and database files)')}</span>
                                    </label>
                                    <div style="margin-top:8px;font-size:12px;color:${themeStyles.textSecondary};">${t('about.uninstall.keepDataDesc', 'Memory data will be retained after uninstallation, can be manually restored')}</div>
                                </div>

                                <div style="margin-bottom:16px;font-size:13px;color:${themeStyles.textSecondary};">
                                    <div style="font-weight:bold;margin-bottom:8px;color:${themeStyles.textColor};">📦 ${t('about.uninstall.keepDataOptions', 'Data Retention Options')}</div>
                                    <ul style="margin:4px 0;padding-left:20px;">
                                        <li>${t('about.uninstall.keepDataOption1', 'Default checked "Keep data (config and database files)"')}</li>
                                        <li>${t('about.uninstall.keepDataOption2', 'When checked: Uninstall plugin but keep all memory data')}</li>
                                        <li>${t('about.uninstall.keepDataOption3', 'When unchecked: Export memories then delete all data')}</li>
                                    </ul>
                                </div>

                                <div style="margin-bottom:16px;font-size:13px;color:${themeStyles.textSecondary};">
                                    <div style="font-weight:bold;margin-bottom:8px;color:${themeStyles.textColor};">⚡ ${t('about.uninstall.uninstallActions', 'Uninstall will perform')}</div>
                                    <ul style="margin:4px 0;padding-left:20px;">
                                        <li>${t('about.uninstall.action1', 'Delete plugin directory')}</li>
                                        <li>${t('about.uninstall.action2', 'Remove plugin from QwenPaw config')}</li>
                                    </ul>
                                </div>

                                <div style="display:flex;gap:12px;justify-content:flex-end;">
                                    <button onclick="document.getElementById('${modalId}').remove()" style="padding:8px 16px;background:transparent;color:${themeStyles.textColor};border:1px solid ${themeStyles.cardBorder};border-radius:4px;cursor:pointer;">${t('common.cancel', 'Cancel')}</button>
                                    <button id="${modalId}-confirm" style="padding:8px 16px;background:${themeStyles.btnDanger};color:white;border:none;border-radius:4px;cursor:pointer;font-weight:bold;">${t('about.uninstall.confirm', 'Confirm Uninstall')}</button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    const div = document.createElement('div');
                    div.innerHTML = modalHtml;
                    document.body.appendChild(div);
                    
                    // 绑定确认按钮事件
                    document.getElementById(modalId + '-confirm').onclick = async () => {
                        const keepData = document.getElementById(keepDataId).checked;
                        const btn = document.getElementById(modalId + '-confirm');
                        btn.textContent = t('about.uninstall.uninstalling', 'Uninstalling...');
                        btn.disabled = true;
                        
                        try {
                            const token = window.QwenPaw?.host?.getApiToken?.() || '';
                            const apiBase = getApiBase();
                            console.log('[HumanThinking] 开始卸载请求，API:', apiBase + '/uninstall');
                            const response = await fetch(apiBase + '/uninstall', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': 'Bearer ' + token
                                },
                                body: JSON.stringify({ keep_data: keepData })
                            });
                            console.log('[HumanThinking] 卸载响应状态:', response.status);
                            const result = await response.json();
                            console.log('[HumanThinking] 卸载响应结果:', result);
                            
                            document.getElementById(modalId).remove();
                            
                            if (result.success) {
                                alert(t('about.uninstall.success', '✅ Uninstall Complete!\n\n{message}\n\n⚠️ Important:\nPlease restart QwenPaw twice to ensure complete cleanup.', { message: result.message }));
                            } else {
                                alert(t('about.uninstall.error', '❌ Uninstall Failed: {message}', { message: result.message || t('about.uninstall.unknownError', 'Unknown error') }));
                            }
                        } catch (e) {
                            console.error('[HumanThinking] 卸载请求异常:', e);
                            document.getElementById(modalId).remove();
                            alert(t('about.uninstall.error', '❌ Uninstall Failed: {message}', { message: e.message }));
                        }
                    };
                };

                return React.createElement('div', { style: { padding: 16, color: themeStyles.textColor } },
                    // 版本信息
                    React.createElement('div', { style: { marginBottom: 24 } },
                        React.createElement('h3', { style: { marginBottom: 16, borderBottom: `2px solid ${themeStyles.linkColor}`, paddingBottom: 8, color: themeStyles.textColor } }, '📋 ' + t('about.versionInfo', 'Version Info')),
                        React.createElement('div', {
                            style: { background: themeStyles.cardBg, padding: 16, borderRadius: 8, border: `1px solid ${themeStyles.cardBorder}` }
                        },
                            React.createElement('div', { style: { marginBottom: 8 } },
                                React.createElement('strong', null, t('about.version', 'Version') + '：'), 'v1.1.5.post1'
                            ),
                            React.createElement('div', { style: { marginBottom: 8 } },
                                React.createElement('strong', null, t('about.pluginName', 'Plugin Name') + '：'), 'Human Thinking Memory Manager'
                            ),
                            React.createElement('div', { style: { marginBottom: 8 } },
                                React.createElement('strong', null, t('about.author', 'Author') + '：'), 'HumanThinking Team'
                            ),
                            React.createElement('div', { style: { marginBottom: 8 } },
                                React.createElement('strong', null, t('about.license', 'License') + '：'), 'MIT'
                            ),
                            React.createElement('div', { style: { marginBottom: 8 } },
                                React.createElement('strong', null, t('about.minQwenPawVersion', 'Minimum QwenPaw Version') + '：'), 'v1.1.5b1'
                            ),
                            React.createElement('div', null,
                                React.createElement('strong', null, t('about.github', 'GitHub') + '：'),
                                React.createElement('a', {
                                    href: 'https://github.com/kingsa2026/QwenPaw_HumanThinking_plugin',
                                    target: '_blank',
                                    style: { color: themeStyles.linkColor }
                                }, 'kingsa2026/QwenPaw_HumanThinking_plugin')
                            )
                        )
                    ),

                    // 功能说明
                    React.createElement('div', { style: { marginBottom: 24 } },
                        React.createElement('h3', { style: { marginBottom: 16, borderBottom: '2px solid #52c41a', paddingBottom: 8, color: themeStyles.textColor } }, '✨ ' + t('about.features.title', 'Features')),
                        React.createElement('div', {
                            style: { background: themeStyles.featureBg, padding: 16, borderRadius: 8, border: `1px solid ${themeStyles.featureBorder}` }
                        },
                            React.createElement('div', { style: { marginBottom: 12 } },
                                React.createElement('h4', { style: { color: themeStyles.textColor } }, t('about.features.memory', '🧠 Memory Management')),
                                React.createElement('ul', null,
                                    React.createElement('li', null, t('about.features.memoryDesc.0', 'Cross-session memory persistence')),
                                    React.createElement('li', null, t('about.features.memoryDesc.1', 'Memory search - Support keyword and semantic search')),
                                    React.createElement('li', null, t('about.features.memoryDesc.2', 'Memory lifecycle - Automatic freezing, archiving and cleanup')),
                                    React.createElement('li', null, t('about.features.memoryDesc.3', 'Emotion state tracking - Record and analyze emotional changes'))
                                )
                            ),
                            React.createElement('div', { style: { marginBottom: 12 } },
                                React.createElement('h4', { style: { color: themeStyles.textColor } }, t('about.features.sleep', '🌙 Sleep Management')),
                                React.createElement('ul', null,
                                    React.createElement('li', null, t('about.features.sleepDesc.0', 'Smart sleep scheduling')),
                                    React.createElement('li', null, t('about.features.sleepDesc.1', 'Dream generation - Organize and consolidate memories during sleep')),
                                    React.createElement('li', null, t('about.features.sleepDesc.2', 'Sleep reports - Generate sleep quality and memory consolidation reports'))
                                )
                            ),
                            React.createElement('div', null,
                                React.createElement('h4', { style: { color: themeStyles.textColor } }, t('about.features.config', '⚙️ Configuration')),
                                React.createElement('ul', null,
                                    React.createElement('li', null, t('about.features.configDesc.0', 'Support Agent-isolated configuration')),
                                    React.createElement('li', null, t('about.features.configDesc.1', 'Distributed database support')),
                                    React.createElement('li', null, t('about.features.configDesc.2', 'Customizable memory retention policies'))
                                )
                            )
                        )
                    ),

                    // 一键卸载
                    React.createElement('div', { style: { marginBottom: 24 } },
                        React.createElement('h3', { style: { marginBottom: 16, borderBottom: '2px solid #ff4d4f', paddingBottom: 8, color: themeStyles.textColor } }, '⚠️ ' + t('about.dangerZone', 'Danger Zone')),
                        React.createElement('div', {
                            style: { background: themeStyles.dangerBg, padding: 16, borderRadius: 8, border: `1px solid ${themeStyles.dangerBorder}` }
                        },
                            React.createElement('div', { style: { marginBottom: 16, color: themeStyles.dangerText, fontWeight: 'bold' } },
                                t('about.uninstall.description', 'Uninstalling will remove the plugin directory and remove the plugin from QwenPaw config.')
                            ),
                            React.createElement('button', {
                                onClick: showUninstallModal,
                                style: {
                                    padding: '8px 24px',
                                    background: themeStyles.btnDanger,
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    fontWeight: 'bold'
                                }
                            }, '⚠️ ' + t('about.uninstall.button', 'Uninstall Plugin'))
                        )
                    )
                );
            };

            const tabItems = [
                { key: 'stats', label: '📊 ' + t('nav.stats', 'Memory Stats'), children: renderStats() },
                { key: 'search', label: '🔍 ' + t('nav.search', 'Memory Search'), children: renderSearch() },
                { key: 'emotion', label: '💝 ' + t('nav.emotion', 'Emotion Status'), children: renderEmotion() },
                { key: 'timeline', label: '📅 ' + t('nav.timeline', 'Timeline'), children: renderTimeline() },
                { key: 'config', label: '⚙️ ' + t('nav.config', 'Memory Config'), children: renderConfig() },
                { key: 'about', label: 'ℹ️ ' + t('nav.about', 'About'), children: renderAbout() }
            ];

            return React.createElement('div', { style: { height: '100%', display: 'flex', flexDirection: 'column' } },
                // 标题栏 - 使用原生CSS类
                React.createElement('div', { className: 'ht-page-header' },
                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } },
                        React.createElement('span', { style: { fontSize: '20px' } }, '🧠'),
                        React.createElement('div', null,
                            React.createElement('div', { className: 'ht-page-title' }, 'HumanThinking ' + t('memory.title', 'Memory Management')),
                            React.createElement('div', { className: 'ht-page-subtitle' }, t('plugin.description', 'Memory Management Plugin'))
                        )
                    ),
                    React.createElement(AgentInfoBar)
                ),
                // 内容区域 - 使用原生CSS类
                React.createElement('div', { className: 'ht-content' },
                    React.createElement(Tabs, {
                        className: 'ht-tabs',
                        items: tabItems,
                        activeKey: activeTab,
                        onChange: setActiveTab
                    })
                )
            );
        };

        // 睡眠管理侧边栏 - 简化版
        const SleepManagementSidebar = () => {
            const { t } = useTranslation();
            const agent = useAgent();
            const [activeTab, setActiveTab] = useState('status');
            const [sleepStatus, setSleepStatus] = useState(null);

            const fetchSleepStatus = async () => {
                try {
                    const currentAgent = getCurrentAgent();
                    const aid = agent.agent_id || currentAgent.agent_id || 'default';
                    const data = await apiRequest('/sleep/status?agent_id=' + aid);
                    setSleepStatus(data);
                } catch (e) {
                    console.error('[HumanThinking] 获取睡眠状态失败:', e);
                }
            };

            useEffect(() => {
                setSleepStatus(null);
            }, [agent.agent_id]);

            useEffect(() => {
                fetchSleepStatus();
                const interval = setInterval(fetchSleepStatus, 5000);
                return () => clearInterval(interval);
            }, [agent.agent_id]);

            const handleSleepAction = async (action) => {
                try {
                    const currentAgent = getCurrentAgent();
                    const aid = agent.agent_id || currentAgent.agent_id || 'default';
                    const queryParam = '?agent_id=' + aid;
                    const endpoint = action === 'wakeup' ? '/sleep/wakeup' + queryParam : '/sleep/force' + queryParam;
                    const body = action === 'wakeup' ? {} : { sleep_type: action };
                    console.log('[HumanThinking] Sleep action:', action, 'agent_id:', aid, 'endpoint:', endpoint);
                    const result = await apiRequest(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    console.log('[HumanThinking] Sleep action result:', result);
                    if (result && result.success === false) {
                        message.error(result.error || t('common.error', 'Error'));
                    } else {
                        message.success(t('common.success', 'Success'));
                    }
                    fetchSleepStatus();
                } catch (e) {
                    console.error('[HumanThinking] Sleep action failed:', e);
                    message.error(t('common.error', 'Error') + ': ' + (e.message || 'Unknown'));
                }
            };

            const statusConfig = {
                active: { icon: '☀️', label: t('sleep.status.awake', 'Active'), color: '#52c41a' },
                light_sleep: { icon: '⭐', label: t('sleep.status.light', 'Light Sleep'), color: '#faad14' },
                rem: { icon: '💭', label: t('sleep.status.rem', 'REM Sleep'), color: '#1890ff' },
                deep_sleep: { icon: '🌙', label: t('sleep.status.deep', 'Deep Sleep'), color: '#722ed1' }
            };

            const current = statusConfig[sleepStatus?.status] || statusConfig.active;
            const gifMap = {
                'active': '/api/plugins/humanthinking/files/img/dance.gif',
                'light_sleep': '/api/plugins/humanthinking/files/img/sleep1.gif',
                'rem': '/api/plugins/humanthinking/files/img/sleep2.gif',
                'deep_sleep': '/api/plugins/humanthinking/files/img/sleep3.gif'
            };

            const getStatusLightClass = () => {
                const type = sleepStatus?.status || 'active';
                const classMap = {
                    'active': 'active',
                    'light_sleep': 'light',
                    'rem': 'rem',
                    'deep_sleep': 'deep'
                };
                return 'ht-status-light ' + (classMap[type] || 'active');
            };

            const getGifStyle = () => {
                const style = {
                    width: 140,
                    height: 140,
                    borderRadius: 16,
                    display: 'block',
                    margin: '0 auto 20px',
                    transition: 'all 0.5s ease'
                };
                if (sleepStatus?.status === 'active') {
                    style.boxShadow = `0 0 20px ${current.color}60, 0 0 40px ${current.color}40`;
                } else if (sleepStatus?.status === 'light_sleep') {
                    style.boxShadow = `0 0 15px ${current.color}50`;
                } else if (sleepStatus?.status === 'rem') {
                    style.boxShadow = `0 0 20px ${current.color}60`;
                } else if (sleepStatus?.status === 'deep_sleep') {
                    style.boxShadow = `0 0 10px ${current.color}40`;
                }
                return style;
            };

            const renderStatus = () => {
                const currentStatus = sleepStatus?.status || 'active';
                const btnBase = { height: 48, transition: 'all 0.3s' };
                const sleepButtons = [
                    { key: 'light', action: 'light', icon: '⭐', label: t('sleep.lightSleep', 'Light Sleep'), activeStatus: 'light_sleep', activeColor: '#faad14', activeBg: '#fffbe6' },
                    { key: 'rem', action: 'rem', icon: '💭', label: t('sleep.remSleep', 'REM Sleep'), activeStatus: 'rem', activeColor: '#1890ff', activeBg: '#e6f7ff' },
                    { key: 'deep', action: 'deep', icon: '🌙', label: t('sleep.deepSleep', 'Deep Sleep'), activeStatus: 'deep_sleep', activeColor: '#722ed1', activeBg: '#f9f0ff' },
                    { key: 'wakeup', action: 'wakeup', icon: '☀️', label: t('sleep.wakeUp', 'Wake Up'), activeStatus: 'active', activeColor: '#52c41a', activeBg: '#f6ffed' }
                ];

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Row, { gutter: [16, 16] },
                        React.createElement(Col, { span: 24 },
                            React.createElement(Card, {
                                size: 'small',
                                style: { textAlign: 'center', padding: '32px 0' }
                            },
                                React.createElement('img', {
                                    className: getStatusLightClass(),
                                    src: gifMap[currentStatus] || gifMap.active,
                                    alt: current.label,
                                    style: getGifStyle()
                                }),
                                React.createElement('div', { style: { fontSize: 28, fontWeight: 'bold', color: current.color, marginTop: 16 } },
                                    current.label
                                ),
                                React.createElement('div', { style: { fontSize: 13, color: '#8c8c8c', marginTop: 8 } },
                                    t('sleep.statusDesc', 'Current sleep state of the agent')
                                )
                            )
                        )
                    ),
                    React.createElement(Row, { gutter: [12, 12], style: { marginTop: 16 } },
                        ...sleepButtons.map(btn => {
                            const isActive = currentStatus === btn.activeStatus;
                            return React.createElement(Col, { span: 12, key: btn.key },
                                React.createElement(Button, {
                                    size: 'large',
                                    block: true,
                                    type: isActive ? 'primary' : 'default',
                                    onClick: () => handleSleepAction(btn.action),
                                    style: isActive
                                        ? { ...btnBase, borderColor: btn.activeColor, backgroundColor: btn.activeBg, color: btn.activeColor, fontWeight: 'bold', boxShadow: `0 2px 8px ${btn.activeColor}33` }
                                        : btnBase
                                }, React.createElement('span', { style: { fontSize: 18, marginRight: 8 } }, btn.icon), btn.label)
                            );
                        })
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
                    const result = await apiRequest('/sleep/config' + queryParam, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(values)
                    });
                    if (result && result.success === false) {
                        message.error(result.error || t('common.saveError', 'Save failed'));
                    } else {
                        message.success(t('common.saveSuccess', 'Save successful'));
                    }
                } catch (e) {
                    message.error(t('common.saveError', 'Save failed'));
                }
            };

            const renderConfig = () => {
                if (!sleepConfig) return React.createElement(Empty, { description: t('common.loading', 'Loading...') });

                // 获取当前Agent名称，用于动态替换显示文本
                const currentAgent = getCurrentAgent();
                let agentName = currentAgent.agent_name || currentAgent.agent_id || '';
                // 如果无法获取agent名称，尝试从页面元素读取
                if (!agentName) {
                    const agentSelect = document.querySelector('[class*="agent-select"]');
                    if (agentSelect) {
                        const selected = agentSelect.querySelector('.ant-select-selection-item') || agentSelect.querySelector('.ant-select-selection-selected-value');
                        if (selected) agentName = selected.textContent.trim();
                    }
                }
                // 最终fallback - 使用默认名称确保替换能工作
                if (!agentName) agentName = 'Agent';
                console.log('[HumanThinking] Current agent name for sleep config:', agentName);

                const ConfigSection = ({ title, icon, children }) => React.createElement(Card, {
                    size: 'small',
                    title: React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                        React.createElement('span', null, icon),
                        React.createElement('span', { style: { fontWeight: 600 } }, title)
                    ),
                    style: { marginBottom: 16 },
                    headStyle: { background: '#fafafa', borderBottom: '1px solid #f0f0f0' }
                }, children);

                const ConfigItem = ({ label, description, children }) => React.createElement('div', { style: { marginBottom: 20 } },
                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 } },
                        React.createElement('label', { className: 'ht-config-label' }, label),
                        children && children.type === Switch && React.createElement('div', null, children)
                    ),
                    children && children.type !== Switch && React.createElement('div', { style: { marginBottom: 4 } }, children),
                    description && React.createElement('div', { className: 'ht-config-desc' }, description)
                );

                // 动态替换Agent名称到描述文本中
                const rawDesc = t('sleep.enableAgentSleepDesc', 'Allow {agent} to enter sleep states');
                const enableSleepDesc = rawDesc.replace('{agent}', agentName);

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(ConfigSection, { title: t('sleep.basicSettings', 'Basic Settings'), icon: '⚙️' },
                        React.createElement(ConfigItem, {
                            label: t('sleep.enableAgentSleep', 'Enable {agent} Sleep').replace('{agent}', agentName),
                            description: enableSleepDesc
                        },
                            React.createElement(Switch, {
                                checked: sleepConfig.enable_agent_sleep,
                                onChange: checked => setSleepConfig({ ...sleepConfig, enable_agent_sleep: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('sleep.lightSleepMinutes', 'Enter Sleep (minutes)'),
                            description: t('sleep.lightSleepMinutesDesc', 'Time before entering light sleep')
                        },
                            React.createElement(Slider, {
                                min: 5,
                                max: 120,
                                value: sleepConfig.light_sleep_minutes || 30,
                                onChange: value => setSleepConfig({ ...sleepConfig, light_sleep_minutes: value }),
                                marks: { 5: '5' + t('common.minute', 'min'), 30: '30' + t('common.minute', 'min'), 120: '120' + t('common.minute', 'min') }
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('sleep.remMinutes', 'Light Sleep Duration (minutes)'),
                            description: t('sleep.remMinutesDesc', 'Duration of light sleep stage')
                        },
                            React.createElement(Slider, {
                                min: 15,
                                max: 180,
                                value: sleepConfig.rem_minutes || 60,
                                onChange: value => setSleepConfig({ ...sleepConfig, rem_minutes: value }),
                                marks: { 15: '15' + t('common.minute', 'min'), 60: '60' + t('common.minute', 'min'), 180: '180' + t('common.minute', 'min') }
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('sleep.deepSleepMinutes', 'Deep Sleep Entry (minutes)'),
                            description: t('sleep.deepSleepMinutesDesc', 'Time before entering deep sleep')
                        },
                            React.createElement(Slider, {
                                min: 30,
                                max: 240,
                                value: sleepConfig.deep_sleep_minutes || 120,
                                onChange: value => setSleepConfig({ ...sleepConfig, deep_sleep_minutes: value }),
                                marks: { 30: '30' + t('common.minute', 'min'), 120: '120' + t('common.minute', 'min'), 240: '240' + t('common.minute', 'min') }
                            })
                        )
                    ),

                    React.createElement(ConfigSection, { title: t('sleep.consolidationSettings', 'Consolidation Settings'), icon: '🧠' },
                        React.createElement(ConfigItem, {
                            label: t('sleep.enableInsight', 'Auto Consolidation'),
                            description: t('sleep.enableInsightDesc', 'Automatically consolidate memories, scan N days')
                        },
                            React.createElement(Switch, {
                                checked: sleepConfig.enable_insight,
                                onChange: checked => setSleepConfig({ ...sleepConfig, enable_insight: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('sleep.enableDreamLog', 'Dream Log'),
                            description: t('sleep.enableDreamLogDesc', 'Record processing logs for each sleep stage')
                        },
                            React.createElement(Switch, {
                                checked: sleepConfig.enable_dream_log,
                                onChange: checked => setSleepConfig({ ...sleepConfig, enable_dream_log: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        React.createElement(ConfigItem, {
                            label: t('sleep.consolidateDays', 'Memory Consolidation Days'),
                            description: t('sleep.consolidateDaysDesc', 'Number of days to scan for consolidation')
                        },
                            React.createElement(Slider, {
                                min: 1,
                                max: 30,
                                value: sleepConfig.consolidate_days || 7,
                                onChange: value => setSleepConfig({ ...sleepConfig, consolidate_days: value }),
                                marks: { 1: '1' + t('common.day', 'days'), 7: '7' + t('common.day', 'days'), 30: '30' + t('common.day', 'days') }
                            })
                        )
                    ),

                    React.createElement(ConfigSection, { title: t('sleep.mergeSettings', 'Memory Merge'), icon: '🔗' },
                        React.createElement(ConfigItem, {
                            label: t('sleep.enableMerge', 'Auto Merge Similar Memories'),
                            description: t('sleep.enableMergeDesc', 'Automatically merge similar memories during sleep')
                        },
                            React.createElement(Switch, {
                                checked: sleepConfig.enable_merge !== false,
                                onChange: checked => setSleepConfig({ ...sleepConfig, enable_merge: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        sleepConfig.enable_merge !== false && React.createElement(ConfigItem, {
                            label: t('sleep.mergeThreshold', 'Merge Similarity Threshold'),
                            description: t('sleep.mergeThresholdDesc', 'Higher threshold = stricter matching, fewer merges')
                        },
                            React.createElement(Slider, {
                                min: 0.5,
                                max: 0.95,
                                step: 0.05,
                                value: sleepConfig.merge_similarity_threshold || 0.8,
                                onChange: value => setSleepConfig({ ...sleepConfig, merge_similarity_threshold: value }),
                                marks: { 0.5: '0.5', 0.7: '0.7', 0.8: '0.8', 0.9: '0.9', 0.95: '0.95' }
                            })
                        ),
                        sleepConfig.enable_merge !== false && React.createElement(ConfigItem, {
                            label: t('sleep.mergeMaxDistance', 'Max Merge Time Distance (hours)'),
                            description: t('sleep.mergeMaxDistanceDesc', 'Only merge memories within this time window')
                        },
                            React.createElement(Slider, {
                                min: 1,
                                max: 168,
                                value: sleepConfig.merge_max_distance_hours || 72,
                                onChange: value => setSleepConfig({ ...sleepConfig, merge_max_distance_hours: value }),
                                marks: { 1: '1h', 24: '24h', 72: '72h', 168: '168h' }
                            })
                        )
                    ),

                    React.createElement(ConfigSection, { title: t('sleep.contradictionSettings', 'Contradiction Detection'), icon: '⚡' },
                        React.createElement(ConfigItem, {
                            label: t('sleep.enableContradictionDetection', 'Contradiction Detection'),
                            description: t('sleep.enableContradictionDetectionDesc', 'Automatically detect and handle conflicting memories during sleep')
                        },
                            React.createElement(Switch, {
                                checked: sleepConfig.enable_contradiction_detection !== false,
                                onChange: checked => setSleepConfig({ ...sleepConfig, enable_contradiction_detection: checked }),
                                checkedChildren: t('config.on', 'On'),
                                unCheckedChildren: t('config.off', 'Off')
                            })
                        ),
                        sleepConfig.enable_contradiction_detection !== false && React.createElement(React.Fragment, null,
                            React.createElement(ConfigItem, {
                                label: t('sleep.contradictionThreshold', 'Contradiction Detection Threshold'),
                                description: t('sleep.contradictionThresholdDesc', 'Higher threshold = stricter detection, fewer false positives')
                            },
                                React.createElement(Slider, {
                                    min: 0.3,
                                    max: 0.99,
                                    step: 0.05,
                                    value: sleepConfig.contradiction_threshold || 0.7,
                                    onChange: value => setSleepConfig({ ...sleepConfig, contradiction_threshold: value }),
                                    marks: { 0.3: '0.3', 0.5: '0.5', 0.7: '0.7', 0.85: '0.85', 0.99: '0.99' }
                                })
                            ),
                            React.createElement(ConfigItem, {
                                label: t('sleep.contradictionStrategy', 'Contradiction Resolution Strategy'),
                                description: t('sleep.contradictionStrategyDesc', 'How to resolve detected contradictions')
                            },
                                React.createElement(Select, {
                                    value: sleepConfig.contradiction_resolution_strategy || 'keep_latest',
                                    onChange: value => setSleepConfig({ ...sleepConfig, contradiction_resolution_strategy: value }),
                                    style: { width: '100%' },
                                    options: [
                                        { value: 'keep_latest', label: t('sleep.strategy.keepLatest', 'Keep Latest') },
                                        { value: 'keep_frequent', label: t('sleep.strategy.keepFrequent', 'Keep Most Frequent') },
                                        { value: 'keep_high_confidence', label: t('sleep.strategy.keepHighConfidence', 'Keep High Confidence') },
                                        { value: 'mark_for_review', label: t('sleep.strategy.markForReview', 'Mark for Review') },
                                        { value: 'keep_both', label: t('sleep.strategy.keepBoth', 'Keep Both') },
                                    ]
                                })
                            ),
                            React.createElement(ConfigItem, {
                                label: t('sleep.autoResolveContradiction', 'Auto Resolve Contradictions'),
                                description: t('sleep.autoResolveContradictionDesc', 'Automatically resolve contradictions without human review')
                            },
                                React.createElement(Switch, {
                                    checked: sleepConfig.auto_resolve_contradiction !== false,
                                    onChange: checked => setSleepConfig({ ...sleepConfig, auto_resolve_contradiction: checked }),
                                    checkedChildren: t('config.on', 'On'),
                                    unCheckedChildren: t('config.off', 'Off')
                                })
                            ),
                            sleepConfig.auto_resolve_contradiction !== false && React.createElement(ConfigItem, {
                                label: t('sleep.minConfidenceForAutoResolve', 'Min Confidence for Auto Resolve'),
                                description: t('sleep.minConfidenceForAutoResolveDesc', 'Only auto-resolve contradictions above this confidence level')
                            },
                                React.createElement(Slider, {
                                    min: 0.5,
                                    max: 0.99,
                                    step: 0.05,
                                    value: sleepConfig.min_confidence_for_auto_resolve || 0.85,
                                    onChange: value => setSleepConfig({ ...sleepConfig, min_confidence_for_auto_resolve: value }),
                                    marks: { 0.5: '0.5', 0.7: '0.7', 0.85: '0.85', 0.99: '0.99' }
                                })
                            ),
                            React.createElement(ConfigItem, {
                                label: t('sleep.enableSemanticCheck', 'Semantic Contradiction Check'),
                                description: t('sleep.enableSemanticCheckDesc', 'Detect semantic contradictions (sentiment polarity reversal)')
                            },
                                React.createElement(Switch, {
                                    checked: sleepConfig.enable_semantic_contradiction_check !== false,
                                    onChange: checked => setSleepConfig({ ...sleepConfig, enable_semantic_contradiction_check: checked }),
                                    checkedChildren: t('config.on', 'On'),
                                    unCheckedChildren: t('config.off', 'Off')
                                })
                            ),
                            React.createElement(ConfigItem, {
                                label: t('sleep.enableTemporalCheck', 'Temporal Contradiction Check'),
                                description: t('sleep.enableTemporalCheckDesc', 'Detect temporal contradictions (past vs present)')
                            },
                                React.createElement(Switch, {
                                    checked: sleepConfig.enable_temporal_contradiction_check !== false,
                                    onChange: checked => setSleepConfig({ ...sleepConfig, enable_temporal_contradiction_check: checked }),
                                    checkedChildren: t('config.on', 'On'),
                                    unCheckedChildren: t('config.off', 'Off')
                                })
                            )
                        )
                    ),

                    // 保存按钮区域 - 使用原生CSS类
                    React.createElement('div', { className: 'ht-form-actions' },
                        React.createElement(Button, {
                            type: 'primary',
                            size: 'large',
                            onClick: () => handleSaveConfig(sleepConfig)
                        }, t('config.save', 'Save Config'))
                    )
                );
            };

            // 功能说明
            const renderEnergy = () => {
                const sleepStates = [
                    { icon: '☀️', name: t('sleep.states.active.name', 'Active State'), energy: t('sleep.states.active.energy', 'High'), color: '#52c41a', desc: t('sleep.states.active.desc', 'Agent is fully active, responding to user requests normally.') },
                    { icon: '⭐', name: t('sleep.states.light.name', 'Light Sleep'), energy: t('sleep.states.light.energy', 'Med-High'), color: '#faad14', desc: t('sleep.states.light.desc', 'Agent enters light rest state, reducing power but maintaining basic responsiveness.') },
                    { icon: '💭', name: t('sleep.states.rem.name', 'REM Stage'), energy: t('sleep.states.rem.energy', 'Medium'), color: '#1890ff', desc: t('sleep.states.rem.desc', 'Simulate human REM sleep, performing memory reorganization and pattern recognition.') },
                    { icon: '🌙', name: t('sleep.states.deep.name', 'Deep Sleep'), energy: t('sleep.states.deep.energy', 'Low'), color: '#722ed1', desc: t('sleep.states.deep.desc', 'Agent enters deep consolidation state, performing six-dimensional weighted scoring on candidate memories, executing forgetting curve algorithm.') }
                ];

                return React.createElement('div', { style: { padding: 16 } },
                    React.createElement(Card, {
                        size: 'small',
                        title: React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                            React.createElement('span', null, '📖'),
                            React.createElement('span', { style: { fontWeight: 600 } }, t('sleep.energyTitle', 'Features'))
                        ),
                        style: { marginBottom: 16 },
                        headStyle: { background: '#fafafa', borderBottom: '1px solid #f0f0f0' }
                    },
                        React.createElement(List, {
                            size: 'small',
                            dataSource: sleepStates,
                            style: { background: 'transparent' },
                            renderItem: (item) => React.createElement(List.Item, {
                                className: 'ht-list-item'
                            },
                                React.createElement('div', { style: { width: '100%' } },
                                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 } },
                                        React.createElement('div', {
                                            style: {
                                                width: 40,
                                                height: 40,
                                                borderRadius: 8,
                                                background: item.color + '15',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: 20
                                            }
                                        }, item.icon),
                                        React.createElement('div', { style: { flex: 1 } },
                                            React.createElement('div', { style: { fontWeight: 'bold', color: item.color, fontSize: 14 } }, item.name)
                                        ),
                                        React.createElement(Tag, { color: item.color, size: 'small' }, t('sleep.scoring.energy', 'Energy') + ': ' + item.energy)
                                    ),
                                    React.createElement('div', { style: { fontSize: 13, color: '#666', paddingLeft: 52, lineHeight: 1.6 } }, item.desc)
                                )
                            )
                        })
                    ),

                    React.createElement(Card, {
                        size: 'small',
                        title: React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: 8 } },
                            React.createElement('span', null, '📊'),
                            React.createElement('span', { style: { fontWeight: 600 } }, t('sleep.scoring.title', 'Six-Dimensional Scoring System'))
                        ),
                        headStyle: { background: '#fafafa', borderBottom: '1px solid #f0f0f0' }
                    },
                        React.createElement(Row, { gutter: [12, 12] },
                            [
                                { name: t('sleep.scoring.relevance', 'Relevance'), weight: '30%', color: '#1890ff' },
                                { name: t('sleep.scoring.frequency', 'Frequency'), weight: '24%', color: '#52c41a' },
                                { name: t('sleep.scoring.timeliness', 'Timeliness'), weight: '15%', color: '#faad14' },
                                { name: t('sleep.scoring.diversity', 'Diversity'), weight: '15%', color: '#722ed1' },
                                { name: t('sleep.scoring.integration', 'Integration'), weight: '10%', color: '#eb2f96' },
                                { name: t('sleep.scoring.richness', 'Concept Richness'), weight: '6%', color: '#13c2c2' }
                            ].map(item =>
                                React.createElement(Col, { span: 8, key: item.name },
                                    React.createElement(Card, { size: 'small', style: { textAlign: 'center', border: '1px solid ' + item.color + '30' } },
                                        React.createElement('div', { style: { color: item.color, fontWeight: 'bold', fontSize: 16 } }, item.weight),
                                        React.createElement('div', { style: { fontSize: 12, color: '#595959' } }, item.name)
                                    )
                                )
                            )
                        )
                    )
                );
            };

            const tabItems = [
                { key: 'status', label: '🌙 ' + t('sleep.statusTitle', 'Sleep Status'), children: renderStatus() },
                { key: 'config', label: '⚙️ ' + t('sleep.configTitle', 'Parameters'), children: renderConfig() },
                { key: 'energy', label: '📖 ' + t('sleep.energyTitle', 'Features'), children: renderEnergy() }
            ];

            return React.createElement('div', { style: { height: '100%', display: 'flex', flexDirection: 'column' } },
                // 标题栏 - 使用原生CSS类
                React.createElement('div', { className: 'ht-page-header' },
                    React.createElement('div', { style: { display: 'flex', alignItems: 'center', gap: '8px' } },
                        React.createElement('span', { style: { fontSize: '20px' } }, '🌙'),
                        React.createElement('div', null,
                            React.createElement('div', { className: 'ht-page-title' }, 'HumanThinking ' + t('sleep.title', 'Sleep Management')),
                            React.createElement('div', { className: 'ht-page-subtitle' }, t('sleep.title', 'Sleep Management'))
                        )
                    ),
                    React.createElement(AgentInfoBar)
                ),
                // 内容区域 - 使用原生CSS类
                React.createElement('div', { className: 'ht-content' },
                    React.createElement(Tabs, {
                        className: 'ht-tabs',
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
    let sidebarComponents = null;

    const resetHtInjectedMarkers = () => {
        try {
            document.querySelectorAll('.ant-select[data-ht-injected]').forEach(el => {
                delete el.dataset.htInjected;
            });
            document.querySelectorAll('[data-ht-tab-injected]').forEach(el => {
                delete el.dataset.htTabInjected;
            });
        } catch(e) {}
    };

    const createTranslatableLabel = (key, fallback) => {
        const React = window.QwenPaw.host.React;
        const LabelComponent = () => {
            const [label, setLabel] = React.useState(t(key, fallback));
            React.useEffect(() => {
                const unsub = subscribeLang(() => {
                    setLabel(t(key, fallback));
                });
                return unsub;
            }, []);
            return label;
        };
        return React.createElement(LabelComponent);
    };

    const registerSidebarRoutes = () => {
        if (!sidebarComponents || !window.QwenPaw?.registerRoutes) return;
        if (window._htRoutesRegistered) return;
        const React = window.QwenPaw.host.React;

        window.QwenPaw.registerRoutes(PLUGIN_ID, [
            {
                path: '/humanthinking/memory',
                component: sidebarComponents.MemoryManagementSidebar,
                label: createTranslatableLabel('nav.memory', 'Memory Management'),
                icon: React.createElement('span', { style: { fontSize: '12px', lineHeight: '12px' } }, '\u270e'),
                priority: 10
            },
            {
                path: '/humanthinking/sleep',
                component: sidebarComponents.SleepManagementSidebar,
                label: createTranslatableLabel('nav.sleep', 'Sleep Management'),
                icon: React.createElement('span', { style: { fontSize: '12px', lineHeight: '12px' } }, '\u262a'),
                priority: 20
            }
        ]);
        window._htRoutesRegistered = true;
        console.log('[HumanThinking] \u2713 \u4fa7\u8fb9\u680f\u8def\u7531\u5df2\u6ce8\u518c:', getCurrentLanguage());
    };

    const init = async () => {
        try {
            // 加载多语言翻译
            translations = await loadTranslations();
            console.log('[HumanThinking] 翻译加载完成:', getCurrentLanguage());

            await waitForDependencies();
            console.log('[HumanThinking] 依赖已加载，开始注册...');

            sidebarComponents = createComponents();

            if (window.QwenPaw?.registerRoutes) {
                registerSidebarRoutes();
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
        const React = window.QwenPaw?.host?.React;
        if (!React) { console.error('[HumanThinking] React not available'); var el = document.createElement('div'); el.textContent = 'React not loaded'; return el; }
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
            .then((result) => {
                setSaving(false);
                if (result && result.success === false) {
                    alert(t('config.errorSaving', 'Save failed: {error}', { error: result.error || t('common.unknownError', 'Unknown error') }));
                } else {
                    alert(t('common.saveSuccess', 'Save successful'));
                }
            })
            .catch(err => {
                console.error('[HumanThinking] Failed to save config:', err);
                setSaving(false);
                alert(t('common.saveError', 'Save failed'));
            });
        };

        const updateConfig = (key, value) => {
            setConfig(prev => ({ ...prev, [key]: value }));
        };

        if (loading) {
            return React.createElement('div', { style: { padding: '40px', textAlign: 'center' } }, t('common.loading', 'Loading...'));
        }

        return React.createElement('div', { style: { padding: '16px' } },
            React.createElement('h3', { style: { marginBottom: '16px' } }, t('htConfig.title', '🧠 HumanThinking Memory Config')),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, t('htConfig.crossSession', 'Cross-Session Memory')),
                React.createElement('input', {
                    type: 'checkbox',
                    checked: config.enable_cross_session,
                    onChange: (e) => updateConfig('enable_cross_session', e.target.checked),
                    style: { marginRight: '8px' }
                }),
                React.createElement('span', null, t('htConfig.crossSessionDesc', 'Enable cross-session memory persistence'))
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, t('htConfig.emotion', 'Emotion Tracking')),
                React.createElement('input', {
                    type: 'checkbox',
                    checked: config.enable_emotion,
                    onChange: (e) => updateConfig('enable_emotion', e.target.checked),
                    style: { marginRight: '8px' }
                }),
                React.createElement('span', null, t('htConfig.emotionDesc', 'Enable emotion state calculation'))
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, t('htConfig.distributedDb', 'Distributed Database')),
                React.createElement('input', {
                    type: 'checkbox',
                    checked: config.distributed_db || false,
                    onChange: (e) => updateConfig('distributed_db', e.target.checked),
                    style: { marginRight: '8px' }
                }),
                React.createElement('span', null, t('htConfig.distributedDbDesc', 'Enable distributed database (cannot be disabled after enabling)'))
            ),
            React.createElement('div', { style: { marginBottom: '16px' } },
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, t('htConfig.sessionIdleTimeout', 'Session Idle Timeout (seconds)') + `: ${config.session_idle_timeout}` + t('common.secondUnit', 's')),
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
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, t('htConfig.maxMemoryChars', 'Max Memory Characters') + `: ${config.max_memory_chars}` + t('common.char', 'chars')),
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
                React.createElement('label', { style: { display: 'block', marginBottom: '8px' } }, t('htConfig.maxResults', 'Search Limit (items)') + `: ${config.max_results}` + t('common.record', 'items')),
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
                React.createElement('h4', { style: { marginBottom: '12px' } }, t('htConfig.lifecycle', 'Memory Lifecycle')),
                React.createElement('div', { style: { marginBottom: '12px' } },
                    React.createElement('label', { style: { display: 'block', marginBottom: '4px' } }, t('htConfig.frozenDays', 'Frozen Days') + `: ${config.frozen_days}` + t('common.day', 'days')),
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
                    React.createElement('label', { style: { display: 'block', marginBottom: '4px' } }, t('htConfig.archiveDays', 'Archive Days') + `: ${config.archive_days}` + t('common.day', 'days')),
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
                    React.createElement('label', { style: { display: 'block', marginBottom: '4px' } }, t('htConfig.deleteDays', 'Delete Days') + `: ${config.delete_days}` + t('common.day', 'days')),
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
                }, saving ? t('htConfig.saving', 'Saving...') : t('htConfig.save', 'Save Config'))
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
                    if (label.includes(t('nav.memory', 'Memory Management')) || label.includes('Memory Manager') || label.includes('memory_manager_backend')) {
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
                        if (label.includes(t('nav.memory', 'Memory Management')) || label.includes('Memory Manager')) {
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
                        if (label.includes(t('nav.memory', 'Memory Management')) || label.includes('Memory Manager')) {
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
                        if (label.includes(t('nav.memory', 'Memory Management')) || label.includes('Memory Manager')) {
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
            htTabBtn.innerHTML = '<div class="ant-tabs-tab-btn" role="tab" aria-selected="false" tabindex="-1">HT' + t('nav.config', 'Config') + '</div>';

            // 添加到tab列表（在"长期记忆"tab之后）
            const tabList = tabsNav.querySelector('.ant-tabs-nav-list');
            const allTabs = tabsNav.querySelectorAll('.ant-tabs-tab');
            console.log('[HumanThinking] tabList found:', !!tabList, 'allTabs count:', allTabs.length);

            let inserted = false;
            for (let i = 0; i < allTabs.length; i++) {
                const tabText = allTabs[i].textContent || '';
                if (tabText.includes(t('nav.memory', 'Memory')) || tabText.includes('Memory')) {
                    if (allTabs[i + 1] && tabList) {
                        tabList.insertBefore(htTabBtn, allTabs[i + 1]);
                        inserted = true;
                        console.log('[HumanThinking] ✓ HT tab inserted after Memory');
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

            console.log('[HumanThinking] ✓ HT Memory Config tab created');
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
                <h3 style="margin-bottom: 16px;">${t('htConfig.title', '🧠 HumanThinking Memory Config')}</h3>
                <div id="ht-config-loading" style="text-align: center; padding: 40px;">
                    ${t('common.loading', 'Loading...')}
                </div>
                <div id="ht-config-content" style="display: none;">
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.crossSession', 'Cross-Session Memory')}</label>
                        <input type="checkbox" id="ht-cross-session" checked style="margin-right: 8px;">
                        <span>${t('htConfig.crossSessionDesc', 'Enable cross-session memory persistence')}</span>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.emotion', 'Emotion Tracking')}</label>
                        <input type="checkbox" id="ht-emotion" checked style="margin-right: 8px;">
                        <span>${t('htConfig.emotionDesc', 'Enable emotion state calculation')}</span>
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.sessionIdleTimeout', 'Session Idle Timeout (seconds)')}</label>
                        <input type="range" id="ht-timeout" min="60" max="600" value="180" style="width: 100%;">
                        <span id="ht-timeout-value">180</span>${t('common.secondUnit', 's')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.maxMemoryChars', 'Max Memory Characters')}</label>
                        <input type="range" id="ht-max-chars" min="100" max="500" value="150" style="width: 100%;">
                        <span id="ht-max-chars-value">150</span>${t('common.char', 'chars')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.maxResults', 'Search Limit (items)')}</label>
                        <input type="range" id="ht-max-results" min="5" max="50" value="5" style="width: 100%;">
                        <span id="ht-max-results-value">5</span>${t('common.record', 'items')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.frozenDays', 'Frozen Days')}</label>
                        <input type="range" id="ht-frozen-days" min="7" max="90" value="30" style="width: 100%;">
                        <span id="ht-frozen-days-value">30</span>${t('common.day', 'days')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.archiveDays', 'Archive Days')}</label>
                        <input type="range" id="ht-archive-days" min="30" max="365" value="90" style="width: 100%;">
                        <span id="ht-archive-days-value">90</span>${t('common.day', 'days')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.deleteDays', 'Delete Days')}</label>
                        <input type="range" id="ht-delete-days" min="90" max="730" value="180" style="width: 100%;">
                        <span id="ht-delete-days-value">180</span>${t('common.day', 'days')}
                    </div>
                    <div style="margin-bottom: 16px;">
                        <label style="display: block; margin-bottom: 8px;">${t('htConfig.compressionMode', 'Compression Mode')}</label>
                        <select id="ht-compression-mode" style="width: 100%; padding: 6px 12px; border: 1px solid #d9d9d9; border-radius: 4px;">
                            <option value="auto">${t('htConfig.compressionAuto', 'Auto (LLM with simple fallback)')}</option>
                            <option value="llm">${t('htConfig.compressionLLM', 'LLM Only')}</option>
                            <option value="simple">${t('htConfig.compressionSimple', 'Simple Concatenation Only')}</option>
                        </select>
                    </div>
                    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #eae9e7;">
                        <button id="ht-save-config" style="padding: 8px 24px; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            ${t('htConfig.save', 'Save Config')}
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

            const compressionMode = container.querySelector('#ht-compression-mode');
            if (compressionMode) compressionMode.value = data.compression_mode || 'auto';
        })
        .catch(err => {
            console.error('[HumanThinking] 加载配置失败:', err);
            const loadingDiv = container.querySelector('#ht-config-loading');
            if (loadingDiv) loadingDiv.innerHTML = t('htConfig.loadFailed', 'Load failed, using default config');
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
            compression_mode: container.querySelector('#ht-compression-mode')?.value || 'auto',
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
                status.textContent = t('htConfig.saveSuccess', '✓ Save successful');
                setTimeout(() => { status.textContent = ''; }, 3000);
            }
        })
        .catch(err => {
            console.error('[HumanThinking] 保存配置失败:', err);
            const status = container.querySelector('#ht-save-status');
            if (status) {
                status.textContent = t('htConfig.saveError', '✗ Save failed');
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
