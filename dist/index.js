/** HumanThinking Memory Manager - Frontend Plugin Entry. */

var React = window.QwenPaw.host.React;
var antd = window.QwenPaw.host.antd;

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
    React.createElement('h3', null, '🧠 HumanThinking 记忆管理'),
    React.createElement('p', null, '跨 Session 认知与情感连续性记忆管理系统'),
    React.createElement('div', { style: { marginTop: 16 } },
      React.createElement('div', { style: { display: 'flex', gap: 16 } },
        React.createElement('div', { style: { flex: 1, padding: 16, background: '#f5f5f5', borderRadius: 8 } },
          React.createElement('div', { style: { fontSize: 24, fontWeight: 'bold' } }, '0'),
          React.createElement('div', { style: { color: '#666' } }, '总记忆数')
        ),
        React.createElement('div', { style: { flex: 1, padding: 16, background: '#f5f5f5', borderRadius: 8 } },
          React.createElement('div', { style: { fontSize: 24, fontWeight: 'bold' } }, '0'),
          React.createElement('div', { style: { color: '#666' } }, '跨Session记忆')
        ),
        React.createElement('div', { style: { flex: 1, padding: 16, background: '#f5f5f5', borderRadius: 8 } },
          React.createElement('div', { style: { fontSize: 24, fontWeight: 'bold' } }, '0'),
          React.createElement('div', { style: { color: '#666' } }, '冷藏记忆')
        ),
        React.createElement('div', { style: { flex: 1, padding: 16, background: '#f5f5f5', borderRadius: 8 } },
          React.createElement('div', { style: { fontSize: 24, fontWeight: 'bold' } }, '0'),
          React.createElement('div', { style: { color: '#666' } }, '活跃会话')
        )
      )
    ),
    React.createElement('button', {
      style: { marginTop: 16, padding: '8px 16px', cursor: 'pointer' },
      onClick: function() { console.log('Refresh clicked'); }
    }, '🔄 刷新')
  );
}

function Settings() {
  var config = getConfig();
  var saving = false;

  function handleChange(key, value) {
    var newConfig = {};
    newConfig[key] = value;
    if (saveConfig(newConfig)) {
      console.log('Settings saved:', key, value);
    }
  }

  return React.createElement('div', { style: { padding: 24 } },
    React.createElement('h3', null, '⚙️ 记忆设置'),
    React.createElement('div', { style: { marginTop: 16 } },
      React.createElement('div', { style: { padding: 16, background: '#fff', borderRadius: 8, border: '1px solid #d9d9d9' } },
        React.createElement('div', { style: { marginBottom: 16 } },
          React.createElement('div', { style: { fontWeight: 'bold' } }, '跨Session记忆'),
          React.createElement('div', { style: { fontSize: 12, color: '#666' } }, '新Session自动继承相关历史记忆'),
          React.createElement('input', {
            type: 'checkbox',
            checked: config.enable_cross_session,
            onChange: function(e) { handleChange('enable_cross_session', e.target.checked); }
          })
        ),
        React.createElement('hr', { style: { margin: '16px 0' } }),
        React.createElement('div', { style: { marginBottom: 16 } },
          React.createElement('div', { style: { fontWeight: 'bold' } }, '情感连续性'),
          React.createElement('div', { style: { fontSize: 12, color: '#666' } }, '跟踪对话情感变化'),
          React.createElement('input', {
            type: 'checkbox',
            checked: config.enable_emotion,
            onChange: function(e) { handleChange('enable_emotion', e.target.checked); }
          })
        ),
        React.createElement('hr', { style: { margin: '16px 0' } }),
        React.createElement('div', { style: { marginBottom: 16 } },
          React.createElement('div', { style: { fontWeight: 'bold' } }, '会话隔离'),
          React.createElement('div', { style: { fontSize: 12, color: '#666' } }, '按AgentID + UserID + SessionID隔离'),
          React.createElement('input', {
            type: 'checkbox',
            checked: config.enable_session_isolation,
            onChange: function(e) { handleChange('enable_session_isolation', e.target.checked); }
          })
        ),
        React.createElement('hr', { style: { margin: '16px 0' } }),
        React.createElement('div', { style: { marginBottom: 16 } },
          React.createElement('div', { style: { fontWeight: 'bold' } }, '记忆冷藏'),
          React.createElement('div', { style: { fontSize: 12, color: '#666' } }, '7天无访问自动冷藏'),
          React.createElement('input', {
            type: 'checkbox',
            checked: config.enable_memory_freeze,
            onChange: function(e) { handleChange('enable_memory_freeze', e.target.checked); }
          })
        )
      )
    ),
    React.createElement('div', {
      style: { marginTop: 16, padding: 16, background: '#e6f7ff', borderRadius: 8, border: '1px solid #91d5ff' }
    },
      React.createElement('div', { style: { fontWeight: 'bold' } }, '提示'),
      React.createElement('div', { style: { fontSize: 12 } }, '修改设置后，部分功能需要刷新页面或新会话才能完全生效')
    )
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
