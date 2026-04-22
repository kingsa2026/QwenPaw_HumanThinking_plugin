/** HumanThinking Memory Manager - Frontend Plugin Entry. */

const { React, antd } = (window as any).QwenPaw.host;
const { Typography, Card, Table, Statistic, Row, Col, Tag, Button, Space, Descriptions } = antd;
const { Title, Paragraph, Text } = Typography;

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
  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>⚙️ 记忆设置</Title>
      <Card style={{ marginTop: 16 }}>
        <Descriptions column={1}>
          <Descriptions.Item label="记忆类型">
            <Tag color="blue">HumanThinking</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="版本">1.1.0</Descriptions.Item>
          <Descriptions.Item label="特性">
            <Space>
              <Tag>跨Session</Tag>
              <Tag>情感连续</Tag>
              <Tag>会话隔离</Tag>
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>
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
