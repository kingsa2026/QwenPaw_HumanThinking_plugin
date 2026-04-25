# HumanThinking 侧边栏使用说明

## 问题说明

由于 QwenPaw 的插件系统原生不支持通过 `plugin.json` 自动注册侧边栏，
目前需要通过**浏览器手动注入**的方式来显示 HumanThinking 侧边栏。

## 使用方法

### 方法1：浏览器控制台注入（推荐）

1. 打开浏览器，访问 `http://192.168.10.132:8088`
2. 登录 QwenPaw
3. 按 `F12` 打开浏览器开发者工具
4. 切换到 **Console (控制台)** 标签
5. 复制 `inject_sidebar.js` 文件中的全部内容
6. 粘贴到控制台并按回车执行
7. 页面右侧会出现 HumanThinking 侧边栏

### 方法2：书签注入（更方便）

1. 在浏览器中创建一个新书签
2. 书签名称：`HumanThinking 侧边栏`
3. 书签URL（将以下内容复制到URL栏）：

```javascript
javascript:(function(){var s=document.createElement('script');s.src='http://192.168.10.132:8088/api/plugins/humanthinking/sidebar.js';document.body.appendChild(s);})();
```

4. 每次访问 QwenPaw 时，点击这个书签即可加载侧边栏

## 侧边栏功能

侧边栏包含以下功能模块：

### 📊 记忆统计
- 显示总记忆数、跨会话记忆数、冷藏记忆数、活跃会话数
- 数据自动刷新

### 🌙 睡眠状态
- 显示当前睡眠状态（活跃/浅睡/深睡）
- 提供手动控制按钮：浅睡、深睡、唤醒

### 💝 情感状态
- 显示当前情感状态和强度
- 支持开心、伤心、生气、中性、惊讶等情感

### 💬 会话列表
- 显示最近的会话列表
- 显示会话名称、记忆数量、对话对象

## 自动刷新

侧边栏会自动：
- 每5秒更新一次当前Agent信息
- 点击"刷新数据"按钮可手动刷新所有数据

## 注意事项

1. 侧边栏是通过 JavaScript 动态注入的，刷新页面后会消失
2. 需要重新执行注入脚本或点击书签
3. 确保 Agent 配置中已选择 "Human Thinking" 作为记忆管理器后端
4. API 接口已正常工作，侧边栏可以正常获取数据

## 故障排查

如果侧边栏不显示或数据加载失败：

1. 检查浏览器控制台是否有错误信息
2. 确认 API 是否正常：`curl http://192.168.10.132:8088/api/plugins/humanthinking/stats`
3. 确认已选择 Human Thinking 作为记忆管理器
4. 尝试清除浏览器缓存后重新注入
