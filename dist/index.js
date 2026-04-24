const { React: e, antd: j } = window.QwenPaw.host, {
  Typography: F,
  Card: m,
  Table: L,
  Statistic: y,
  Row: z,
  Col: p,
  Tag: S,
  Button: T,
  Space: k,
  Descriptions: G,
  Input: D,
  List: w,
  Timeline: b,
  Badge: M,
  Switch: I,
  Slider: _,
  Form: g,
  Tabs: x,
  Empty: C,
  Spin: P,
  Divider: V,
  Tooltip: X,
  Progress: R
} = j, { Title: f, Paragraph: B, Text: h } = F, { TabPane: v } = x, u = () => {
  var l, r;
  const t = (r = (l = window.QwenPaw.host) == null ? void 0 : l.getApiUrl) == null ? void 0 : r.call(l, "");
  return t && t.includes("/api/") ? `${t}plugins/humanthinking` : `${t}api/plugins/humanthinking`;
}, E = () => {
  var l, r;
  return {
    Authorization: `Bearer ${(r = (l = window.QwenPaw.host) == null ? void 0 : l.getApiToken) == null ? void 0 : r.call(l)}`,
    "Content-Type": "application/json"
  };
};
function H() {
  const [t, l] = e.useState(""), [r, c] = e.useState([]), [i, a] = e.useState(!1), o = async () => {
    if (t.trim()) {
      a(!0);
      try {
        const n = await (await fetch(`${u()}/search`, {
          method: "POST",
          headers: E(),
          body: JSON.stringify({ query: t, limit: 20 })
        })).json();
        c(n.memories || []);
      } catch (s) {
        console.error("Search failed:", s);
      }
      a(!1);
    }
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(f, { level: 4 }, "🔍 记忆搜索"), /* @__PURE__ */ e.createElement(k.Compact, { style: { width: "100%", marginBottom: 16 } }, /* @__PURE__ */ e.createElement(
    D,
    {
      placeholder: "搜索历史记忆...",
      value: t,
      onChange: (s) => l(s.target.value),
      onPressEnter: o
    }
  ), /* @__PURE__ */ e.createElement(T, { type: "primary", onClick: o, loading: i }, "搜索")), /* @__PURE__ */ e.createElement(
    w,
    {
      dataSource: r,
      renderItem: (s) => /* @__PURE__ */ e.createElement(w.Item, null, /* @__PURE__ */ e.createElement(m, { size: "small", style: { width: "100%" } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "start" } }, /* @__PURE__ */ e.createElement(h, { ellipsis: !0, style: { maxWidth: "70%" } }, s.content), /* @__PURE__ */ e.createElement(k, null, /* @__PURE__ */ e.createElement(S, { color: s.memory_type === "fact" ? "blue" : s.memory_type === "emotion" ? "red" : "green" }, s.memory_type), /* @__PURE__ */ e.createElement(S, null, "重要性: ", s.importance))), /* @__PURE__ */ e.createElement("div", { style: { marginTop: 8 } }, /* @__PURE__ */ e.createElement(h, { type: "secondary", style: { fontSize: 12 } }, s.role, " · ", s.created_at)))),
      locale: { emptyText: "输入关键词搜索记忆" }
    }
  ));
}
function A() {
  const [t, l] = e.useState(null), [r, c] = e.useState([]), [i, a] = e.useState(!1), o = async () => {
    a(!0);
    try {
      const d = await (await fetch(`${u()}/emotion`, {
        headers: E()
      })).json();
      l({
        emotion: d.current_emotion,
        intensity: d.intensity,
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      }), c(d.history || []);
    } catch (n) {
      console.error("Failed to fetch emotion:", n);
    }
    a(!1);
  };
  e.useEffect(() => {
    o();
    const n = setInterval(o, 3e4);
    return () => clearInterval(n);
  }, []);
  const s = (n) => ({
    satisfied: "green",
    frustrated: "red",
    neutral: "blue",
    excited: "orange",
    sad: "purple"
  })[n] || "blue";
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(f, { level: 4 }, "💝 情感状态"), i && !t ? /* @__PURE__ */ e.createElement(P, null) : t ? /* @__PURE__ */ e.createElement(e.Fragment, null, /* @__PURE__ */ e.createElement(m, { size: "small", style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", alignItems: "center", gap: 16 } }, /* @__PURE__ */ e.createElement(
    M,
    {
      status: "processing",
      color: s(t.emotion),
      text: /* @__PURE__ */ e.createElement(h, { strong: !0, style: { fontSize: 18 } }, t.emotion)
    }
  ), /* @__PURE__ */ e.createElement(
    R,
    {
      percent: t.intensity * 100,
      size: "small",
      style: { width: 120 },
      showInfo: !1
    }
  ))), /* @__PURE__ */ e.createElement(f, { level: 5 }, "情感历史"), /* @__PURE__ */ e.createElement(b, null, r.slice(0, 5).map((n, d) => /* @__PURE__ */ e.createElement(b.Item, { key: d, color: s(n.emotion) }, /* @__PURE__ */ e.createElement("div", null, n.emotion, " (强度: ", (n.intensity * 100).toFixed(0), "%)"), /* @__PURE__ */ e.createElement(h, { type: "secondary", style: { fontSize: 12 } }, n.timestamp))))) : /* @__PURE__ */ e.createElement(C, { description: "暂无情感数据" }));
}
function O() {
  const [t, l] = e.useState([]), [r, c] = e.useState(!1), i = async () => {
    c(!0);
    try {
      const o = await (await fetch(`${u()}/sessions`, {
        headers: E()
      })).json();
      l(o || []);
    } catch (a) {
      console.error("Failed to fetch sessions:", a);
    }
    c(!1);
  };
  return e.useEffect(() => {
    i();
  }, []), /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(f, { level: 4 }, "💬 会话列表"), /* @__PURE__ */ e.createElement(
    w,
    {
      loading: r,
      dataSource: t,
      renderItem: (a) => /* @__PURE__ */ e.createElement(w.Item, null, /* @__PURE__ */ e.createElement(m, { size: "small", style: { width: "100%" } }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", justifyContent: "space-between" } }, /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(h, { strong: !0 }, a.session_id.slice(0, 8), "..."), /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(S, { size: "small", color: a.status === "active" ? "green" : "default" }, a.status), /* @__PURE__ */ e.createElement(h, { type: "secondary", style: { fontSize: 12, marginLeft: 8 } }, a.memory_count, " 条记忆"))), /* @__PURE__ */ e.createElement(h, { type: "secondary", style: { fontSize: 12 } }, a.last_active)))),
      locale: { emptyText: "暂无会话" }
    }
  ));
}
function Q() {
  const [t, l] = e.useState(null), [r, c] = e.useState(!1), i = async () => {
    c(!0);
    try {
      const o = await (await fetch(`${u()}/stats`, {
        headers: E()
      })).json();
      l(o);
    } catch (a) {
      console.error("Failed to fetch stats:", a);
    }
    c(!1);
  };
  return e.useEffect(() => {
    i();
    const a = setInterval(i, 6e4);
    return () => clearInterval(a);
  }, []), /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(f, { level: 4 }, "📊 记忆统计"), /* @__PURE__ */ e.createElement(z, { gutter: [8, 8] }, /* @__PURE__ */ e.createElement(p, { span: 12 }, /* @__PURE__ */ e.createElement(m, { size: "small" }, /* @__PURE__ */ e.createElement(
    y,
    {
      title: "总记忆",
      value: (t == null ? void 0 : t.total_memories) || 0,
      loading: r
    }
  ))), /* @__PURE__ */ e.createElement(p, { span: 12 }, /* @__PURE__ */ e.createElement(m, { size: "small" }, /* @__PURE__ */ e.createElement(
    y,
    {
      title: "跨会话",
      value: (t == null ? void 0 : t.cross_session_memories) || 0,
      loading: r
    }
  ))), /* @__PURE__ */ e.createElement(p, { span: 12 }, /* @__PURE__ */ e.createElement(m, { size: "small" }, /* @__PURE__ */ e.createElement(
    y,
    {
      title: "冷藏",
      value: (t == null ? void 0 : t.frozen_memories) || 0,
      loading: r
    }
  ))), /* @__PURE__ */ e.createElement(p, { span: 12 }, /* @__PURE__ */ e.createElement(m, { size: "small" }, /* @__PURE__ */ e.createElement(
    y,
    {
      title: "活跃会话",
      value: (t == null ? void 0 : t.active_sessions) || 0,
      loading: r
    }
  )))));
}
function J() {
  const [t, l] = e.useState([]), [r, c] = e.useState(!1), i = async () => {
    c(!0);
    try {
      const o = await (await fetch(`${u()}/memories/timeline`, {
        headers: E()
      })).json();
      l(o || []);
    } catch (a) {
      console.error("Failed to fetch timeline:", a);
    }
    c(!1);
  };
  return e.useEffect(() => {
    i();
  }, []), /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(f, { level: 4 }, "📅 记忆时间线"), /* @__PURE__ */ e.createElement(b, { mode: "left" }, t.map((a, o) => /* @__PURE__ */ e.createElement(
    b.Item,
    {
      key: o,
      label: a.created_at,
      color: a.importance > 3 ? "red" : a.importance > 1 ? "blue" : "gray"
    },
    /* @__PURE__ */ e.createElement(h, null, a.content.slice(0, 50), "..."),
    /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(S, { size: "small" }, a.memory_type), /* @__PURE__ */ e.createElement(S, { size: "small" }, "重要性: ", a.importance))
  ))), t.length === 0 && /* @__PURE__ */ e.createElement(C, { description: "暂无记忆记录" }));
}
function K() {
  const [t, l] = e.useState({}), [r, c] = e.useState(!1), [i, a] = e.useState(!1), o = async () => {
    c(!0);
    try {
      const d = await (await fetch(`${u()}/config`, {
        headers: E()
      })).json();
      l(d);
    } catch (n) {
      console.error("Failed to fetch config:", n);
    }
    c(!1);
  }, s = async () => {
    a(!0);
    try {
      await fetch(`${u()}/config`, {
        method: "POST",
        headers: E(),
        body: JSON.stringify(t)
      });
    } catch (n) {
      console.error("Failed to save config:", n);
    }
    a(!1);
  };
  return e.useEffect(() => {
    o();
  }, []), /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(f, { level: 4 }, "⚙️ 配置"), /* @__PURE__ */ e.createElement(P, { spinning: r }, /* @__PURE__ */ e.createElement(g, { layout: "vertical" }, /* @__PURE__ */ e.createElement(g.Item, { label: "启用跨会话记忆" }, /* @__PURE__ */ e.createElement(
    I,
    {
      checked: t.enable_cross_session,
      onChange: (n) => l({ ...t, enable_cross_session: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "启用情感跟踪" }, /* @__PURE__ */ e.createElement(
    I,
    {
      checked: t.enable_emotion,
      onChange: (n) => l({ ...t, enable_emotion: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "冷藏天数" }, /* @__PURE__ */ e.createElement(
    _,
    {
      min: 7,
      max: 90,
      value: t.frozen_days,
      onChange: (n) => l({ ...t, frozen_days: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "归档天数" }, /* @__PURE__ */ e.createElement(
    _,
    {
      min: 30,
      max: 365,
      value: t.archive_days,
      onChange: (n) => l({ ...t, archive_days: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "删除天数" }, /* @__PURE__ */ e.createElement(
    _,
    {
      min: 90,
      max: 730,
      value: t.delete_days,
      onChange: (n) => l({ ...t, delete_days: n })
    }
  )), /* @__PURE__ */ e.createElement(T, { type: "primary", onClick: s, loading: i }, "保存配置"))));
}
function N() {
  const [t, l] = e.useState("search");
  return /* @__PURE__ */ e.createElement("div", { style: { height: "100%", display: "flex", flexDirection: "column" } }, /* @__PURE__ */ e.createElement(
    x,
    {
      activeKey: t,
      onChange: l,
      type: "card",
      size: "small",
      style: { flex: 1 }
    },
    /* @__PURE__ */ e.createElement(v, { tab: "🔍", key: "search" }, /* @__PURE__ */ e.createElement(H, null)),
    /* @__PURE__ */ e.createElement(v, { tab: "📊", key: "stats" }, /* @__PURE__ */ e.createElement(Q, null)),
    /* @__PURE__ */ e.createElement(v, { tab: "💬", key: "sessions" }, /* @__PURE__ */ e.createElement(O, null)),
    /* @__PURE__ */ e.createElement(v, { tab: "💝", key: "emotion" }, /* @__PURE__ */ e.createElement(A, null)),
    /* @__PURE__ */ e.createElement(v, { tab: "📅", key: "timeline" }, /* @__PURE__ */ e.createElement(J, null)),
    /* @__PURE__ */ e.createElement(v, { tab: "⚙️", key: "config" }, /* @__PURE__ */ e.createElement(K, null))
  ));
}
function U() {
  const [t, l] = e.useState(null), [r, c] = e.useState([]), [i, a] = e.useState(!1), o = async () => {
    a(!0);
    try {
      const d = await (await fetch(`${u()}/stats`, {
        headers: E()
      })).json();
      l(d);
      const $ = await (await fetch(`${u()}/memories/recent`, {
        headers: E()
      })).json();
      c($.memories || []);
    } catch (n) {
      console.error("Failed to fetch data:", n);
    }
    a(!1);
  };
  e.useEffect(() => {
    o();
  }, []);
  const s = [
    { title: "内容", dataIndex: "content", key: "content", ellipsis: !0 },
    { title: "角色", dataIndex: "role", key: "role", width: 80 },
    {
      title: "类型",
      dataIndex: "memory_type",
      key: "memory_type",
      width: 100,
      render: (n) => {
        const d = {
          fact: "blue",
          preference: "green",
          emotion: "red",
          general: "default"
        };
        return /* @__PURE__ */ e.createElement(S, { color: d[n] || "default" }, n);
      }
    },
    {
      title: "重要性",
      dataIndex: "importance",
      key: "importance",
      width: 100,
      render: (n) => `${n}/5`
    },
    { title: "时间", dataIndex: "created_at", key: "created_at", width: 180 }
  ];
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 24 } }, /* @__PURE__ */ e.createElement(f, { level: 3 }, "🧠 HumanThinking 记忆管理"), /* @__PURE__ */ e.createElement(B, null, "跨 Session 认知与情感连续性记忆管理系统"), /* @__PURE__ */ e.createElement(z, { gutter: 16, style: { marginTop: 24 } }, /* @__PURE__ */ e.createElement(p, { span: 6 }, /* @__PURE__ */ e.createElement(m, null, /* @__PURE__ */ e.createElement(y, { title: "总记忆数", value: (t == null ? void 0 : t.total_memories) || 0 }))), /* @__PURE__ */ e.createElement(p, { span: 6 }, /* @__PURE__ */ e.createElement(m, null, /* @__PURE__ */ e.createElement(y, { title: "跨Session记忆", value: (t == null ? void 0 : t.cross_session_memories) || 0 }))), /* @__PURE__ */ e.createElement(p, { span: 6 }, /* @__PURE__ */ e.createElement(m, null, /* @__PURE__ */ e.createElement(y, { title: "冷藏记忆", value: (t == null ? void 0 : t.frozen_memories) || 0 }))), /* @__PURE__ */ e.createElement(p, { span: 6 }, /* @__PURE__ */ e.createElement(m, null, /* @__PURE__ */ e.createElement(y, { title: "活跃会话", value: (t == null ? void 0 : t.active_sessions) || 0 })))), /* @__PURE__ */ e.createElement(m, { title: "最近记忆", style: { marginTop: 24 } }, /* @__PURE__ */ e.createElement(
    L,
    {
      dataSource: r,
      columns: s,
      rowKey: "id",
      loading: i,
      pagination: { pageSize: 10 },
      size: "small"
    }
  )), /* @__PURE__ */ e.createElement(m, { title: "操作", style: { marginTop: 24 } }, /* @__PURE__ */ e.createElement(k, null, /* @__PURE__ */ e.createElement(T, { onClick: o, loading: i }, "刷新"))));
}
class q {
  constructor() {
    this.id = "humanthinking-memory";
  }
  setup() {
    var l, r;
    (r = (l = window.QwenPaw).registerRoutes) == null || r.call(l, this.id, [
      {
        path: "/plugin/humanthinking/dashboard",
        component: U,
        label: "记忆管理",
        icon: "🧠",
        priority: 10
      },
      {
        path: "/plugin/humanthinking/sidebar",
        component: N,
        label: "记忆助手",
        icon: "🧠",
        priority: 11,
        sidebar: !0
        // 标记为侧边栏组件
      }
    ]);
  }
}
new q().setup();
