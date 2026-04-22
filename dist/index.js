/** HumanThinking Memory Manager - Frontend Plugin Entry. */

const { React, antd } = window.QwenPaw.host;
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
  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '🧠 HumanThinking 记忆管理'),
    React.createElement(Paragraph, null, '跨 Session 认知与情感连续性记忆管理系统'),
    React.createElement(Card, { title: '统计', style: { marginTop: 16 } },
      React.createElement(Row, { gutter: 16 },
        React.createElement(Col, { span: 6 },
          React.createElement(Card, null,
            React.createElement(Statistic, { title: '总记忆数', value: 0 })
          )
        ),
        React.createElement(Col, { span: 6 },
          React.createElement(Card, null,
            React.createElement(Statistic, { title: '跨Session记忆', value: 0 })
          )
        ),
        React.createElement(Col, { span: 6 },
          React.createElement(Card, null,
            React.createElement(Statistic, { title: '冷藏记忆', value: 0 })
          )
        ),
        React.createElement(Col, { span: 6 },
          React.createElement(Card, null,
            React.createElement(Statistic, { title: '活跃会话', value: 0 })
          )
        )
      )
    ),
    React.createElement(Space, { style: { marginTop: 16 } },
      React.createElement(Button, { onClick: () => message.success('刷新成功') }, '🔄 刷新')
    )
  );
}

function MemorySettings() {
  const [config, setConfig] = React.useState(getConfig());
  const [saving, setSaving] = React.useState(false);

  const handleChange = (key, value) => {
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

  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '⚙️ 记忆设置'),
    React.createElement(Card, { title: '功能开关', style: { marginTop: 16 } },
      React.createElement('div', { style: { display: 'flex', flexDirection: 'column', gap: 16 } },
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '跨Session记忆'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '新Session自动继承相关历史记忆')
          ),
          React.createElement(Switch, {
            checked: config.enable_cross_session,
            onChange: (checked) => handleChange('enable_cross_session', checked),
            loading: saving
          })
        ),
        React.createElement(Divider, { style: { margin: '8px 0' } }),
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '情感连续性'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '跟踪对话情感变化')
          ),
          React.createElement(Switch, {
            checked: config.enable_emotion,
            onChange: (checked) => handleChange('enable_emotion', checked),
            loading: saving
          })
        ),
        React.createElement(Divider, { style: { margin: '8px 0' } }),
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '会话隔离'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '按AgentID + UserID + SessionID隔离')
          ),
          React.createElement(Switch, {
            checked: config.enable_session_isolation,
            onChange: (checked) => handleChange('enable_session_isolation', checked),
            loading: saving
          })
        ),
        React.createElement(Divider, { style: { margin: '8px 0' } }),
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '记忆冷藏'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '7天无访问自动冷藏')
          ),
          React.createElement(Switch, {
            checked: config.enable_memory_freeze,
            onChange: (checked) => handleChange('enable_memory_freeze', checked),
            loading: saving
          })
        )
      )
    ),
    React.createElement(Alert,
      {
        message: '提示',
        description: '修改设置后，部分功能需要刷新页面或新会话才能完全生效',
        type: 'info',
        showIcon: true,
        style: { marginTop: 16 }
      }
    )
  );
}

class HumanThinkingPlugin {
  id = "humanthinking-memory";

  setup() {
    window.QwenPaw.registerRoutes?.(this.id, [
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
    console.info('[HumanThinking] Plugin loaded successfully');
  }
}

new HumanThinkingPlugin().setup();

export {};
