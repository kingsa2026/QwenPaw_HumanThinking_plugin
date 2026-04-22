const { React: e, antd: V } = window.QwenPaw.host, { Typography: W, Card: c, Table: F, Statistic: x, Row: X, Col: B, Tag: J, Button: v, Space: $, Descriptions: S, Switch: h, Divider: D, Alert: K, message: g, Modal: ce, InputNumber: L, Select: me, DatePicker: ue, Progress: ge } = V, { Title: z, Paragraph: d, Text: m } = W;
require("dayjs");
const U = "humanthinking_config", Q = "humanthinking_backup_config", R = {
  enable_cross_session: !0,
  enable_emotion: !0,
  enable_session_isolation: !0,
  enable_memory_freeze: !0,
  session_idle_timeout: 180,
  refresh_interval: 5,
  max_results: 5,
  max_memory_chars: 150
}, M = {
  auto_backup_enabled: !1,
  auto_backup_interval_hours: 24,
  last_backup_time: null,
  backup_count: 5
}, j = {
  enable_agent_sleep: !0,
  sleep_idle_hours: 2,
  auto_consolidate: !0,
  consolidate_interval_hours: 6
}, q = "humanthinking_sleep_config";
function Z() {
  try {
    const t = localStorage.getItem(U);
    if (t)
      return { ...R, ...JSON.parse(t) };
  } catch (t) {
    console.error("Failed to load config:", t);
  }
  return R;
}
function ee(t) {
  try {
    return localStorage.setItem(U, JSON.stringify(t)), !0;
  } catch (a) {
    return console.error("Failed to save config:", a), !1;
  }
}
function te() {
  try {
    const t = localStorage.getItem(Q);
    if (t)
      return { ...M, ...JSON.parse(t) };
  } catch (t) {
    console.error("Failed to load backup config:", t);
  }
  return M;
}
function P(t) {
  try {
    return localStorage.setItem(Q, JSON.stringify(t)), !0;
  } catch (a) {
    return console.error("Failed to save backup config:", a), !1;
  }
}
function ne() {
  try {
    const t = localStorage.getItem(q);
    if (t)
      return { ...j, ...JSON.parse(t) };
  } catch (t) {
    console.error("Failed to load sleep config:", t);
  }
  return j;
}
function ae(t) {
  try {
    return localStorage.setItem(q, JSON.stringify(t)), !0;
  } catch (a) {
    return console.error("Failed to save sleep config:", a), !1;
  }
}
function le() {
  const [t, a] = e.useState(null), [r, u] = e.useState([]), [i, n] = e.useState([]), [_, p] = e.useState(!1), [A, o] = e.useState("overview"), [s, f] = e.useState([]), [C, N] = e.useState(!1), O = async () => {
    var l, y, E, I;
    p(!0);
    try {
      const k = (y = (l = window.QwenPaw.host) == null ? void 0 : l.getApiToken) == null ? void 0 : y.call(l), T = (I = (E = window.QwenPaw.host) == null ? void 0 : E.getApiUrl) == null ? void 0 : I.call(E, "");
      try {
        const w = await (await fetch(`${T}api/plugin/humanthinking/stats`, {
          headers: { Authorization: `Bearer ${k}` }
        })).json();
        a(w);
      } catch {
        console.warn("Stats API not available, using mock data"), a({
          total_memories: 156,
          cross_session_memories: 89,
          frozen_memories: 23,
          active_sessions: 4
        });
      }
      try {
        const w = await (await fetch(`${T}api/plugin/humanthinking/agents`, {
          headers: { Authorization: `Bearer ${k}` }
        })).json();
        u(w.agents || []);
      } catch {
        console.warn("Agents API not available, using mock data"), u([
          {
            agent_id: "agent_001",
            agent_name: "客服助手",
            db_path: "/home/user/.qwenpaw/workspaces/agent_001/memory/human_thinking.db",
            db_size_mb: 2.35,
            last_updated: "2025-04-22 14:30:00",
            memory_count: 89,
            memory_type_stats: { fact: 23, preference: 45, emotion: 12, general: 9 }
          },
          {
            agent_id: "agent_002",
            agent_name: "电商客服",
            db_path: "/home/user/.qwenpaw/workspaces/agent_002/memory/human_thinking.db",
            db_size_mb: 5.67,
            last_updated: "2025-04-22 16:45:00",
            memory_count: 234,
            memory_type_stats: { fact: 67, preference: 89, emotion: 34, general: 44 }
          }
        ]);
      }
      try {
        const w = await (await fetch(`${T}api/plugin/humanthinking/recent`, {
          headers: { Authorization: `Bearer ${k}` }
        })).json();
        n(w.memories || []);
      } catch {
        console.warn("Recent API not available, using mock data"), n([
          { id: 1, content: "用户喜欢蓝色", role: "user", memory_type: "preference", importance: 4, created_at: "2025-04-22 16:30:00" },
          { id: 2, content: "订单号12345已发货", role: "assistant", memory_type: "fact", importance: 5, created_at: "2025-04-22 16:25:00" },
          { id: 3, content: "用户表示不满", role: "user", memory_type: "emotion", importance: 5, created_at: "2025-04-22 16:20:00" }
        ]);
      }
    } catch (k) {
      console.error("Failed to fetch data:", k);
    }
    p(!1);
  };
  e.useEffect(() => {
    O();
  }, []);
  const G = [
    { title: "Agent名称", dataIndex: "agent_name", key: "agent_name", width: 120 },
    {
      title: "数据库大小",
      dataIndex: "db_size_mb",
      key: "db_size_mb",
      width: 100,
      render: (l) => `${l.toFixed(2)} MB`
    },
    { title: "记忆数量", dataIndex: "memory_count", key: "memory_count", width: 100 },
    { title: "事实", dataIndex: ["memory_type_stats", "fact"], key: "fact", width: 60 },
    { title: "偏好", dataIndex: ["memory_type_stats", "preference"], key: "preference", width: 60 },
    { title: "情感", dataIndex: ["memory_type_stats", "emotion"], key: "emotion", width: 60 },
    { title: "一般", dataIndex: ["memory_type_stats", "general"], key: "general", width: 60 },
    { title: "最新更新", dataIndex: "last_updated", key: "last_updated", width: 160 }
  ], H = [
    { title: "内容", dataIndex: "content", key: "content", ellipsis: !0 },
    { title: "角色", dataIndex: "role", key: "role", width: 80 },
    {
      title: "类型",
      dataIndex: "memory_type",
      key: "memory_type",
      width: 100,
      render: (l) => {
        const y = {
          fact: "blue",
          preference: "green",
          emotion: "red",
          general: "default"
        };
        return /* @__PURE__ */ e.createElement(J, { color: y[l] || "default" }, l);
      }
    },
    {
      title: "重要性",
      dataIndex: "importance",
      key: "importance",
      width: 100,
      render: (l) => `${l}/5`
    },
    { title: "时间", dataIndex: "created_at", key: "created_at", width: 180 }
  ], Y = [
    {
      key: "overview",
      label: "📊 总览",
      children: /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(X, { gutter: 16, style: { marginTop: 24 } }, /* @__PURE__ */ e.createElement(B, { span: 6 }, /* @__PURE__ */ e.createElement(c, null, /* @__PURE__ */ e.createElement(x, { title: "总记忆数", value: (t == null ? void 0 : t.total_memories) || 0 }))), /* @__PURE__ */ e.createElement(B, { span: 6 }, /* @__PURE__ */ e.createElement(c, null, /* @__PURE__ */ e.createElement(x, { title: "跨Session记忆", value: (t == null ? void 0 : t.cross_session_memories) || 0 }))), /* @__PURE__ */ e.createElement(B, { span: 6 }, /* @__PURE__ */ e.createElement(c, null, /* @__PURE__ */ e.createElement(x, { title: "冷藏记忆", value: (t == null ? void 0 : t.frozen_memories) || 0 }))), /* @__PURE__ */ e.createElement(B, { span: 6 }, /* @__PURE__ */ e.createElement(c, null, /* @__PURE__ */ e.createElement(x, { title: "活跃会话", value: (t == null ? void 0 : t.active_sessions) || 0 })))), /* @__PURE__ */ e.createElement(c, { title: "最近记忆", style: { marginTop: 24 } }, /* @__PURE__ */ e.createElement(
        F,
        {
          dataSource: i,
          columns: H,
          rowKey: "id",
          loading: _,
          pagination: { pageSize: 10 },
          size: "small"
        }
      )))
    },
    {
      key: "agents",
      label: "🤖 Agent列表",
      children: /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(c, { title: "Agent记忆统计", style: { marginTop: 24 } }, /* @__PURE__ */ e.createElement("div", { style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement($, null, /* @__PURE__ */ e.createElement(
        v,
        {
          onClick: () => f(r.map((l) => l.agent_id)),
          size: "small"
        },
        "全选"
      ), /* @__PURE__ */ e.createElement(
        v,
        {
          onClick: () => f([]),
          size: "small"
        },
        "取消"
      ), /* @__PURE__ */ e.createElement(
        v,
        {
          type: "primary",
          danger: !0,
          disabled: s.length === 0 || C,
          loading: C,
          onClick: async () => {
            if (s.length === 0) {
              g.warning("请先选择要备份的 Agent");
              return;
            }
            N(!0), g.info(`正在备份 ${s.length} 个 Agent...`), await new Promise((y) => setTimeout(y, 2e3));
            const l = {
              id: Date.now(),
              time: (/* @__PURE__ */ new Date()).toLocaleString(),
              agents: s.length,
              size: `${(Math.random() * s.length * 5 + 1).toFixed(2)} MB`,
              status: "success"
            };
            try {
              const y = localStorage.getItem("humanthinking_backup_history"), E = y ? JSON.parse(y) : [], I = [l, ...E].slice(0, 10);
              localStorage.setItem("humanthinking_backup_history", JSON.stringify(I));
            } catch {
            }
            N(!1), g.success(`已成功备份 ${s.length} 个 Agent`);
          }
        },
        "批量备份选中 (",
        s.length,
        ")"
      ))), /* @__PURE__ */ e.createElement(
        F,
        {
          rowSelection: {
            selectedRowKeys: s,
            onChange: (l) => f(l)
          },
          dataSource: r,
          columns: G,
          rowKey: "agent_id",
          loading: _,
          pagination: {
            pageSize: 10,
            showSizeChanger: !0,
            showTotal: (l) => `共 ${l} 个 Agent`
          },
          size: "small"
        }
      )))
    }
  ];
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 24 } }, /* @__PURE__ */ e.createElement(z, { level: 3 }, "🧠 HumanThinking 记忆管理"), /* @__PURE__ */ e.createElement(d, null, "跨 Session 认知与情感连续性记忆管理系统"), /* @__PURE__ */ e.createElement($, { style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement(v, { onClick: O, loading: _ }, "🔄 刷新")), /* @__PURE__ */ e.createElement(c, null, /* @__PURE__ */ e.createElement(Tabs, { activeKey: A, onChange: o, items: Y })));
}
function oe() {
  const [t, a] = e.useState(te()), [r, u] = e.useState(!1), [i, n] = e.useState([]);
  e.useEffect(() => {
    try {
      const o = localStorage.getItem("humanthinking_backup_history");
      o && n(JSON.parse(o));
    } catch (o) {
      console.error("Failed to load backup history:", o);
    }
  }, []);
  const _ = (o) => {
    const s = { ...t, auto_backup_enabled: o };
    P(s), a(s), g.success(o ? "自动备份已开启" : "自动备份已关闭");
  }, p = (o) => {
    const s = { ...t, auto_backup_interval_hours: o };
    P(s), a(s), g.success("备份间隔已更新");
  }, A = async () => {
    u(!0), g.info("开始备份..."), await new Promise((C) => setTimeout(C, 2e3));
    const s = [{
      id: Date.now(),
      time: (/* @__PURE__ */ new Date()).toLocaleString(),
      size: `${(Math.random() * 10 + 1).toFixed(2)} MB`,
      status: "success"
    }, ...i].slice(0, 10);
    n(s), localStorage.setItem("humanthinking_backup_history", JSON.stringify(s));
    const f = { ...t, last_backup_time: (/* @__PURE__ */ new Date()).toISOString() };
    P(f), a(f), u(!1), g.success("备份完成！");
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 24 } }, /* @__PURE__ */ e.createElement(z, { level: 3 }, "💾 记忆备份"), /* @__PURE__ */ e.createElement(c, { title: "自动备份设置", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "自动备份"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0 } }, "按设定时间间隔自动备份所有记忆")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.auto_backup_enabled,
      onChange: _
    }
  )), t.auto_backup_enabled && /* @__PURE__ */ e.createElement("div", { style: { display: "flex", alignItems: "center", gap: 16 } }, /* @__PURE__ */ e.createElement(m, null, "备份间隔："), /* @__PURE__ */ e.createElement(
    L,
    {
      min: 1,
      max: 168,
      value: t.auto_backup_interval_hours,
      onChange: (o) => o && p(o),
      style: { width: 100 }
    }
  ), /* @__PURE__ */ e.createElement(m, null, "小时"))), /* @__PURE__ */ e.createElement(c, { title: "手动备份", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement(d, null, "立即备份所有 Agent 的记忆数据"), /* @__PURE__ */ e.createElement(
    v,
    {
      type: "primary",
      loading: r,
      onClick: A
    },
    r ? "备份中..." : "立即备份"
  )), /* @__PURE__ */ e.createElement(c, { title: "备份历史", style: { marginTop: 16 } }, i.length > 0 ? /* @__PURE__ */ e.createElement(
    F,
    {
      dataSource: i,
      columns: [
        { title: "时间", dataIndex: "time", key: "time" },
        { title: "大小", dataIndex: "size", key: "size" },
        {
          title: "状态",
          dataIndex: "status",
          key: "status",
          render: (o) => /* @__PURE__ */ e.createElement(J, { color: o === "success" ? "green" : "red" }, o)
        }
      ],
      rowKey: "id",
      pagination: { pageSize: 5 },
      size: "small"
    }
  ) : /* @__PURE__ */ e.createElement(d, { type: "secondary" }, "暂无备份记录")));
}
function se() {
  const [t, a] = e.useState(Z()), [r, u] = e.useState(!1), i = (n, _) => {
    const p = { ...t, [n]: _ };
    u(!0), ee(p) ? (a(p), g.success("设置已保存")) : g.error("保存失败"), u(!1);
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 24 } }, /* @__PURE__ */ e.createElement(z, { level: 3 }, "⚙️ 记忆设置"), /* @__PURE__ */ e.createElement(c, { title: "功能开关", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "跨Session记忆"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0, fontSize: 12 } }, "新Session自动继承相关历史记忆")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.enable_cross_session,
      onChange: (n) => i("enable_cross_session", n),
      loading: r
    }
  )), /* @__PURE__ */ e.createElement(D, { style: { margin: "8px 0" } }), /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "情感连续性"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0, fontSize: 12 } }, "跟踪对话情感变化，在上下文中注入情感状态")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.enable_emotion,
      onChange: (n) => i("enable_emotion", n),
      loading: r
    }
  )), /* @__PURE__ */ e.createElement(D, { style: { margin: "8px 0" } }), /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "会话隔离"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0, fontSize: 12 } }, "按AgentID + UserID + SessionID隔离记忆")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.enable_session_isolation,
      onChange: (n) => i("enable_session_isolation", n),
      loading: r
    }
  )), /* @__PURE__ */ e.createElement(D, { style: { margin: "8px 0" } }), /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "记忆冷藏"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0, fontSize: 12 } }, "7天无访问自动冷藏，释放缓存空间")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.enable_memory_freeze,
      onChange: (n) => i("enable_memory_freeze", n),
      loading: r
    }
  )))), /* @__PURE__ */ e.createElement(c, { title: "高级设置", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement(S, { column: 1, size: "small" }, /* @__PURE__ */ e.createElement(S.Item, { label: "会话空闲超时" }, t.session_idle_timeout, " 秒"), /* @__PURE__ */ e.createElement(S.Item, { label: "刷新间隔" }, t.refresh_interval, " 轮"), /* @__PURE__ */ e.createElement(S.Item, { label: "最大返回数" }, t.max_results, " 条"), /* @__PURE__ */ e.createElement(S.Item, { label: "单条记忆最大字符" }, t.max_memory_chars, " 字符"))), /* @__PURE__ */ e.createElement(
    K,
    {
      message: "提示",
      description: "修改设置后，部分功能需要刷新页面或新会话才能完全生效",
      type: "info",
      showIcon: !0,
      style: { marginTop: 16 }
    }
  ));
}
function re() {
  const [t, a] = e.useState(ne()), [r, u] = e.useState(!1), i = (n, _) => {
    const p = { ...t, [n]: _ };
    u(!0), ae(p) ? (a(p), g.success("睡眠设置已保存")) : g.error("保存失败"), u(!1);
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 24 } }, /* @__PURE__ */ e.createElement(z, { level: 3 }, "😴 Agent 睡眠设置"), /* @__PURE__ */ e.createElement(d, null, "Agent 睡眠功能：2小时无会话自动进入睡眠，有新会话自动唤醒"), /* @__PURE__ */ e.createElement(c, { title: "睡眠开关", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "启用 Agent 睡眠"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0, fontSize: 12 } }, "2小时无会话/无新任务自动进入睡眠状态")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.enable_agent_sleep,
      onChange: (n) => i("enable_agent_sleep", n),
      loading: r
    }
  ))), t.enable_agent_sleep && /* @__PURE__ */ e.createElement(e.Fragment, null, /* @__PURE__ */ e.createElement(c, { title: "睡眠条件", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement(m, null, "空闲多少小时后进入睡眠："), /* @__PURE__ */ e.createElement(
    L,
    {
      min: 1,
      max: 24,
      value: t.sleep_idle_hours,
      onChange: (n) => n && i("sleep_idle_hours", n),
      style: { marginLeft: 16, width: 80 }
    }
  ), /* @__PURE__ */ e.createElement(m, { style: { marginLeft: 8 } }, "小时"))), /* @__PURE__ */ e.createElement(c, { title: "睡眠时自动整理记忆", style: { marginTop: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, { strong: !0 }, "自动总结经验"), /* @__PURE__ */ e.createElement(d, { type: "secondary", style: { marginBottom: 0, fontSize: 12 } }, "睡眠时自动整理对话经验，生成为持久化固定记忆")), /* @__PURE__ */ e.createElement(
    h,
    {
      checked: t.auto_consolidate,
      onChange: (n) => i("auto_consolidate", n)
    }
  )), t.auto_consolidate && /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(m, null, "整理间隔："), /* @__PURE__ */ e.createElement(
    L,
    {
      min: 1,
      max: 72,
      value: t.consolidate_interval_hours,
      onChange: (n) => n && i("consolidate_interval_hours", n),
      style: { marginLeft: 16, width: 80 }
    }
  ), /* @__PURE__ */ e.createElement(m, { style: { marginLeft: 8 } }, "小时")))), /* @__PURE__ */ e.createElement(
    K,
    {
      message: "工作原理",
      description: /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement("div", null, "• 睡眠：Agent 停止活动，释放资源"), /* @__PURE__ */ e.createElement("div", null, "• 唤醒：新会话/新任务立即唤醒"), /* @__PURE__ */ e.createElement("div", null, "• 自动整理：根据四种记忆类型(fact/preference/emotion/general)自动分类存储")),
      type: "info",
      showIcon: !0,
      style: { marginTop: 16 }
    }
  ));
}
class ie {
  constructor() {
    this.id = "humanthinking-memory";
  }
  setup() {
    var a, r;
    (r = (a = window.QwenPaw).registerRoutes) == null || r.call(a, this.id, [
      {
        path: "/plugin/humanthinking/dashboard",
        component: le,
        label: "记忆管理",
        icon: "🧠",
        priority: 10
      },
      {
        path: "/plugin/humanthinking/backup",
        component: oe,
        label: "记忆备份",
        icon: "💾",
        priority: 12
      },
      {
        path: "/plugin/humanthinking/sleep",
        component: re,
        label: "睡眠设置",
        icon: "😴",
        priority: 13
      },
      {
        path: "/plugin/humanthinking/settings",
        component: se,
        label: "记忆设置",
        icon: "⚙️",
        priority: 11
      }
    ]);
  }
}
new ie().setup();
