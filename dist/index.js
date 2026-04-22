/** HumanThinking Memory Manager - Frontend Plugin Entry. */

var React = window.QwenPaw.host.React;
var antd = window.QwenPaw.host.antd;
var Switch = antd.Switch;
var Card = antd.Card;
var Typography = antd.Typography;
var Row = antd.Row;
var Col = antd.Col;
var Statistic = antd.Stat;
var Button = antd.Button;
var Divider = antd.Divider;
var Alert = antd.Alert;
var Space = antd.Space;

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
  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '🧠 HumanThinking 记忆管理'),
    React.createElement(Paragraph, null, '跨 Session 认知与情感连续性记忆管理系统'),
    
    React.createElement(Row, { gutter: 16, style: { marginTop: 24 } },
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
    ),
    
    React.createElement(Space, { style: { marginTop: 24 } },
      React.createElement(Button, { icon: '🔄', onClick: function() { console.log('Refresh'); } }, '刷新数据')
    )
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
