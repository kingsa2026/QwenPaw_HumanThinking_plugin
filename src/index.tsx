/** HumanThinking Memory Manager - Frontend Plugin Entry. */

const { React, antd } = (window as any).QwenPaw.host;
const { Typography, Card, Table, Statistic, Row, Col, Tag, Button, Space, Descriptions, Switch, Divider, Alert, message } = antd;
const { Title, Paragraph, Text } = Typography;

const CONFIG_KEY = 'humanthinking_config';

const defaultConfig = {
  enable_cross_session: true,
  enable_emotion: true,
  enable_session_isolation: true,
  enable_memory_freeze: true,
  session_idle_timeout: 180,
  refresh_interval: 5,
  max_results: 5,
  max_memory_chars: 150,
};

interface MemoryStats {
  total_memories: number;
  cross_session_memories: number;
  frozen_memories: number;
  active_sessions: number;
}

interface MemoryRecord {
  id: number;
  content: string;
  role: string;
  session_id: string;
  importance: number;
  memory_type: string;
  created_at: string;
}

function getConfig() {
  try {
    const stored = localStorage.getItem(CONFIG_KEY);
    if (stored) {
      return { ...defaultConfig, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.error('Failed to load config:', e);
  }
  return defaultConfig;
}

function saveConfig(config: any) {
  try {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
    return true;
  } catch (e) {
    console.error('Failed to save config:', e);
    return false;
  }
}

function HumanThinkingDashboard() {
  const [stats, setStats] = React.useState<MemoryStats | null>(null);
  const [recentMemories, setRecentMemories] = React.useState<MemoryRecord[]>([]);
  const [loading, setLoading] = React.useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = (window as any).QwenPaw.host?.getApiToken?.();
      const baseUrl = (window as any).QwenPaw.host?.getApiUrl?.('');

      const statsRes = await fetch(`${baseUrl}api/plugin/humanthinking/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const statsData = await statsRes.json();
      setStats(statsData);

      const memoriesRes = await fetch(`${baseUrl}api/plugin/humanthinking/recent`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const memoriesData = await memoriesRes.json();
      setRecentMemories(memoriesData.memories || []);
    } catch (e) {
      console.error('Failed to fetch memory data:', e);
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
      <Paragraph>
        跨 Session 认知与情感连续性记忆管理系统
      </Paragraph>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总记忆数" value={stats?.total_memories || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="跨Session记忆" value={stats?.cross_session_memories || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="冷藏记忆" value={stats?.frozen_memories || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="活跃会话" value={stats?.active_sessions || 0} />
          </Card>
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

function MemorySettings() {
  const [config, setConfig] = React.useState(getConfig());
  const [saving, setSaving] = React.useState(false);

  const handleChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    setSaving(true);
    
    if (saveConfig(newConfig)) {
      setConfig(newConfig);
      message.success('设置已保存');
    } else {
      message.error('保存失败');
    }
    
    setSaving(false);
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>⚙️ 记忆设置</Title>
      
      <Card title="功能开关" style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>跨Session记忆</Text>
              <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                新Session自动继承相关历史记忆
              </Paragraph>
            </div>
            <Switch 
              checked={config.enable_cross_session}
              onChange={(checked) => handleChange('enable_cross_session', checked)}
              loading={saving}
            />
          </div>
          
          <Divider style={{ margin: '8px 0' }} />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>情感连续性</Text>
              <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                跟踪对话情感变化，在上下文中注入情感状态
              </Paragraph>
            </div>
            <Switch 
              checked={config.enable_emotion}
              onChange={(checked) => handleChange('enable_emotion', checked)}
              loading={saving}
            />
          </div>
          
          <Divider style={{ margin: '8px 0' }} />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>会话隔离</Text>
              <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                按AgentID + UserID + SessionID隔离记忆
              </Paragraph>
            </div>
            <Switch 
              checked={config.enable_session_isolation}
              onChange={(checked) => handleChange('enable_session_isolation', checked)}
              loading={saving}
            />
          </div>
          
          <Divider style={{ margin: '8px 0' }} />
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Text strong>记忆冷藏</Text>
              <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                7天无访问自动冷藏，释放缓存空间
              </Paragraph>
            </div>
            <Switch 
              checked={config.enable_memory_freeze}
              onChange={(checked) => handleChange('enable_memory_freeze', checked)}
              loading={saving}
            />
          </div>
        </div>
      </Card>

      <Card title="高级设置" style={{ marginTop: 16 }}>
        <Descriptions column={1} size="small">
          <Descriptions.Item label="会话空闲超时">
            {config.session_idle_timeout} 秒
          </Descriptions.Item>
          <Descriptions.Item label="刷新间隔">
            {config.refresh_interval} 轮
          </Descriptions.Item>
          <Descriptions.Item label="最大返回数">
            {config.max_results} 条
          </Descriptions.Item>
          <Descriptions.Item label="单条记忆最大字符">
            {config.max_memory_chars} 字符
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Alert 
        message="提示" 
        description="修改设置后，部分功能需要刷新页面或新会话才能完全生效" 
        type="info" 
        showIcon 
        style={{ marginTop: 16 }}
      />
    </div>
  );
}

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
        path: '/plugin/humanthinking/settings',
        component: MemorySettings,
        label: '记忆设置',
        icon: '⚙️',
        priority: 11,
      },
    ]);
  }
}

new HumanThinkingPlugin().setup();

export {};
