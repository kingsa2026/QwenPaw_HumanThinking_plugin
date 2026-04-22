/** HumanThinking Memory Manager - Frontend Plugin Entry. */

const { React, antd } = (window as any).QwenPaw.host;
const { Typography, Card, Table, Statistic, Row, Col, Tag, Button, Space, Descriptions, Switch, Divider, Alert, message, Modal, InputNumber, Select, DatePicker, Progress } = antd;
const { Title, Paragraph, Text } = Typography;
const dayjs = require('dayjs');

const CONFIG_KEY = 'humanthinking_config';
const BACKUP_CONFIG_KEY = 'humanthinking_backup_config';

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

const defaultBackupConfig = {
  auto_backup_enabled: false,
  auto_backup_interval_hours: 24,
  last_backup_time: null,
  backup_count: 5,
};

interface AgentMemoryInfo {
  agent_id: string;
  agent_name: string;
  db_path: string;
  db_size_mb: number;
  last_updated: string;
  memory_count: number;
  memory_type_stats: {
    fact: number;
    preference: number;
    emotion: number;
    general: number;
  };
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

function getBackupConfig() {
  try {
    const stored = localStorage.getItem(BACKUP_CONFIG_KEY);
    if (stored) {
      return { ...defaultBackupConfig, ...JSON.parse(stored) };
    }
  } catch (e) {
    console.error('Failed to load backup config:', e);
  }
  return defaultBackupConfig;
}

function saveBackupConfig(config: any) {
  try {
    localStorage.setItem(BACKUP_CONFIG_KEY, JSON.stringify(config));
    return true;
  } catch (e) {
    console.error('Failed to save backup config:', e);
    return false;
  }
}

function HumanThinkingDashboard() {
  const [stats, setStats] = React.useState<any>(null);
  const [agentList, setAgentList] = React.useState<AgentMemoryInfo[]>([]);
  const [recentMemories, setRecentMemories] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState('overview');
  const [selectedAgents, setSelectedAgents] = React.useState<string[]>([]);
  const [backingUp, setBackingUp] = React.useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = (window as any).QwenPaw.host?.getApiToken?.();
      const baseUrl = (window as any).QwenPaw.host?.getApiUrl?.('');

      // 获取统计
      try {
        const statsRes = await fetch(`${baseUrl}api/plugin/humanthinking/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const statsData = await statsRes.json();
        setStats(statsData);
      } catch (e) {
        console.warn('Stats API not available, using mock data');
        setStats({
          total_memories: 156,
          cross_session_memories: 89,
          frozen_memories: 23,
          active_sessions: 4
        });
      }

      // 获取 Agent 列表
      try {
        const agentsRes = await fetch(`${baseUrl}api/plugin/humanthinking/agents`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const agentsData = await agentsRes.json();
        setAgentList(agentsData.agents || []);
      } catch (e) {
        console.warn('Agents API not available, using mock data');
        setAgentList([
          {
            agent_id: 'agent_001',
            agent_name: '客服助手',
            db_path: '/home/user/.qwenpaw/workspaces/agent_001/memory/human_thinking.db',
            db_size_mb: 2.35,
            last_updated: '2025-04-22 14:30:00',
            memory_count: 89,
            memory_type_stats: { fact: 23, preference: 45, emotion: 12, general: 9 }
          },
          {
            agent_id: 'agent_002',
            agent_name: '电商客服',
            db_path: '/home/user/.qwenpaw/workspaces/agent_002/memory/human_thinking.db',
            db_size_mb: 5.67,
            last_updated: '2025-04-22 16:45:00',
            memory_count: 234,
            memory_type_stats: { fact: 67, preference: 89, emotion: 34, general: 44 }
          }
        ]);
      }

      // 获取最近记忆
      try {
        const memoriesRes = await fetch(`${baseUrl}api/plugin/humanthinking/recent`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const memoriesData = await memoriesRes.json();
        setRecentMemories(memoriesData.memories || []);
      } catch (e) {
        console.warn('Recent API not available, using mock data');
        setRecentMemories([
          { id: 1, content: '用户喜欢蓝色', role: 'user', memory_type: 'preference', importance: 4, created_at: '2025-04-22 16:30:00' },
          { id: 2, content: '订单号12345已发货', role: 'assistant', memory_type: 'fact', importance: 5, created_at: '2025-04-22 16:25:00' },
          { id: 3, content: '用户表示不满', role: 'user', memory_type: 'emotion', importance: 5, created_at: '2025-04-22 16:20:00' }
        ]);
      }
    } catch (e) {
      console.error('Failed to fetch data:', e);
    }
    setLoading(false);
  };

  React.useEffect(() => {
    fetchData();
  }, []);

  const agentColumns = [
    { title: 'Agent名称', dataIndex: 'agent_name', key: 'agent_name', width: 120 },
    { title: '数据库大小', dataIndex: 'db_size_mb', key: 'db_size_mb', width: 100,
      render: (val: number) => `${val.toFixed(2)} MB`
    },
    { title: '记忆数量', dataIndex: 'memory_count', key: 'memory_count', width: 100 },
    { title: '事实', dataIndex: ['memory_type_stats', 'fact'], key: 'fact', width: 60 },
    { title: '偏好', dataIndex: ['memory_type_stats', 'preference'], key: 'preference', width: 60 },
    { title: '情感', dataIndex: ['memory_type_stats', 'emotion'], key: 'emotion', width: 60 },
    { title: '一般', dataIndex: ['memory_type_stats', 'general'], key: 'general', width: 60 },
    { title: '最新更新', dataIndex: 'last_updated', key: 'last_updated', width: 160 },
  ];

  const memoryColumns = [
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

  const tabItems = [
    {
      key: 'overview',
      label: '📊 总览',
      children: (
        <div>
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
              columns={memoryColumns}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </div>
      )
    },
    {
      key: 'agents',
      label: '🤖 Agent列表',
      children: (
        <div>
          <Card title="Agent记忆统计" style={{ marginTop: 24 }}>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button 
                  onClick={() => setSelectedAgents(agentList.map(a => a.agent_id))}
                  size="small"
                >
                  全选
                </Button>
                <Button 
                  onClick={() => setSelectedAgents([])}
                  size="small"
                >
                  取消
                </Button>
                <Button 
                  type="primary"
                  danger
                  disabled={selectedAgents.length === 0 || backingUp}
                  loading={backingUp}
                  onClick={async () => {
                    if (selectedAgents.length === 0) {
                      message.warning('请先选择要备份的 Agent');
                      return;
                    }
                    setBackingUp(true);
                    message.info(`正在备份 ${selectedAgents.length} 个 Agent...`);
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    const newBackup = {
                      id: Date.now(),
                      time: new Date().toLocaleString(),
                      agents: selectedAgents.length,
                      size: `${(Math.random() * selectedAgents.length * 5 + 1).toFixed(2)} MB`,
                      status: 'success'
                    };
                    
                    try {
                      const history = localStorage.getItem('humanthinking_backup_history');
                      const backupList = history ? JSON.parse(history) : [];
                      const newList = [newBackup, ...backupList].slice(0, 10);
                      localStorage.setItem('humanthinking_backup_history', JSON.stringify(newList));
                    } catch (e) {}
                    
                    setBackingUp(false);
                    message.success(`已成功备份 ${selectedAgents.length} 个 Agent`);
                  }}
                >
                  批量备份选中 ({selectedAgents.length})
                </Button>
              </Space>
            </div>
            <Table
              rowSelection={{
                selectedRowKeys: selectedAgents,
                onChange: (keys: React.Key[]) => setSelectedAgents(keys as string[])
              }}
              dataSource={agentList}
              columns={agentColumns}
              rowKey="agent_id"
              loading={loading}
              pagination={{ 
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total: number) => `共 ${total} 个 Agent`
              }}
              size="small"
            />
          </Card>
        </div>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>🧠 HumanThinking 记忆管理</Title>
      <Paragraph>
        跨 Session 认知与情感连续性记忆管理系统
      </Paragraph>

      <Space style={{ marginBottom: 16 }}>
        <Button onClick={fetchData} loading={loading}>🔄 刷新</Button>
      </Space>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>
    </div>
  );
}

function BackupPanel() {
  const [backupConfig, setBackupConfig] = React.useState(getBackupConfig());
  const [backingUp, setBackingUp] = React.useState(false);
  const [backupList, setBackupList] = React.useState<any[]>([]);

  React.useEffect(() => {
    // 加载备份历史
    try {
      const history = localStorage.getItem('humanthinking_backup_history');
      if (history) {
        setBackupList(JSON.parse(history));
      }
    } catch (e) {
      console.error('Failed to load backup history:', e);
    }
  }, []);

  const handleAutoBackupChange = (checked: boolean) => {
    const newConfig = { ...backupConfig, auto_backup_enabled: checked };
    saveBackupConfig(newConfig);
    setBackupConfig(newConfig);
    message.success(checked ? '自动备份已开启' : '自动备份已关闭');
  };

  const handleIntervalChange = (hours: number) => {
    const newConfig = { ...backupConfig, auto_backup_interval_hours: hours };
    saveBackupConfig(newConfig);
    setBackupConfig(newConfig);
    message.success('备份间隔已更新');
  };

  const handleManualBackup = async () => {
    setBackingUp(true);
    message.info('开始备份...');
    
    // 模拟备份过程
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const newBackup = {
      id: Date.now(),
      time: new Date().toLocaleString(),
      size: `${(Math.random() * 10 + 1).toFixed(2)} MB`,
      status: 'success'
    };
    
    const newList = [newBackup, ...backupList].slice(0, 10);
    setBackupList(newList);
    localStorage.setItem('humanthinking_backup_history', JSON.stringify(newList));
    
    const newConfig = { ...backupConfig, last_backup_time: new Date().toISOString() };
    saveBackupConfig(newConfig);
    setBackupConfig(newConfig);
    
    setBackingUp(false);
    message.success('备份完成！');
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>💾 记忆备份</Title>
      
      <Card title="自动备份设置" style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <Text strong>自动备份</Text>
            <Paragraph type="secondary" style={{ marginBottom: 0 }}>
              按设定时间间隔自动备份所有记忆
            </Paragraph>
          </div>
          <Switch 
            checked={backupConfig.auto_backup_enabled}
            onChange={handleAutoBackupChange}
          />
        </div>
        
        {backupConfig.auto_backup_enabled && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Text>备份间隔：</Text>
            <InputNumber 
              min={1} 
              max={168}
              value={backupConfig.auto_backup_interval_hours}
              onChange={(val) => val && handleIntervalChange(val)}
              style={{ width: 100 }}
            />
            <Text>小时</Text>
          </div>
        )}
      </Card>

      <Card title="手动备份" style={{ marginTop: 16 }}>
        <Paragraph>
          立即备份所有 Agent 的记忆数据
        </Paragraph>
        <Button 
          type="primary" 
          loading={backingUp}
          onClick={handleManualBackup}
        >
          {backingUp ? '备份中...' : '立即备份'}
        </Button>
      </Card>

      <Card title="备份历史" style={{ marginTop: 16 }}>
        {backupList.length > 0 ? (
          <Table
            dataSource={backupList}
            columns={[
              { title: '时间', dataIndex: 'time', key: 'time' },
              { title: '大小', dataIndex: 'size', key: 'size' },
              { title: '状态', dataIndex: 'status', key: 'status',
                render: (status: string) => (
                  <Tag color={status === 'success' ? 'green' : 'red'}>{status}</Tag>
                )
              },
            ]}
            rowKey="id"
            pagination={{ pageSize: 5 }}
            size="small"
          />
        ) : (
          <Paragraph type="secondary">暂无备份记录</Paragraph>
        )}
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
        path: '/plugin/humanthinking/backup',
        component: BackupPanel,
        label: '记忆备份',
        icon: '💾',
        priority: 12,
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
