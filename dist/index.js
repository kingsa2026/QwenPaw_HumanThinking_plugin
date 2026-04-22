/** HumanThinking Memory Manager - Frontend Plugin Entry. */

var React = window.QwenPaw.host.React;

var CONFIG_KEY = 'humanthinking_config';
var defaultConfig = {
  enable_cross_session: true,
  enable_emotion: true,
  enable_session_isolation: true,
  enable_memory_freeze: true,
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
  var containerStyle = { padding: 24 };
  var titleStyle = { fontSize: 20, fontWeight: 'bold', marginBottom: 8 };
  var descStyle = { color: '#666', marginBottom: 24 };
  var statRowStyle = { display: 'flex', gap: 16, marginBottom: 24 };
  var statStyle = { flex: 1, padding: 16, background: 'var(--antd-token, #f5f5f5)', borderRadius: 8, textAlign: 'center' };
  var statNumStyle = { fontSize: 28, fontWeight: 'bold', color: '#1677ff' };
  var statLabelStyle = { fontSize: 12, color: '#666', marginTop: 4 };
  var btnStyle = { padding: '8px 16px', background: '#1677ff', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' };

  return React.createElement('div', { style: containerStyle },
    React.createElement('h2', { style: titleStyle }, '🧠 HumanThinking 记忆管理'),
    React.createElement('p', { style: descStyle }, '跨 Session 认知与情感连续性记忆管理系统'),
    
    React.createElement('div', { style: statRowStyle },
      React.createElement('div', { style: statStyle },
        React.createElement('div', { style: statNumStyle }, '0'),
        React.createElement('div', { style: statLabelStyle }, '总记忆数')
      ),
      React.createElement('div', { style: statStyle },
        React.createElement('div', { style: statNumStyle }, '0'),
        React.createElement('div', { style: statLabelStyle }, '跨Session记忆')
      ),
      React.createElement('div', { style: statStyle },
        React.createElement('div', { style: statNumStyle }, '0'),
        React.createElement('div', { style: statLabelStyle }, '冷藏记忆')
      ),
      React.createElement('div', { style: statStyle },
        React.createElement('div', { style: statNumStyle }, '0'),
        React.createElement('div', { style: statLabelStyle }, '活跃会话')
      )
    ),
    
    React.createElement('button', { style: btnStyle, onClick: function() { console.log('Refresh'); } }, '🔄 刷新数据')
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

  var containerStyle = { padding: 24 };
  var titleStyle = { fontSize: 20, fontWeight: 'bold', marginBottom: 8 };
  var descStyle = { color: '#666', marginBottom: 24 };
  var cardStyle = { border: '1px solid #d9d9d9', borderRadius: 8, overflow: 'hidden' };
  var cardTitleStyle = { fontSize: 14, fontWeight: 'bold', padding: '12px 16px', borderBottom: '1px solid #d9d9d9', margin: 0 };
  var itemStyle = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' };
  var labelStyle = { fontWeight: 'bold', fontSize: 14 };
  var desc2Style = { fontSize: 12, color: '#666', marginTop: 2 };
  var hrStyle = { margin: 0, border: 'none', borderTop: '1px solid #d9d9d9' };
  var checkboxStyle = { width: 18, height: 18, cursor: 'pointer' };
  var alertStyle = { marginTop: 16, padding: 12, background: '#e6f4ff', border: '1px solid #91d5ff', borderRadius: 8 };

  return React.createElement('div', { style: containerStyle },
    React.createElement('h2', { style: titleStyle }, '⚙️ 记忆设置'),
    React.createElement('p', { style: descStyle }, '配置 HumanThinking 记忆管理功能'),
    
    React.createElement('div', { style: cardStyle },
      React.createElement('div', { style: cardTitleStyle }, '功能开关'),
      
      React.createElement('div', { style: itemStyle },
        React.createElement('div', null,
          React.createElement('div', { style: labelStyle }, '跨Session记忆'),
          React.createElement('div', { style: desc2Style }, '新Session自动继承相关历史记忆')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: checkboxStyle,
          checked: config.enable_cross_session,
          onChange: function(e) { handleChange('enable_cross_session', e.target.checked); }
        })
      ),
      React.createElement('hr', { style: hrStyle }),
      
      React.createElement('div', { style: itemStyle },
        React.createElement('div', null,
          React.createElement('div', { style: labelStyle }, '情感连续性'),
          React.createElement('div', { style: desc2Style }, '跟踪对话情感变化，注入上下文')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: checkboxStyle,
          checked: config.enable_emotion,
          onChange: function(e) { handleChange('enable_emotion', e.target.checked); }
        })
      ),
      React.createElement('hr', { style: hrStyle }),
      
      React.createElement('div', { style: itemStyle },
        React.createElement('div', null,
          React.createElement('div', { style: labelStyle }, '会话隔离'),
          React.createElement('div', { style: desc2Style }, '按AgentID + UserID + SessionID隔离')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: checkboxStyle,
          checked: config.enable_session_isolation,
          onChange: function(e) { handleChange('enable_session_isolation', e.target.checked); }
        })
      ),
      React.createElement('hr', { style: hrStyle }),
      
      React.createElement('div', { style: itemStyle },
        React.createElement('div', null,
          React.createElement('div', { style: labelStyle }, '记忆冷藏'),
          React.createElement('div', { style: desc2Style }, '7天无访问自动冷藏，释放缓存空间')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: checkboxStyle,
          checked: config.enable_memory_freeze,
          onChange: function(e) { handleChange('enable_memory_freeze', e.target.checked); }
        })
      )
    ),
    
    React.createElement('div', { style: alertStyle },
      React.createElement('div', { style: { fontWeight: 'bold', color: '#1677ff' } }, '💡 提示'),
      React.createElement('div', { style: { fontSize: 12, color: '#666', marginTop: 4 } }, '修改设置后，部分功能需要刷新页面或新会话才能完全生效')
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
