/** HumanThinking Memory Manager - Frontend Plugin Entry v1.2.0 */

const { React, antd } = (window as any).QwenPaw.host;
const { 
  Typography, Card, Table, Statistic, Row, Col, Tag, Button, Space, 
  Descriptions, Input, List, Timeline, Badge, Switch, Slider, Form,
  Tabs, Empty, Spin, Divider, Tooltip, Progress
} = antd;
const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

// ============ 类型定义 ============
interface MemoryRecord {
  id: number;
  content: string;
  role: string;
  session_id: string;
  importance: number;
  memory_type: string;
  created_at: string;
}

interface SessionInfo {
  session_id: string;
  agent_id: string;
  user_id?: string;
  created_at: string;
  last_active: string;
  memory_count: number;
  status: string;
}

interface EmotionState {
  emotion: string;
  intensity: number;
  timestamp: string;
}

interface MemoryStats {
  total_memories: number;
  cross_session_memories: number;
  frozen_memories: number;
  active_sessions: number;
}

// ============ API 工具函数 ============
const getApiBase = () => {
  const baseUrl = (window as any).QwenPaw.host?.getApiUrl?.('');
  // getApiUrl 可能已经包含 /api/ 前缀，避免重复
  if (baseUrl && baseUrl.includes('/api/')) {
    return `${baseUrl}plugins/humanthinking`;
  }
  return `${baseUrl}api/plugins/humanthinking`;
};

const getHeaders = () => {
  const token = (window as any).QwenPaw.host?.getApiToken?.();
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

// ============ 1. 记忆搜索组件 ============
function MemorySearch() {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<MemoryRecord[]>([]);
  const [loading, setLoading] = React.useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/search`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ query, limit: 20 })
      });
      const data = await resp.json();
      setResults(data.memories || []);
    } catch (e) {
      console.error('Search failed:', e);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}>🔍 记忆搜索</Title>
      <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
        <Input 
          placeholder="搜索历史记忆..." 
          value={query}
          onChange={e => setQuery(e.target.value)}
          onPressEnter={handleSearch}
        />
        <Button type="primary" onClick={handleSearch} loading={loading}>搜索</Button>
      </Space.Compact>
      
      <List
        dataSource={results}
        renderItem={(item: MemoryRecord) => (
          <List.Item>
            <Card size="small" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <Text ellipsis style={{ maxWidth: '70%' }}>{item.content}</Text>
                <Space>
                  <Tag color={item.memory_type === 'fact' ? 'blue' : item.memory_type === 'emotion' ? 'red' : 'green'}>
                    {item.memory_type}
                  </Tag>
                  <Tag>重要性: {item.importance}</Tag>
                </Space>
              </div>
              <div style={{ marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {item.role} · {item.created_at}
                </Text>
              </div>
            </Card>
          </List.Item>
        )}
        locale={{ emptyText: '输入关键词搜索记忆' }}
      />
    </div>
  );
}

// ============ 2. 情感状态指示器 ============
function EmotionIndicator() {
  const [emotion, setEmotion] = React.useState<EmotionState | null>(null);
  const [history, setHistory] = React.useState<EmotionState[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchEmotion = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/emotion`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setEmotion({
        emotion: data.current_emotion,
        intensity: data.intensity,
        timestamp: new Date().toISOString()
      });
      setHistory(data.history || []);
    } catch (e) {
      console.error('Failed to fetch emotion:', e);
    }
    setLoading(false);
  };

  React.useEffect(() => {
    fetchEmotion();
    const interval = setInterval(fetchEmotion, 30000); // 30秒刷新
    return () => clearInterval(interval);
  }, []);

  const getEmotionColor = (emotion: string) => {
    const colors: Record<string, string> = {
      'satisfied': 'green',
      'frustrated': 'red',
      'neutral': 'blue',
      'excited': 'orange',
      'sad': 'purple'
    };
    return colors[emotion] || 'blue';
  };

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}>💝 情感状态</Title>
      {loading && !emotion ? (
        <Spin />
      ) : emotion ? (
        <>
          <Card size="small" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <Badge 
                status="processing" 
                color={getEmotionColor(emotion.emotion)}
                text={<Text strong style={{ fontSize: 18 }}>{emotion.emotion}</Text>}
              />
              <Progress 
                percent={emotion.intensity * 100} 
                size="small" 
                style={{ width: 120 }}
                showInfo={false}
              />
            </div>
          </Card>
          
          <Title level={5}>情感历史</Title>
          <Timeline>
            {history.slice(0, 5).map((item, index) => (
              <Timeline.Item key={index} color={getEmotionColor(item.emotion)}>
                <div>{item.emotion} (强度: {(item.intensity * 100).toFixed(0)}%)</div>
                <Text type="secondary" style={{ fontSize: 12 }}>{item.timestamp}</Text>
              </Timeline.Item>
            ))}
          </Timeline>
        </>
      ) : (
        <Empty description="暂无情感数据" />
      )}
    </div>
  );
}

// ============ 3. 会话列表 ============
function SessionList() {
  const [sessions, setSessions] = React.useState<SessionInfo[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchSessions = async () => {
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
  };

  React.useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}>💬 会话列表</Title>
      <List
        loading={loading}
        dataSource={sessions}
        renderItem={(item: SessionInfo) => (
          <List.Item>
            <Card size="small" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <Text strong>{item.session_id.slice(0, 8)}...</Text>
                  <div>
                    <Tag size="small" color={item.status === 'active' ? 'green' : 'default'}>
                      {item.status}
                    </Tag>
                    <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                      {item.memory_count} 条记忆
                    </Text>
                  </div>
                </div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {item.last_active}
                </Text>
              </div>
            </Card>
          </List.Item>
        )}
        locale={{ emptyText: '暂无会话' }}
      />
    </div>
  );
}

// ============ 4. 记忆统计面板 ============
function MemoryStatsPanel() {
  const [stats, setStats] = React.useState<MemoryStats | null>(null);
  const [loading, setLoading] = React.useState(false);

  const fetchStats = async () => {
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
  };

  React.useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // 60秒刷新
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}>📊 记忆统计</Title>
      <Row gutter={[8, 8]}>
        <Col span={12}>
          <Card size="small">
            <Statistic 
              title="总记忆" 
              value={stats?.total_memories || 0} 
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small">
            <Statistic 
              title="跨会话" 
              value={stats?.cross_session_memories || 0}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small">
            <Statistic 
              title="冷藏" 
              value={stats?.frozen_memories || 0}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small">
            <Statistic 
              title="活跃会话" 
              value={stats?.active_sessions || 0}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

// ============ 5. 记忆时间线 ============
function MemoryTimeline() {
  const [memories, setMemories] = React.useState<MemoryRecord[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchTimeline = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/memories/timeline`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setMemories(data || []);
    } catch (e) {
      console.error('Failed to fetch timeline:', e);
    }
    setLoading(false);
  };

  React.useEffect(() => {
    fetchTimeline();
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}>📅 记忆时间线</Title>
      <Timeline mode="left">
        {memories.map((item, index) => (
          <Timeline.Item 
            key={index}
            label={item.created_at}
            color={item.importance > 3 ? 'red' : item.importance > 1 ? 'blue' : 'gray'}
          >
            <Text>{item.content.slice(0, 50)}...</Text>
            <div>
              <Tag size="small">{item.memory_type}</Tag>
              <Tag size="small">重要性: {item.importance}</Tag>
            </div>
          </Timeline.Item>
        ))}
      </Timeline>
      {memories.length === 0 && <Empty description="暂无记忆记录" />}
    </div>
  );
}

// ============ 6. 配置面板 ============
function ConfigPanel() {
  const [config, setConfig] = React.useState<any>({});
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  const fetchConfig = async () => {
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
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${getApiBase()}/config`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(config)
      });
    } catch (e) {
      console.error('Failed to save config:', e);
    }
    setSaving(false);
  };

  React.useEffect(() => {
    fetchConfig();
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <Title level={4}>⚙️ 配置</Title>
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

// ============ 7. 主侧边栏组件 ============
function HumanThinkingSidebar() {
  const [activeTab, setActiveTab] = React.useState('search');

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        type="card"
        size="small"
        style={{ flex: 1 }}
      >
        <TabPane tab="🔍" key="search">
          <MemorySearch />
        </TabPane>
        <TabPane tab="📊" key="stats">
          <MemoryStatsPanel />
        </TabPane>
        <TabPane tab="💬" key="sessions">
          <SessionList />
        </TabPane>
        <TabPane tab="💝" key="emotion">
          <EmotionIndicator />
        </TabPane>
        <TabPane tab="📅" key="timeline">
          <MemoryTimeline />
        </TabPane>
        <TabPane tab="⚙️" key="config">
          <ConfigPanel />
        </TabPane>
      </Tabs>
    </div>
  );
}

// ============ 8. Dashboard (原有) ============
function HumanThinkingDashboard() {
  const [stats, setStats] = React.useState<MemoryStats | null>(null);
  const [recentMemories, setRecentMemories] = React.useState<MemoryRecord[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/stats`, {
        headers: getHeaders()
      });
      const data = await resp.json();
      setStats(data);

      const memoriesResp = await fetch(`${getApiBase()}/memories/recent`, {
        headers: getHeaders()
      });
      const memoriesData = await memoriesResp.json();
      setRecentMemories(memoriesData.memories || []);
    } catch (e) {
      console.error('Failed to fetch data:', e);
    }
    setLoading(false);
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const columns = [
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '角色', dataIndex: 'role', key: 'role', width: 80 },
    { title: '类型', dataIndex: 'memory_type', key: 'memory_type', width: 100,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          'fact': 'blue', 'preference': 'green', 'emotion': 'red', 'general': 'default'
        };
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
      }
    },
    { title: '重要性', dataIndex: 'importance', key: 'importance', width: 100,
      render: (val: number) => `${val}/5`
    },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>🧠 HumanThinking 记忆管理</Title>
      <Paragraph>跨 Session 认知与情感连续性记忆管理系统</Paragraph>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card><Statistic title="总记忆数" value={stats?.total_memories || 0} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="跨Session记忆" value={stats?.cross_session_memories || 0} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="冷藏记忆" value={stats?.frozen_memories || 0} /></Card>
        </Col>
        <Col span={6}>
          <Card><Statistic title="活跃会话" value={stats?.active_sessions || 0} /></Card>
        </Col>
      </Row>

      <Card title="最近记忆" style={{ marginTop: 24 }}>
        <Table
          dataSource={recentMemories}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>

      <Card title="操作" style={{ marginTop: 24 }}>
        <Space>
          <Button onClick={fetchData} loading={loading}>刷新</Button>
        </Space>
      </Card>
    </div>
  );
}

// ============ 插件注册 ============
class HumanThinkingPlugin {
  readonly id = "humanthinking-memory";

  setup(): void {
    (window as any).QwenPaw.registerRoutes?.(this.id, [
      {
        path: '/plugin/humanthinking/dashboard',
        component: HumanThinkingDashboard,
        label: '记忆管理',
        icon: '🧠',
        priority: 10,
      },
      {
        path: '/plugin/humanthinking/sidebar',
        component: HumanThinkingSidebar,
        label: '记忆助手',
        icon: '🧠',
        priority: 11,
        sidebar: true, // 标记为侧边栏组件
      },
    ]);
  }
}

new HumanThinkingPlugin().setup();

export {};
