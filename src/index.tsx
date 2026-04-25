/**
 * HumanThinking 插件前端入口
 * 
 * 提供两个独立的侧边栏：
 * 1. 记忆管理侧边栏 (6个Tab)
 * 2. 睡眠管理侧边栏 (3个Tab)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Tabs,
  Card,
  Statistic,
  Row,
  Col,
  Input,
  Button,
  List,
  Tag,
  Space,
  Divider,
  Timeline,
  Form,
  Switch,
  Slider,
  Select,
  Checkbox,
  Popconfirm,
  Modal,
  message,
  Spin,
  Empty,
  Typography,
  Badge,
  Table
} from 'antd';
import {
  SearchOutlined,
  BarChartOutlined,
  MessageOutlined,
  HeartOutlined,
  CalendarOutlined,
  SettingOutlined,
  MoonOutlined,
  SaveOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  LinkOutlined,
  ReloadOutlined,
  CheckOutlined,
  CloseOutlined,
  InfoCircleOutlined,
  BulbOutlined,
  BookOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// ============ API 工具函数 ============

const getApiBase = () => {
  const baseUrl = (window as any).QwenPaw?.host?.getApiUrl?.('') || '';
  if (baseUrl && baseUrl.includes('/api/')) {
    return `${baseUrl}plugins/humanthinking`;
  }
  return `${baseUrl}api/plugins/humanthinking`;
};

const getHeaders = () => {
  const token = (window as any).QwenPaw?.host?.getApiToken?.();
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

// 获取当前Agent信息
const getCurrentAgent = () => {
  try {
    const agentStorage = sessionStorage.getItem('qwenpaw-agent-storage');
    if (agentStorage) {
      const data = JSON.parse(agentStorage);
      const agentId = data.state?.selectedAgent;
      const agentName = data.state?.agents?.[agentId]?.name || '未命名Agent';
      return { agent_id: agentId, agent_name: agentName };
    }
  } catch (e) {
    console.error('Failed to get agent info:', e);
  }
  return { agent_id: '', agent_name: '未选择Agent' };
};

// ============ 全局组件：智能体信息栏 ============

function AgentInfoBar() {
  const [agent, setAgent] = useState({ agent_id: '', agent_name: '' });

  useEffect(() => {
    const updateAgent = () => {
      setAgent(getCurrentAgent());
    };
    updateAgent();
    const interval = setInterval(updateAgent, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      padding: '8px 16px',
      background: '#f0f2f5',
      borderBottom: '1px solid #d9d9d9',
      fontSize: '13px',
      color: '#666'
    }}>
      <span>🤖 当前智能体: </span>
      <Text strong>{agent.agent_name}</Text>
      <Text type="secondary" style={{ marginLeft: 8 }}>({agent.agent_id})</Text>
    </div>
  );
}

// ============ 3.1 记忆统计面板 ============

function MemoryStatsPanel() {
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/stats`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setStats(data);
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><BarChartOutlined /> 记忆统计</Title>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Card>
              <Statistic title="总记忆" value={stats.total_memories || 0} />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic title="跨会话记忆" value={stats.cross_session_memories || 0} />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic title="冷藏记忆" value={stats.frozen_memories || 0} />
            </Card>
          </Col>
          <Col span={12}>
            <Card>
              <Statistic title="活跃会话" value={stats.active_sessions || 0} />
            </Card>
          </Col>
          <Col span={12}>
            <Card>
              <Statistic title="情感状态数" value={stats.emotional_states || 0} />
            </Card>
          </Col>
        </Row>
        <Divider />
        <Button icon={<ReloadOutlined />} onClick={fetchStats}>刷新数据</Button>
      </Spin>
    </div>
  );
}

// ============ 3.2 记忆搜索面板 ============

function MemorySearch() {
  const [query, setQuery] = useState('');
  const [memories, setMemories] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingMemory, setEditingMemory] = useState<any>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm, setEditForm] = useState({ content: '', memory_type: '', importance: 3 });

  const searchMemories = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/search`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ query, limit: 20 })
      });
      const data = await resp.json();
      setMemories(data.memories || []);
    } catch (e) {
      console.error('Failed to search:', e);
    }
    setLoading(false);
  }, [query]);

  const handleSave = async (memory: any) => {
    try {
      const resp = await fetch(`${getApiBase()}/memories/${memory.id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({
          content: memory.content,
          memory_type: memory.memory_type,
          importance: memory.importance
        })
      });
      if (resp.ok) {
        message.success('保存成功');
        memory._modified = false;
        setMemories([...memories]);
      }
    } catch (e) {
      console.error('Failed to save:', e);
    }
  };

  const handleBatchDelete = async () => {
    try {
      const resp = await fetch(`${getApiBase()}/memories/batch`, {
        method: 'DELETE',
        headers: getHeaders(),
        body: JSON.stringify({ memory_ids: selectedIds })
      });
      if (resp.ok) {
        message.success(`已删除 ${selectedIds.length} 条记忆`);
        setMemories(memories.filter(m => !selectedIds.includes(m.id)));
        setSelectedIds([]);
      }
    } catch (e) {
      console.error('Failed to delete:', e);
    }
  };

  const openEditModal = (memory: any) => {
    setEditingMemory(memory);
    setEditForm({
      content: memory.content,
      memory_type: memory.memory_type || 'fact',
      importance: memory.importance || 3
    });
    setEditModalVisible(true);
  };

  const handleEditSave = async () => {
    if (!editingMemory) return;
    try {
      const resp = await fetch(`${getApiBase()}/memories/${editingMemory.id}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(editForm)
      });
      if (resp.ok) {
        message.success('保存成功');
        const updated = memories.map(m => 
          m.id === editingMemory.id ? { ...m, ...editForm } : m
        );
        setMemories(updated);
        setEditModalVisible(false);
      }
    } catch (e) {
      console.error('Failed to save:', e);
    }
  };

  const updateMemoryField = (id: string, field: string, value: any) => {
    const updated = memories.map(m => {
      if (m.id === id) {
        const newM = { ...m, [field]: value, _modified: true };
        return newM;
      }
      return m;
    });
    setMemories(updated);
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><SearchOutlined /> 记忆搜索</Title>
      <Space style={{ marginBottom: 16 }}>
        <Input
          placeholder="搜索记忆..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          onPressEnter={searchMemories}
          style={{ width: 300 }}
        />
        <Button type="primary" icon={<SearchOutlined />} onClick={searchMemories}>搜索</Button>
      </Space>

      {memories.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <Checkbox
            checked={selectedIds.length === memories.length && memories.length > 0}
            indeterminate={selectedIds.length > 0 && selectedIds.length < memories.length}
            onChange={e => setSelectedIds(e.target.checked ? memories.map(m => m.id) : [])}
          >
            全选
          </Checkbox>
          <Text style={{ marginLeft: 16 }}>已选择 {selectedIds.length} 项</Text>
        </div>
      )}

      <Spin spinning={loading}>
        <List
          dataSource={memories}
          renderItem={(item: any) => (
            <List.Item>
              <Card style={{ width: '100%' }} size="small">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <Checkbox
                    checked={selectedIds.includes(item.id)}
                    onChange={e => {
                      if (e.target.checked) {
                        setSelectedIds([...selectedIds, item.id]);
                      } else {
                        setSelectedIds(selectedIds.filter(id => id !== item.id));
                      }
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <div
                      style={{ cursor: 'pointer', marginBottom: 8 }}
                      onClick={() => openEditModal(item)}
                    >
                      <Text>{item.content}</Text>
                      <EditOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                    </div>
                    <Space>
                      <Text type="secondary">角色: {item.role || 'user'}</Text>
                      <Select
                        size="small"
                        value={item.memory_type || 'fact'}
                        onChange={value => updateMemoryField(item.id, 'memory_type', value)}
                        style={{ width: 100 }}
                      >
                        <Option value="fact">事实</Option>
                        <Option value="emotion">情感</Option>
                        <Option value="preference">偏好</Option>
                        <Option value="order">订单</Option>
                        <Option value="address">地址</Option>
                        <Option value="contact">联系</Option>
                        <Option value="other">其他</Option>
                      </Select>
                      <Select
                        size="small"
                        value={item.importance || 3}
                        onChange={value => updateMemoryField(item.id, 'importance', value)}
                        style={{ width: 80 }}
                      >
                        <Option value={1}>1</Option>
                        <Option value={2}>2</Option>
                        <Option value={3}>3</Option>
                        <Option value={4}>4</Option>
                        <Option value={5}>5</Option>
                      </Select>
                      <Text type="secondary">{new Date(item.created_at).toLocaleString()}</Text>
                    </Space>
                  </div>
                  <Button
                    type="primary"
                    size="small"
                    icon={<SaveOutlined />}
                    disabled={!item._modified}
                    onClick={() => handleSave(item)}
                  >
                    保存
                  </Button>
                </div>
              </Card>
            </List.Item>
          )}
        />
      </Spin>

      {selectedIds.length > 0 && (
        <div style={{ position: 'fixed', bottom: 20, right: 20 }}>
          <Popconfirm
            title="确认批量删除"
            description={`确定要删除 ${selectedIds.length} 条记忆吗？此操作不可恢复！`}
            onConfirm={handleBatchDelete}
            okText="确认删除"
            cancelText="取消"
          >
            <Button type="primary" danger icon={<DeleteOutlined />}>
              批量删除({selectedIds.length})
            </Button>
          </Popconfirm>
        </div>
      )}

      <Modal
        title="编辑记忆"
        open={editModalVisible}
        onOk={handleEditSave}
        onCancel={() => setEditModalVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label="记忆内容">
            <TextArea
              rows={4}
              value={editForm.content}
              onChange={e => setEditForm({ ...editForm, content: e.target.value })}
            />
          </Form.Item>
          <Form.Item label="记忆类型">
            <Select
              value={editForm.memory_type}
              onChange={value => setEditForm({ ...editForm, memory_type: value })}
            >
              <Option value="fact">事实</Option>
              <Option value="emotion">情感</Option>
              <Option value="preference">偏好</Option>
              <Option value="order">订单</Option>
              <Option value="address">地址</Option>
              <Option value="contact">联系</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>
          <Form.Item label="重要性">
            <Select
              value={editForm.importance}
              onChange={value => setEditForm({ ...editForm, importance: value })}
            >
              <Option value={1}>1 - 低</Option>
              <Option value={2}>2</Option>
              <Option value={3}>3 - 中</Option>
              <Option value={4}>4</Option>
              <Option value={5}>5 - 高</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

// ============ 3.3 会话列表面板 ============

function SessionList() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/sessions`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setSessions(data || []);
    } catch (e) {
      console.error('Failed to fetch sessions:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleRename = async (sessionId: string) => {
    try {
      const resp = await fetch(`${getApiBase()}/sessions/${sessionId}/rename`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ session_name: editName })
      });
      if (resp.ok) {
        message.success('重命名成功');
        setSessions(sessions.map(s => 
          s.session_id === sessionId ? { ...s, session_name: editName } : s
        ));
        setEditingId(null);
      }
    } catch (e) {
      console.error('Failed to rename:', e);
    }
  };

  const handleBatchDelete = async () => {
    try {
      const resp = await fetch(`${getApiBase()}/sessions/batch-delete`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ session_ids: selectedIds })
      });
      if (resp.ok) {
        message.success(`已删除 ${selectedIds.length} 个会话`);
        setSessions(sessions.filter(s => !selectedIds.includes(s.session_id)));
        setSelectedIds([]);
      }
    } catch (e) {
      console.error('Failed to delete:', e);
    }
  };

  const openSession = (sessionId: string) => {
    const qp = (window as any).QwenPaw;
    if (qp?.host?.openSession) {
      qp.host.openSession(sessionId);
    } else {
      window.open(`/console/chat/${sessionId}`, '_blank');
    }
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><MessageOutlined /> 会话列表</Title>
      
      <div style={{ marginBottom: 16 }}>
        <Button onClick={() => setSelectedIds(selectedIds.length === sessions.length ? [] : sessions.map(s => s.session_id))}>
          {selectedIds.length === sessions.length ? '取消全选' : '批量选择'}
        </Button>
        {selectedIds.length > 0 && (
          <Text style={{ marginLeft: 16 }}>已选择 {selectedIds.length} 项</Text>
        )}
      </div>

      <Spin spinning={loading}>
        <List
          dataSource={sessions}
          renderItem={(item: any) => (
            <List.Item>
              <Card style={{ width: '100%' }} size="small">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <Checkbox
                    checked={selectedIds.includes(item.session_id)}
                    onChange={e => {
                      if (e.target.checked) {
                        setSelectedIds([...selectedIds, item.session_id]);
                      } else {
                        setSelectedIds(selectedIds.filter(id => id !== item.session_id));
                      }
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    {editingId === item.session_id ? (
                      <Space>
                        <Input
                          value={editName}
                          onChange={e => setEditName(e.target.value)}
                          size="small"
                        />
                        <Button size="small" icon={<CheckOutlined />} onClick={() => handleRename(item.session_id)} />
                        <Button size="small" icon={<CloseOutlined />} onClick={() => setEditingId(null)} />
                      </Space>
                    ) : (
                      <div
                        style={{ cursor: 'pointer', fontWeight: 'bold' }}
                        onClick={() => {
                          setEditingId(item.session_id);
                          setEditName(item.session_name || '');
                        }}
                      >
                        {item.session_name || '未命名会话'}
                        <EditOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                      </div>
                    )}
                    <div style={{ marginTop: 4 }}>
                      <Text type="secondary">对话对象: {item.user_name || '未知'}</Text>
                    </div>
                    <div>
                      <Text type="secondary">会话ID: </Text>
                      <a onClick={() => openSession(item.session_id)}>{item.session_id}</a>
                    </div>
                    <div>
                      <Text type="secondary">记忆数: {item.memory_count} | 最后活跃: {new Date(item.last_active).toLocaleString()}</Text>
                    </div>
                  </div>
                </div>
              </Card>
            </List.Item>
          )}
        />
      </Spin>

      {selectedIds.length > 0 && (
        <div style={{ position: 'fixed', bottom: 20, right: 20 }}>
          <Popconfirm
            title="确认批量删除"
            description={`确定要删除 ${selectedIds.length} 个会话吗？此操作不可恢复！`}
            onConfirm={handleBatchDelete}
            okText="确认删除"
            cancelText="取消"
          >
            <Button type="primary" danger icon={<DeleteOutlined />}>
              批量删除({selectedIds.length})
            </Button>
          </Popconfirm>
        </div>
      )}
    </div>
  );
}

// ============ 3.4 情感状态面板 ============

function EmotionIndicator() {
  const [emotion, setEmotion] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const fetchEmotion = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/emotion`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setEmotion(data);
    } catch (e) {
      console.error('Failed to fetch emotion:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchEmotion();
  }, [fetchEmotion]);

  const getEmotionIcon = (emo: string) => {
    const map: any = { happy: '😊', sad: '😢', angry: '😠', neutral: '😐', excited: '🤩' };
    return map[emo] || '😐';
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><HeartOutlined /> 情感状态</Title>
      <Spin spinning={loading}>
        <Card style={{ textAlign: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 64, marginBottom: 16 }}>
            {getEmotionIcon(emotion.current_emotion)}
          </div>
          <Title level={3}>
            当前: {emotion.current_emotion || 'neutral'} ({emotion.intensity || 0})
          </Title>
        </Card>
        
        <Title level={5}>情感历史</Title>
        <Timeline>
          {(emotion.history || []).map((h: any, idx: number) => (
            <Timeline.Item key={idx}>
              {new Date(h.timestamp).toLocaleString()} - {h.emotion} ({h.intensity})
            </Timeline.Item>
          ))}
        </Timeline>
      </Spin>
    </div>
  );
}

// ============ 3.5 记忆时间线面板 ============

function MemoryTimeline() {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchTimeline = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/memories/timeline`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setTimeline(data || []);
    } catch (e) {
      console.error('Failed to fetch timeline:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><CalendarOutlined /> 记忆时间线</Title>
      <Spin spinning={loading}>
        <Timeline mode="left">
          {timeline.map((item: any, idx: number) => (
            <Timeline.Item key={idx} label={item.date}>
              <Card size="small">
                <Text strong>{item.count} 个事件</Text>
                <div>
                  {item.events.map((e: string, i: number) => (
                    <Tag key={i}>{e}</Tag>
                  ))}
                </div>
              </Card>
            </Timeline.Item>
          ))}
        </Timeline>
      </Spin>
    </div>
  );
}

// ============ 3.6 配置面板 ============

function ConfigPanel() {
  const [config, setConfig] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/config`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setConfig(data);
    } catch (e) {
      console.error('Failed to fetch config:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${getApiBase()}/config`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(config)
      });
      message.success('配置已保存');
    } catch (e) {
      console.error('Failed to save config:', e);
    }
    setSaving(false);
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><SettingOutlined /> 配置</Title>
      <Spin spinning={loading}>
        <Form layout="vertical">
          <Form.Item label="启用跨会话记忆">
            <Switch 
              checked={config.enable_cross_session}
              onChange={v => setConfig({...config, enable_cross_session: v})}
            />
          </Form.Item>
          <Form.Item label="启用情感跟踪">
            <Switch 
              checked={config.enable_emotion}
              onChange={v => setConfig({...config, enable_emotion: v})}
            />
          </Form.Item>
          <Form.Item label="最大搜索结果数">
            <Slider 
              min={1} max={20} 
              value={config.max_results}
              onChange={v => setConfig({...config, max_results: v})}
            />
          </Form.Item>
          <Form.Item label="冷藏天数">
            <Slider 
              min={7} max={90} 
              value={config.frozen_days}
              onChange={v => setConfig({...config, frozen_days: v})}
            />
          </Form.Item>
          <Form.Item label="归档天数">
            <Slider 
              min={30} max={365} 
              value={config.archive_days}
              onChange={v => setConfig({...config, archive_days: v})}
            />
          </Form.Item>
          <Form.Item label="删除天数">
            <Slider 
              min={90} max={730} 
              value={config.delete_days}
              onChange={v => setConfig({...config, delete_days: v})}
            />
          </Form.Item>
          <Button type="primary" onClick={handleSave} loading={saving}>
            保存配置
          </Button>
        </Form>
      </Spin>
    </div>
  );
}

// ============ 侧边栏A：记忆管理主组件 ============

function MemoryManagementSidebar() {
  const [activeTab, setActiveTab] = useState('stats');

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <AgentInfoBar />
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        type="card"
        style={{ flex: 1, overflow: 'auto' }}
      >
        <Tabs.TabPane tab={<span><BarChartOutlined />统计</span>} key="stats">
          <MemoryStatsPanel />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><SearchOutlined />搜索</span>} key="search">
          <MemorySearch />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><MessageOutlined />会话</span>} key="sessions">
          <SessionList />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><HeartOutlined />情感</span>} key="emotion">
          <EmotionIndicator />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><CalendarOutlined />时间线</span>} key="timeline">
          <MemoryTimeline />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><SettingOutlined />配置</span>} key="config">
          <ConfigPanel />
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
}

// ============ 4. 睡眠管理侧边栏 ============

function SleepStatusPanel() {
  const [status, setStatus] = useState<any>({});
  const [loading, setLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const resp = await fetch(`${getApiBase()}/sleep/status`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setStatus(data);
    } catch (e) {
      console.error('Failed to fetch sleep status:', e);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleForceSleep = async (type: string) => {
    try {
      await fetch(`${getApiBase()}/sleep/force`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ sleep_type: type })
      });
      message.success(`已进入${type}睡眠`);
      fetchStatus();
    } catch (e) {
      console.error('Failed to force sleep:', e);
    }
  };

  const handleWakeUp = async () => {
    try {
      await fetch(`${getApiBase()}/sleep/wakeup`, {
        method: 'POST',
        headers: getHeaders()
      });
      message.success('已唤醒');
      fetchStatus();
    } catch (e) {
      console.error('Failed to wakeup:', e);
    }
  };

  const getStatusColor = () => {
    if (status.status === 'active') return '#52c41a';
    if (status.sleep_type === 'deep') return '#722ed1';
    if (status.sleep_type === 'rem') return '#1890ff';
    if (status.sleep_type === 'light') return '#faad14';
    return '#d9d9d9';
  };

  const getStatusText = () => {
    if (status.status === 'active') return '活跃状态';
    if (status.sleep_type === 'deep') return '深层睡眠';
    if (status.sleep_type === 'rem') return 'REM阶段';
    if (status.sleep_type === 'light') return '浅层睡眠';
    return '未知状态';
  };

  const getStatusIcon = () => {
    if (status.status === 'active') return '☀️';
    if (status.sleep_type === 'deep') return '🌙';
    if (status.sleep_type === 'rem') return '💭';
    if (status.sleep_type === 'light') return '⭐';
    return '❓';
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><MoonOutlined /> 睡眠状态</Title>
      <Card style={{ textAlign: 'center', marginBottom: 24 }}>
        <div style={{ 
          width: 120, 
          height: 120, 
          borderRadius: '50%', 
          background: getStatusColor(),
          margin: '0 auto 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 48,
          boxShadow: `0 0 20px ${getStatusColor()}80`
        }}>
          {getStatusIcon()}
        </div>
        <Title level={3} style={{ color: getStatusColor() }}>
          {getStatusText()}
        </Title>
        <Text type="secondary">
          上次活跃: {status.last_active_time ? new Date(status.last_active_time * 1000).toLocaleString() : '-'}
        </Text>
      </Card>

      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Button 
            block 
            onClick={() => handleForceSleep('light')}
            disabled={status.status !== 'active'}
          >
            进入浅层睡眠
          </Button>
        </Col>
        <Col span={8}>
          <Button 
            block 
            onClick={() => handleForceSleep('deep')}
            disabled={status.status !== 'active'}
          >
            进入深层睡眠
          </Button>
        </Col>
        <Col span={8}>
          <Button 
            block 
            type="primary"
            onClick={handleWakeUp}
            disabled={status.status === 'active'}
          >
            立即唤醒
          </Button>
        </Col>
      </Row>
    </div>
  );
}

function SleepConfigPanel() {
  const [config, setConfig] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/sleep/config`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setConfig(data);
    } catch (e) {
      console.error('Failed to fetch sleep config:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${getApiBase()}/sleep/config`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(config)
      });
      message.success('配置已保存');
    } catch (e) {
      console.error('Failed to save sleep config:', e);
    }
    setSaving(false);
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><SettingOutlined /> 参数配置</Title>
      <Spin spinning={loading}>
        <Form layout="vertical">
          <Form.Item label="启用Agent睡眠">
            <Switch 
              checked={config.enable_agent_sleep}
              onChange={v => setConfig({...config, enable_agent_sleep: v})}
            />
          </Form.Item>

          <Divider orientation="left">睡眠阶段时长</Divider>

          <Form.Item label={`进入睡眠状态时间: ${config.light_sleep_minutes || 30}分钟`}>
            <Slider 
              min={5} max={120} 
              value={config.light_sleep_minutes || 30}
              onChange={v => setConfig({...config, light_sleep_minutes: v})}
              marks={{ 5: '5分', 30: '30分', 60: '60分', 120: '120分' }}
            />
          </Form.Item>

          <Form.Item label={`浅层睡眠持续时间: ${config.rem_minutes || 60}分钟`}>
            <Slider 
              min={15} max={180} 
              value={config.rem_minutes || 60}
              onChange={v => setConfig({...config, rem_minutes: v})}
              marks={{ 15: '15分', 60: '60分', 120: '120分', 180: '180分' }}
            />
          </Form.Item>

          <Form.Item label={`深层睡眠进入时间: ${config.deep_sleep_minutes || 120}分钟`}>
            <Slider 
              min={30} max={240} 
              value={config.deep_sleep_minutes || 120}
              onChange={v => setConfig({...config, deep_sleep_minutes: v})}
              marks={{ 30: '30分', 120: '120分', 180: '180分', 240: '240分' }}
            />
          </Form.Item>

          <Divider orientation="left">洞察灯功能</Divider>

          <Form.Item label="启用洞察灯">
            <Switch 
              checked={config.enable_insight}
              onChange={v => setConfig({...config, enable_insight: v})}
            />
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              开启后，Agent在睡眠期间会生成记忆洞察和反思摘要
            </Paragraph>
          </Form.Item>

          <Form.Item label="启用梦境日志">
            <Switch 
              checked={config.enable_dream_log}
              onChange={v => setConfig({...config, enable_dream_log: v})}
            />
            <Paragraph type="secondary" style={{ marginTop: 8 }}>
              记录睡眠各阶段的处理日志，便于调试和分析
            </Paragraph>
          </Form.Item>

          <Form.Item label="记忆整合天数">
            <Slider 
              min={1} max={30} 
              value={config.consolidate_days || 7}
              onChange={v => setConfig({...config, consolidate_days: v})}
            />
          </Form.Item>

          <Button type="primary" onClick={handleSave} loading={saving}>
            保存配置
          </Button>
        </Form>
      </Spin>
    </div>
  );
}

function SleepEnergyPanel() {
  return (
    <div style={{ padding: 16 }}>
      <Title level={4}><BookOutlined /> 共轭能说明</Title>
      <Timeline mode="left">
        <Timeline.Item label="活跃状态" color="green">
          <Title level={5}>☀️ 活跃状态 (Active)</Title>
          <Paragraph>
            <Text strong>共轭能: 高 (High)</Text>
            <br />
            Agent处于完全活跃状态，实时响应用户请求，记忆系统正常工作。
            所有功能模块都处于待命状态。
          </Paragraph>
        </Timeline.Item>

        <Timeline.Item label="浅层睡眠" color="orange">
          <Title level={5}>⭐ 浅层睡眠 (Light Sleep)</Title>
          <Paragraph>
            <Text strong>共轭能: 中-高 (Medium-High)</Text>
            <br />
            Agent进入轻度休息状态，但仍可快速唤醒。
            此阶段会扫描最近7天的对话日志，进行去重和重要性标记。
            适合短暂休息或低峰期使用。
          </Paragraph>
        </Timeline.Item>

        <Timeline.Item label="REM阶段" color="blue">
          <Title level={5}>💭 REM阶段 (Rapid Eye Movement)</Title>
          <Paragraph>
            <Text strong>共轭能: 中 (Medium)</Text>
            <br />
            模拟人类的REM睡眠，Agent进行"梦境处理"。
            提取对话主题，发现跨会话的关联模式，生成反思摘要。
            识别"持久真理"(Lasting Truths)，为长期记忆做准备。
            唤醒需要较长时间。
          </Paragraph>
        </Timeline.Item>

        <Timeline.Item label="深层睡眠" color="purple">
          <Title level={5}>🌙 深层睡眠 (Deep Sleep)</Title>
          <Paragraph>
            <Text strong>共轭能: 低 (Low)</Text>
            <br />
            Agent进入深度整合状态，大部分功能暂停。
            对候选记忆进行六维加权评分(相关性、频率、时效性、多样性、整合度、概念丰富度)。
            高分记忆在数据库中标记为`long_term`长期记忆，并更新评分。
            执行遗忘曲线算法，自动冷藏、归档、删除过期记忆。
            唤醒需要重新加载上下文。
          </Paragraph>
        </Timeline.Item>
      </Timeline>

      <Divider />

      <Card type="inner" title="六维评分系统">
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Statistic title="相关性 (30%)" value="与用户长期兴趣的相关程度" />
          </Col>
          <Col span={12}>
            <Statistic title="频率 (24%)" value="记忆被访问的频率" />
          </Col>
          <Col span={12}>
            <Statistic title="时效性 (15%)" value="记忆的时效性权重" />
          </Col>
          <Col span={12}>
            <Statistic title="查询多样性 (15%)" value="被查询的模式多样性" />
          </Col>
          <Col span={12}>
            <Statistic title="整合度 (10%)" value="与其他记忆的关联程度" />
          </Col>
          <Col span={12}>
            <Statistic title="概念丰富度 (6%)" value="内容的概念密度" />
          </Col>
        </Row>
      </Card>
    </div>
  );
}

// ============ 侧边栏B：睡眠管理主组件 ============

function SleepManagementSidebar() {
  const [activeTab, setActiveTab] = useState('status');

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <AgentInfoBar />
      <Title level={4} style={{ padding: '0 16px', marginTop: 16 }}>
        <MoonOutlined /> HumanThinking 睡眠管理
      </Title>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        type="card"
        style={{ flex: 1, overflow: 'auto' }}
      >
        <Tabs.TabPane tab={<span><MoonOutlined />睡眠状态</span>} key="status">
          <SleepStatusPanel />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><SettingOutlined />参数配置</span>} key="config">
          <SleepConfigPanel />
        </Tabs.TabPane>
        <Tabs.TabPane tab={<span><BookOutlined />共轭能说明</span>} key="energy">
          <SleepEnergyPanel />
        </Tabs.TabPane>
      </Tabs>
    </div>
  );
}

// ============ 原有Dashboard (保留兼容) ============

function HumanThinkingDashboard() {
  return <MemoryManagementSidebar />;
}

// ============ 导出 ============

export {
  MemoryManagementSidebar,
  SleepManagementSidebar,
  HumanThinkingDashboard,
  MemoryStatsPanel,
  MemorySearch,
  SessionList,
  EmotionIndicator,
  MemoryTimeline,
  ConfigPanel,
  SleepStatusPanel,
  SleepConfigPanel,
  SleepEnergyPanel,
  AgentInfoBar
};

export default MemoryManagementSidebar;
