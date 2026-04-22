/** HumanThinking Memory Manager - Frontend Plugin Entry. */

var React = window.QwenPaw.host.React;

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

function getStyle() {
  var isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  var bg = isDark ? '#141414' : '#ffffff';
  var bg2 = isDark ? '#1f1f1f' : '#fafafa';
  var bg3 = isDark ? '#262626' : '#f5f5f5';
  var text = isDark ? '#ffffff' : '#000000';
  var text2 = isDark ? '#rgba(255,255,255,0.65)' : 'rgba(0,0,0,0.45)';
  var border = isDark ? '#424242' : '#d9d9d9';
  var primary = '#1677ff';
  
  return {
    container: { padding: 24, background: bg, minHeight: '100vh', color: text },
    card: { background: bg2, border: '1px solid ' + border, borderRadius: 8, marginTop: 16 },
    cardTitle: { fontSize: 16, fontWeight: 'bold', color: text, borderBottom: '1px solid ' + border, padding: '12px 16px', margin: 0 },
    stat: { padding: 16, background: bg3, borderRadius: 8, textAlign: 'center' },
    statNum: { fontSize: 28, fontWeight: 'bold', color: primary },
    statLabel: { fontSize: 12, color: text2, marginTop: 4 },
    title: { fontSize: 20, fontWeight: 'bold', color: text, marginBottom: 8 },
    desc: { fontSize: 14, color: text2, marginBottom: 16 },
    row: { display: 'flex', gap: 16, marginTop: 16 },
    item: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 0', borderBottom: '1px solid ' + border },
    label: { fontWeight: 'bold', color: text, fontSize: 14 },
    desc2: { fontSize: 12, color: text2, marginTop: 2 },
    alert: { marginTop: 16, padding: 12, background: isDark ? '#1f3b5c' : '#e6f4ff', border: '1px solid ' + (isDark ? '#15395b' : '#91d5ff'), borderRadius: 8 },
    alertTitle: { fontWeight: 'bold', color: isDark ? '#79c0ff' : primary, fontSize: 14 },
    alertText: { fontSize: 12, color: text2, marginTop: 4 },
    button: { padding: '8px 16px', background: primary, color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14 },
    hr: { margin: '12px 0', border: 'none', borderTop: '1px solid ' + border },
    checkbox: { width: 18, height: 18, cursor: 'pointer' }
  };
}

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
  var style = getStyle();
  
  return React.createElement('div', { style: style.container },
    React.createElement('h2', { style: { margin: 0, fontSize: 20, fontWeight: 'bold' } }, '🧠 HumanThinking 记忆管理'),
    React.createElement('p', { style: style.desc }, '跨 Session 认知与情感连续性记忆管理系统'),
    
    React.createElement('div', { style: style.row },
      React.createElement('div', { style: style.stat },
        React.createElement('div', { style: style.statNum }, '0'),
        React.createElement('div', { style: style.statLabel }, '总记忆数')
      ),
      React.createElement('div', { style: style.stat },
        React.createElement('div', { style: style.statNum }, '0'),
        React.createElement('div', { style: style.statLabel }, '跨Session记忆')
      ),
      React.createElement('div', { style: style.stat },
        React.createElement('div', { style: style.statNum }, '0'),
        React.createElement('div', { style: style.statLabel }, '冷藏记忆')
      ),
      React.createElement('div', { style: style.stat },
        React.createElement('div', { style: style.statNum }, '0'),
        React.createElement('div', { style: style.statLabel }, '活跃会话')
      )
    ),
    
    React.createElement('button', { style: style.button, onClick: function() { console.log('Refresh'); } }, '🔄 刷新数据')
  );
}

function Settings() {
  var config = getConfig();
  var style = getStyle();

  function handleChange(key, value) {
    var newConfig = {};
    Object.keys(config).forEach(function(k) {
      newConfig[k] = config[k];
    });
    newConfig[key] = value;
    if (saveConfig(newConfig)) {
      console.log('Saved:', key, value);
      location.reload();
    }
  }

  return React.createElement('div', { style: style.container },
    React.createElement('h2', { style: { margin: 0, fontSize: 20, fontWeight: 'bold' } }, '⚙️ 记忆设置'),
    React.createElement('p', { style: style.desc }, '配置 HumanThinking 记忆管理功能'),
    
    React.createElement('div', { style: style.card },
      React.createElement('div', { style: style.cardTitle }, '功能开关'),
      
      React.createElement('div', { style: style.item },
        React.createElement('div', null,
          React.createElement('div', { style: style.label }, '跨Session记忆'),
          React.createElement('div', { style: style.desc2 }, '新Session自动继承相关历史记忆')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: style.checkbox,
          checked: config.enable_cross_session,
          onChange: function(e) { handleChange('enable_cross_session', e.target.checked); }
        })
      ),
      React.createElement('hr', { style: style.hr }),
      
      React.createElement('div', { style: style.item },
        React.createElement('div', null,
          React.createElement('div', { style: style.label }, '情感连续性'),
          React.createElement('div', { style: style.desc2 }, '跟踪对话情感变化，注入上下文')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: style.checkbox,
          checked: config.enable_emotion,
          onChange: function(e) { handleChange('enable_emotion', e.target.checked); }
        })
      ),
      React.createElement('hr', { style: style.hr }),
      
      React.createElement('div', { style: style.item },
        React.createElement('div', null,
          React.createElement('div', { style: style.label }, '会话隔离'),
          React.createElement('div', { style: style.desc2 }, '按AgentID + UserID + SessionID隔离')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: style.checkbox,
          checked: config.enable_session_isolation,
          onChange: function(e) { handleChange('enable_session_isolation', e.target.checked); }
        })
      ),
      React.createElement('hr', { style: style.hr }),
      
      React.createElement('div', { style: style.item },
        React.createElement('div', null,
          React.createElement('div', { style: style.label }, '记忆冷藏'),
          React.createElement('div', { style: style.desc2 }, '7天无访问自动冷藏，释放缓存空间')
        ),
        React.createElement('input', {
          type: 'checkbox',
          style: style.checkbox,
          checked: config.enable_memory_freeze,
          onChange: function(e) { handleChange('enable_memory_freeze', e.target.checked); }
        })
      )
    ),
    
    React.createElement('div', { style: style.alert },
      React.createElement('div', { style: style.alertTitle }, '💡 提示'),
      React.createElement('div', { style: style.alertText }, '修改设置后，部分功能需要刷新页面或新会话才能完全生效')
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
