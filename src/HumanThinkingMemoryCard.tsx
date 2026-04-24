import {
  Form,
  Select,
  Card,
  Alert,
  Switch,
  InputNumber,
} from "@agentscope-ai/design";
import { useTranslation } from "react-i18next";
import React from "react";

const CONFIG_KEY = "humanthinking_config";

function getConfig(agentId: string | null) {
  const key = agentId ? `humanthinking_config_${agentId}` : "humanthinking_config";
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {}
  return {
    enable_cross_session: true,
    enable_emotion: true,
    enable_session_isolation: true,
    enable_memory_freeze: true,
    session_idle_timeout: 180,
    refresh_interval: 5,
    max_results: 5,
    max_memory_chars: 150,
  };
}

function saveConfig(config: any, agentId: string | null) {
  const key = agentId ? `humanthinking_config_${agentId}` : "humanthinking_config";
  try {
    localStorage.setItem(key, JSON.stringify(config));
    return true;
  } catch (e) {
    console.error("Failed to save config:", e);
    return false;
  }
}

async function getCurrentAgentId(): Promise<string | null> {
  try {
    const stored = sessionStorage.getItem("qwenpaw-agent-storage");
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed?.state?.selectedAgent || null;
    }
  } catch (e) {}
  return null;
}

async function fetchAgentConfig(): Promise<{ memory_manager_backend?: string } | null> {
  try {
    const token = (window as any).QwenPaw.host?.getApiToken?.();
    const baseUrl = (window as any).QwenPaw.host?.getApiUrl?.('');
    if (!baseUrl || !token) return null;

    const agentId = await getCurrentAgentId();
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
    if (agentId) {
      headers['X-Agent-Id'] = agentId;
    }

    const res = await fetch(`${baseUrl}agent/running-config`, {
      headers,
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.error('Failed to fetch agent config:', e);
  }
  return null;
}

async function updateAgentConfig(config: any): Promise<boolean> {
  try {
    const token = (window as any).QwenPaw.host?.getApiToken?.();
    const baseUrl = (window as any).QwenPaw.host?.getApiUrl?.('');
    if (!baseUrl || !token) return false;

    const agentId = await getCurrentAgentId();
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
    if (agentId) {
      headers['X-Agent-Id'] = agentId;
    }

    const res = await fetch(`${baseUrl}agent/running-config`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(config),
    });
    return res.ok;
  } catch (e) {
    console.error('Failed to update agent config:', e);
    return false;
  }
}

export function HumanThinkingMemoryCard() {
  const { t } = useTranslation();
  const [config, setConfig] = React.useState(getConfig(null));
  const [saving, setSaving] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  const loadConfig = async () => {
    setLoading(true);
    const currentAgentId = await getCurrentAgentId();
    const agentConfig = await fetchAgentConfig();
    if (agentConfig) {
      const savedConfig = getConfig(agentConfig.memory_manager_backend || null);
      setConfig(savedConfig);
    }
    setLoading(false);
  };

  React.useEffect(() => {
    loadConfig();
  }, []);

  // 轮询检测 Agent 切换，每 3 秒检查一次
  React.useEffect(() => {
    let lastAgentId: string | null = null;

    const checkAgent = async () => {
      const currentAgentId = await getCurrentAgentId();
      if (currentAgentId !== lastAgentId) {
        lastAgentId = currentAgentId;
        loadConfig();
      }
    };

    checkAgent();
    const interval = setInterval(checkAgent, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleChange = async (key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    setSaving(true);

    // 保存到 localStorage
    saveConfig(newConfig, null);
    setConfig(newConfig);

    // 更新 Agent 运行配置 - 必须设置 memory_manager_backend 为 "human_thinking"
    await updateAgentConfig({
      memory_manager_backend: "human_thinking",
      human_thinking_memory_config: newConfig,
    });

    setSaving(false);
  };

  return (
    <Card title={t("humanThinking.title") || "HumanThinking 记忆设置"}>
      <Alert
        type="info"
        showIcon
        message={
          t("humanThinking.description") ||
          "跨 Session 认知与情感连续性记忆管理系统"
        }
        style={{ marginBottom: 16 }}
      />

      <Form.Item
        label={t("humanThinking.enableCrossSession") || "跨Session记忆"}
        tooltip={
          t("humanThinking.enableCrossSessionTooltip") ||
          "新Session自动继承相关历史记忆"
        }
      >
        <Switch
          checked={config.enable_cross_session}
          onChange={(checked) => handleChange("enable_cross_session", checked)}
          loading={saving}
        />
      </Form.Item>

      <Form.Item
        label={t("humanThinking.enableEmotion") || "情感连续性"}
        tooltip={
          t("humanThinking.enableEmotionTooltip") ||
          "跟踪对话情感变化，在上下文中注入情感状态"
        }
      >
        <Switch
          checked={config.enable_emotion}
          onChange={(checked) => handleChange("enable_emotion", checked)}
          loading={saving}
        />
      </Form.Item>

      <Form.Item
        label={t("humanThinking.enableSessionIsolation") || "会话隔离"}
        tooltip={
          t("humanThinking.enableSessionIsolationTooltip") ||
          "按AgentID + UserID + SessionID隔离记忆"
        }
      >
        <Switch
          checked={config.enable_session_isolation}
          onChange={(checked) =>
            handleChange("enable_session_isolation", checked)
          }
          loading={saving}
        />
      </Form.Item>

      <Form.Item
        label={t("humanThinking.enableMemoryFreeze") || "记忆冷藏"}
        tooltip={
          t("humanThinking.enableMemoryFreezeTooltip") ||
          "7天无访问自动冷藏，释放缓存空间"
        }
      >
        <Switch
          checked={config.enable_memory_freeze}
          onChange={(checked) => handleChange("enable_memory_freeze", checked)}
          loading={saving}
        />
      </Form.Item>

      <Form.Item
        label={t("humanThinking.sessionIdleTimeout") || "会话空闲超时"}
        tooltip={
          t("humanThinking.sessionIdleTimeoutTooltip") ||
          "超过此时间未活动则释放缓存"
        }
      >
        <InputNumber
          value={config.session_idle_timeout}
          onChange={(val) =>
            val && handleChange("session_idle_timeout", val)
          }
          min={30}
          max={3600}
          addonAfter="秒"
          style={{ width: "100%" }}
        />
      </Form.Item>

      <Form.Item
        label={t("humanThinking.refreshInterval") || "刷新间隔"}
        tooltip={
          t("humanThinking.refreshIntervalTooltip") || "每N轮对话刷新一次缓存"
        }
      >
        <InputNumber
          value={config.refresh_interval}
          onChange={(val) => val && handleChange("refresh_interval", val)}
          min={1}
          max={50}
          addonAfter="轮"
          style={{ width: "100%" }}
        />
      </Form.Item>

      <Form.Item
        label={t("humanThinking.maxResults") || "最大返回数"}
        tooltip={
          t("humanThinking.maxResultsTooltip") ||
          "搜索记忆时返回的最大条数"
        }
      >
        <InputNumber
          value={config.max_results}
          onChange={(val) => val && handleChange("max_results", val)}
          min={1}
          max={20}
          addonAfter="条"
          style={{ width: "100%" }}
        />
      </Form.Item>
    </Card>
  );
}
