/** HumanThinking Memory Manager - Frontend Plugin Entry. */

var React = window.QwenPaw.host.React;
var antd = window.QwenPaw.host.antd;
var Switch = antd.Switch;
var Card = antd.Card;
var Typography = antd.Typography;
var Row = antd.Row;
var Col = antd.Col;
var Button = antd.Button;
var Divider = antd.Divider;
var Alert = antd.Alert;
var Space = antd.Space;
var Tabs = antd.Tabs;
var Table = antd.Table;
var Tag = antd.Tag;

var Title = Typography.Title;
var Paragraph = Typography.Paragraph;
var Text = Typography.Text;

var CONFIG_KEY = 'humanthinking_config';
var defaultConfig = {
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
    var stored = localStorage.getItem(CONFIG_KEY);
    if (stored) {
      var parsed = JSON.parse(stored);
      var result = {};
      Object.keys(defaultConfig).forEach(function(key) {
        result[key] = parsed[key] !== undefined ? parsed[key] : defaultConfig[key];
      });
      return result;
    }
  } catch (e) {
    console.error('Failed to load config:', e);
  }
  return defaultConfig;
}

function saveConfig(config) {
  try {
    localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
    return true;
  } catch (e) {
    console.error('Failed to save config:', e);
    return false;
  }
}

function Dashboard() {
  var statCardStyle = { padding: 16, textAlign: 'center', background: 'var(--ant component-background)', borderRadius: 8, border: '1px solid var(--ant border-color-split)' };
  var statNumStyle = { fontSize: 24, fontWeight: 'bold', color: '#1677ff' };
  var statLabelStyle = { fontSize: 12, color: 'var(--ant text-color-secondary)', marginTop: 4 };
  
  var mockAgents = [
    { agent_id: 'agent_001', agent_name: '客服助手', db_size_mb: 2.35, memory_count: 89, last_updated: '2025-04-22 14:30' },
    { agent_id: 'agent_002', agent_name: '电商客服', db_size_mb: 5.67, memory_count: 234, last_updated: '2025-04-22 16:45' },
  ];
  
  var agentColumns = [
    { title: 'Agent名称', dataIndex: 'agent_name', key: 'agent_name' },
    { title: '数据库大小', dataIndex: 'db_size_mb', key: 'db_size_mb', render: function(val) { return val.toFixed(2) + ' MB'; } },
    { title: '记忆数量', dataIndex: 'memory_count', key: 'memory_count' },
    { title: '更新时间', dataIndex: 'last_updated', key: 'last_updated' },
  ];
  
  var tabItems = [
    {
      key: 'overview',
      label: '📊 总览',
      children: React.createElement('div', null,
        React.createElement(Row, { gutter: 16, style: { marginTop: 24 } },
          React.createElement(Col, { span: 6 },
            React.createElement('div', { style: statCardStyle },
              React.createElement('div', { style: statNumStyle }, '2'),
              React.createElement('div', { style: statLabelStyle }, 'Agent数')
            )
          ),
          React.createElement(Col, { span: 6 },
            React.createElement('div', { style: statCardStyle },
              React.createElement('div', { style: statNumStyle }, '323'),
              React.createElement('div', { style: statLabelStyle }, '总记忆数')
            )
          ),
          React.createElement(Col, { span: 6 },
            React.createElement('div', { style: statCardStyle },
              React.createElement('div', { style: statNumStyle }, '156'),
              React.createElement('div', { style: statLabelStyle }, '跨Session记忆')
            )
          ),
          React.createElement(Col, { span: 6 },
            React.createElement('div', { style: statCardStyle },
              React.createElement('div', { style: statNumStyle }, '3'),
              React.createElement('div', { style: statLabelStyle }, '活跃会话')
            )
          )
        ),
        React.createElement(Space, { style: { marginTop: 24 } },
          React.createElement(Button, { icon: '🔄', onClick: function() { console.log('Refresh'); } }, '刷新数据')
        )
      )
    },
    {
      key: 'agents',
      label: '🤖 Agent列表',
      children: React.createElement('div', { style: { marginTop: 16 } },
        React.createElement(Table, {
          dataSource: mockAgents,
          columns: agentColumns,
          rowKey: 'agent_id',
          pagination: { pageSize: 10 },
          size: 'small'
        })
      )
    }
  ];
  
  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '🧠 HumanThinking 记忆管理'),
    React.createElement(Paragraph, null, '跨 Session 认知与情感连续性记忆管理系统'),
    React.createElement(Tabs, { items: tabItems, defaultActiveKey: 'overview' })
  );
}

function Settings() {
  var config = getConfig();

  function handleChange(key, value) {
    var newConfig = {};
    Object.keys(config).forEach(function(k) {
      newConfig[k] = config[k];
    });
    newConfig[key] = value;
    if (saveConfig(newConfig)) {
      console.log('Saved:', key, value);
    }
  }

  var switchStyle = { marginLeft: 'auto' };
  var itemStyle = { display: 'flex', alignItems: 'center', padding: '12px 0', justifyContent: 'space-between' };

  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '⚙️ 记忆设置'),
    React.createElement(Paragraph, null, '配置 HumanThinking 记忆管理功能'),
    
    React.createElement(Card, { title: '功能开关', style: { marginTop: 16 } },
      React.createElement('div', null,
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '跨Session记忆'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '新Session自动继承相关历史记忆')
          ),
          React.createElement(Switch, {
            style: switchStyle,
            checked: config.enable_cross_session,
            onChange: function(checked) { handleChange('enable_cross_session', checked); }
          })
        ),
        
        React.createElement(Divider, { style: { margin: '12px 0' } }),
        
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '情感连续性'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '跟踪对话情感变化，注入上下文')
          ),
          React.createElement(Switch, {
            style: switchStyle,
            checked: config.enable_emotion,
            onChange: function(checked) { handleChange('enable_emotion', checked); }
          })
        ),
        
        React.createElement(Divider, { style: { margin: '12px 0' } }),
        
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '会话隔离'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '按AgentID + UserID + SessionID隔离')
          ),
          React.createElement(Switch, {
            style: switchStyle,
            checked: config.enable_session_isolation,
            onChange: function(checked) { handleChange('enable_session_isolation', checked); }
          })
        ),
        
        React.createElement(Divider, { style: { margin: '12px 0' } }),
        
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null,
            React.createElement(Text, { strong: true }, '记忆冷藏'),
            React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '7天无访问自动冷藏，释放缓存空间')
          ),
          React.createElement(Switch, {
            style: switchStyle,
            checked: config.enable_memory_freeze,
            onChange: function(checked) { handleChange('enable_memory_freeze', checked); }
          })
        )
      )
    ),
    
    React.createElement(Alert, {
      message: '💡 提示',
      description: '修改设置后，部分功能需要刷新页面或新会话才能完全生效',
      type: 'info',
      showIcon: true,
      style: { marginTop: 16 }
    })
  );
}

var HumanThinkingPlugin = {
  id: "humanthinking-memory",

  setup: function() {
    if (window.QwenPaw && window.QwenPaw.registerRoutes) {
      window.QwenPaw.registerRoutes(this.id, [
        {
          path: '/plugin/humanthinking/dashboard',
          component: Dashboard,
          label: '记忆管理',
          icon: '🧠',
          priority: 10,
        },
        {
          path: '/plugin/humanthinking/settings',
          component: Settings,
          label: '记忆设置',
          icon: '⚙️',
          priority: 11,
        },
      ]);
      console.info('[HumanThinking] Plugin loaded successfully');
    } else {
      console.warn('[HumanThinking] QwenPaw.registerRoutes not available');
    }
  }
};

HumanThinkingPlugin.setup();

export {};
