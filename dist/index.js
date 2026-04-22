/** HumanThinking Memory Manager - Frontend Plugin Entry. */

var React = window.QwenPaw.host.React;
var useState = React.useState;
var useEffect = React.useEffect;
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
var InputNumber = antd.InputNumber;
var message = antd.message;

var Title = Typography.Title;
var Paragraph = Typography.Paragraph;
var Text = Typography.Text;

var CONFIG_KEY = 'humanthinking_config';
var BACKUP_CONFIG_KEY = 'humanthinking_backup_config';
var SLEEP_CONFIG_KEY = 'humanthinking_sleep_config';

var defaultConfig = {
  enable_cross_session: true,
  enable_emotion: true,
  enable_session_isolation: true,
  enable_memory_freeze: true,
};

var defaultBackupConfig = {
  auto_backup_enabled: false,
  auto_backup_interval_hours: 24,
};

var defaultSleepConfig = {
  enable_agent_sleep: true,
  sleep_idle_hours: 2,
  auto_consolidate: true,
  consolidate_interval_hours: 6,
};

function loadConfig(key, defaults) {
  try {
    var stored = localStorage.getItem(key);
    if (stored) return Object.assign({}, defaults, JSON.parse(stored));
  } catch (e) { console.error('Load error:', e); }
  return defaults;
}

function saveConfigFn(key, config) {
  try { localStorage.setItem(key, JSON.stringify(config)); return true; } 
  catch (e) { console.error('Save error:', e); return false; }
}

function Dashboard() {
  var _a = useState(loadConfig(BACKUP_CONFIG_KEY, defaultBackupConfig)), backupConfig = _a[0], setBackupConfig = _a[1];
  
  var mockAgents = [
    { agent_id: 'agent_001', agent_name: '客服助手', db_path: '/path/to/agent_001.db', db_size_mb: 2.35, memory_count: 89, last_updated: '2025-04-22 14:30', stats: { fact: 23, preference: 45, emotion: 12, general: 9 } },
    { agent_id: 'agent_002', agent_name: '电商客服', db_path: '/path/to/agent_002.db', db_size_mb: 5.67, memory_count: 234, last_updated: '2025-04-22 16:45', stats: { fact: 67, preference: 89, emotion: 34, general: 44 } },
  ];
  
  var agentColumns = [
    { title: 'Agent名称', dataIndex: 'agent_name', key: 'agent_name', width: 120 },
    { title: '数据库大小', dataIndex: 'db_size_mb', key: 'db_size_mb', width: 100, render: function(val) { return val.toFixed(2) + ' MB'; } },
    { title: '记忆数', dataIndex: 'memory_count', key: 'memory_count', width: 80 },
    { title: '事实', dataIndex: ['stats', 'fact'], key: 'fact', width: 50, render: function(val) { return React.createElement(Tag, { color: 'blue' }, val || 0); } },
    { title: '偏好', dataIndex: ['stats', 'preference'], key: 'preference', width: 50, render: function(val) { return React.createElement(Tag, { color: 'green' }, val || 0); } },
    { title: '情感', dataIndex: ['stats', 'emotion'], key: 'emotion', width: 50, render: function(val) { return React.createElement(Tag, { color: 'red' }, val || 0); } },
    { title: '一般', dataIndex: ['stats', 'general'], key: 'general', width: 50, render: function(val) { return React.createElement(Tag, null, val || 0); } },
    { title: '更新时间', dataIndex: 'last_updated', key: 'last_updated', width: 150 },
  ];

  var statCardStyle = { padding: 16, textAlign: 'center', background: 'var(--ant-component-background, #fff)', borderRadius: 8, border: '1px solid var(--ant-border-color-split, #d9d9d9)' };
  var statNumStyle = { fontSize: 24, fontWeight: 'bold', color: '#1677ff' };
  var statLabelStyle = { fontSize: 12, color: 'var(--ant-text-color-secondary, #666)', marginTop: 4 };

  function handleAutoBackupChange(checked) {
    var newConfig = Object.assign({}, backupConfig, { auto_backup_enabled: checked });
    saveConfigFn(BACKUP_CONFIG_KEY, newConfig);
    setBackupConfig(newConfig);
    message.success(checked ? '自动备份已开启' : '自动备份已关闭');
  }

  function handleIntervalChange(val) {
    if (!val) return;
    var newConfig = Object.assign({}, backupConfig, { auto_backup_interval_hours: val });
    saveConfigFn(BACKUP_CONFIG_KEY, newConfig);
    setBackupConfig(newConfig);
    message.success('间隔已更新为 ' + val + ' 小时');
  }

  var tabItems = [
    {
      key: 'overview',
      label: '📊 总览',
      children: React.createElement('div', null,
        React.createElement(Row, { gutter: 16, style: { marginTop: 24 } },
          React.createElement(Col, { span: 6 }, React.createElement('div', { style: statCardStyle }, React.createElement('div', { style: statNumStyle }, '2'), React.createElement('div', { style: statLabelStyle }, 'Agent数'))),
          React.createElement(Col, { span: 6 }, React.createElement('div', { style: statCardStyle }, React.createElement('div', { style: statNumStyle }, '323'), React.createElement('div', { style: statLabelStyle }, '总记忆数'))),
          React.createElement(Col, { span: 6 }, React.createElement('div', { style: statCardStyle }, React.createElement('div', { style: statNumStyle }, '156'), React.createElement('div', { style: statLabelStyle }, '跨Session记忆'))),
          React.createElement(Col, { span: 6 }, React.createElement('div', { style: statCardStyle }, React.createElement('div', { style: statNumStyle }, '3'), React.createElement('div', { style: statLabelStyle }, '活跃会话')))
        ),
        React.createElement(Space, { style: { marginTop: 24 } }, React.createElement(Button, { icon: '🔄', onClick: function() { message.success('刷新成功'); } }, '刷新数据'))
      )
    },
    {
      key: 'agents',
      label: '🤖 Agent列表',
      children: React.createElement('div', { style: { marginTop: 16 } },
        React.createElement('div', { style: { marginBottom: 16 } },
          React.createElement(Space, null,
            React.createElement(Button, { onClick: function() { message.info('全选功能'); } }, '全选'),
            React.createElement(Button, { onClick: function() { message.info('取消选择'); } }, '取消'),
            React.createElement(Button, { type: 'primary', danger: true, onClick: function() { message.info('批量备份'); } }, '批量备份选中 (0)')
          )
        ),
        React.createElement('div', { style: { marginBottom: 16, padding: 12, background: 'var(--ant-background-color-light, #fafafa)', borderRadius: 8 } },
          React.createElement(Space, null,
            React.createElement(Text, { strong: true }, '自动备份：'),
            React.createElement(Switch, { size: 'small', checked: backupConfig.auto_backup_enabled, onChange: handleAutoBackupChange }),
            React.createElement(Text, { style: { marginLeft: 16 } }, '间隔'),
            React.createElement(InputNumber, { size: 'small', min: 1, max: 168, value: backupConfig.auto_backup_interval_hours, onChange: handleIntervalChange, style: { width: 60 } }),
            React.createElement(Text, null, '小时')
          )
        ),
        React.createElement(Table, { columns: agentColumns, dataSource: mockAgents, rowKey: 'agent_id', pagination: { pageSize: 10, showTotal: function(total) { return '共 ' + total + ' 个 Agent'; }, showSizeChanger: true }, rowSelection: { onChange: function(keys) { console.log('Selected:', keys); } }, size: 'small' })
      )
    }
  ];
  
  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '🧠 HumanThinking 记忆管理'),
    React.createElement(Paragraph, null, '跨 Session 认知与情感连续性记忆管理系统'),
    React.createElement(Tabs, { items: tabItems, defaultActiveKey: 'overview' })
  );
}

function SleepSettings() {
  var _a = useState(loadConfig(SLEEP_CONFIG_KEY, defaultSleepConfig)), sleepConfig = _a[0], setSleepConfig = _a[1];

  function handleChange(key, value) {
    var newConfig = Object.assign({}, sleepConfig, { [key]: value });
    saveConfigFn(SLEEP_CONFIG_KEY, newConfig);
    setSleepConfig(newConfig);
    message.success('睡眠设置已保存');
  }

  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '😴 Agent 睡眠设置'),
    React.createElement(Paragraph, null, 'Agent 睡眠功能：2小时无会话自动进入睡眠，有新会话自动唤醒'),
    
    React.createElement(Card, { title: '睡眠开关', style: { marginTop: 16 } },
      React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
        React.createElement('div', null, React.createElement(Text, { strong: true }, '启用 Agent 睡眠'), React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '2小时无会话/无新任务自动进入睡眠状态')),
        React.createElement(Switch, { checked: sleepConfig.enable_agent_sleep, onChange: function(checked) { handleChange('enable_agent_sleep', checked); } })
      )
    ),

    sleepConfig.enable_agent_sleep && React.createElement('div', null,
      React.createElement(Card, { title: '睡眠条件', style: { marginTop: 16 } },
        React.createElement('div', null,
          React.createElement(Text, null, '空闲多少小时后进入睡眠：'),
          React.createElement(InputNumber, { min: 1, max: 24, value: sleepConfig.sleep_idle_hours, onChange: function(val) { val && handleChange('sleep_idle_hours', val); }, style: { marginLeft: 16, width: 80 } }),
          React.createElement(Text, { style: { marginLeft: 8 } }, '小时')
        )
      ),

      React.createElement(Card, { title: '睡眠时自动整理记忆', style: { marginTop: 16 } },
        React.createElement('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 } },
          React.createElement('div', null, React.createElement(Text, { strong: true }, '自动总结经验'), React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '睡眠时自动整理对话经验，生成为持久化固定记忆')),
          React.createElement(Switch, { checked: sleepConfig.auto_consolidate, onChange: function(checked) { handleChange('auto_consolidate', checked); } })
        ),
        sleepConfig.auto_consolidate && React.createElement('div', null,
          React.createElement(Text, null, '整理间隔：'),
          React.createElement(InputNumber, { min: 1, max: 72, value: sleepConfig.consolidate_interval_hours, onChange: function(val) { val && handleChange('consolidate_interval_hours', val); }, style: { marginLeft: 16, width: 80 } }),
          React.createElement(Text, { style: { marginLeft: 8 } }, '小时')
        )
      )
    ),

    React.createElement(Alert, {
      message: '工作原理',
      description: React.createElement('div', null, 
        React.createElement('div', null, '• 睡眠：Agent 停止活动，释放资源'),
        React.createElement('div', null, '• 唤醒：新会话/新任务立即唤醒'),
        React.createElement('div', null, '• 自动整理：根据四种记忆类型(fact/preference/emotion/general)自动分类存储')
      ),
      type: 'info',
      showIcon: true,
      style: { marginTop: 16 }
    })
  );
}

function Settings() {
  var _a = useState(loadConfig(CONFIG_KEY, defaultConfig)), config = _a[0], setConfig = _a[1];

  function handleChange(key, value) {
    var newConfig = Object.assign({}, config, { [key]: value });
    saveConfigFn(CONFIG_KEY, newConfig);
    setConfig(newConfig);
    message.success('设置已保存');
  }

  var switchStyle = { marginLeft: 'auto' };
  var itemStyle = { display: 'flex', alignItems: 'center', padding: '12px 0', justifyContent: 'space-between' };

  return React.createElement('div', { style: { padding: 24 } },
    React.createElement(Title, { level: 3 }, '⚙️ 记忆设置'),
    React.createElement(Paragraph, null, '配置 HumanThinking 记忆管理功能'),
    
    React.createElement(Card, { title: '功能开关', style: { marginTop: 16 } },
      React.createElement('div', null,
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null, React.createElement(Text, { strong: true }, '跨Session记忆'), React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '新Session自动继承相关历史记忆')),
          React.createElement(Switch, { style: switchStyle, checked: config.enable_cross_session, onChange: function(checked) { handleChange('enable_cross_session', checked); } })
        ),
        React.createElement(Divider, { style: { margin: '12px 0' } }),
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null, React.createElement(Text, { strong: true }, '情感连续性'), React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '跟踪对话情感变化，注入上下文')),
          React.createElement(Switch, { style: switchStyle, checked: config.enable_emotion, onChange: function(checked) { handleChange('enable_emotion', checked); } })
        ),
        React.createElement(Divider, { style: { margin: '12px 0' } }),
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null, React.createElement(Text, { strong: true }, '会话隔离'), React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '按AgentID + UserID + SessionID隔离')),
          React.createElement(Switch, { style: switchStyle, checked: config.enable_session_isolation, onChange: function(checked) { handleChange('enable_session_isolation', checked); } })
        ),
        React.createElement(Divider, { style: { margin: '12px 0' } }),
        React.createElement('div', { style: itemStyle },
          React.createElement('div', null, React.createElement(Text, { strong: true }, '记忆冷藏'), React.createElement(Paragraph, { type: 'secondary', style: { marginBottom: 0, fontSize: 12 } }, '7天无访问自动冷藏，释放缓存空间')),
          React.createElement(Switch, { style: switchStyle, checked: config.enable_memory_freeze, onChange: function(checked) { handleChange('enable_memory_freeze', checked); } })
        )
      )
    ),
    
    React.createElement(Alert, { message: '💡 提示', description: '修改设置后，部分功能需要刷新页面或新会话才能完全生效', type: 'info', showIcon: true, style: { marginTop: 16 } })
  );
}

var HumanThinkingPlugin = {
  id: "humanthinking-memory",

  setup: function() {
    if (window.QwenPaw && window.QwenPaw.registerRoutes) {
      window.QwenPaw.registerRoutes(this.id, [
        { path: '/plugin/humanthinking/dashboard', component: Dashboard, label: '记忆管理', icon: '🧠', priority: 10 },
        { path: '/plugin/humanthinking/sleep', component: SleepSettings, label: '睡眠设置', icon: '😴', priority: 12 },
        { path: '/plugin/humanthinking/settings', component: Settings, label: '记忆设置', icon: '⚙️', priority: 11 },
      ]);
      console.info('[HumanThinking] Plugin loaded successfully');
    } else {
      console.warn('[HumanThinking] QwenPaw.registerRoutes not available');
    }
  }
};

HumanThinkingPlugin.setup();

export {};
