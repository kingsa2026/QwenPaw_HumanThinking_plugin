import e, { useState as d, useEffect as F, useCallback as L } from "react";
import { Typography as de, Select as j, Input as G, Spin as B, Row as X, Col as S, Card as T, Statistic as C, Divider as R, Button as k, Space as K, Checkbox as V, List as H, Popconfirm as Z, Modal as ue, Form as g, Timeline as P, Tag as Ee, Switch as J, Slider as A, Tabs as w, message as M } from "antd";
import { BarChartOutlined as ee, ReloadOutlined as ge, SearchOutlined as W, EditOutlined as te, SaveOutlined as pe, DeleteOutlined as ne, MessageOutlined as ae, CheckOutlined as he, CloseOutlined as ye, HeartOutlined as le, CalendarOutlined as re, SettingOutlined as U, MoonOutlined as q, BookOutlined as ce } from "@ant-design/icons";
const { Title: y, Text: _, Paragraph: N } = de, { Option: E } = j, { TextArea: fe } = G, f = () => {
  var a, s, o;
  const t = ((o = (s = (a = window.QwenPaw) == null ? void 0 : a.host) == null ? void 0 : s.getApiUrl) == null ? void 0 : o.call(s, "")) || "";
  return t && t.includes("/api/") ? `${t}plugins/humanthinking` : `${t}api/plugins/humanthinking`;
}, v = () => {
  var a, s, o;
  return {
    Authorization: `Bearer ${(o = (s = (a = window.QwenPaw) == null ? void 0 : a.host) == null ? void 0 : s.getApiToken) == null ? void 0 : o.call(s)}`,
    "Content-Type": "application/json"
  };
}, ve = () => {
  var t, a, s, o;
  try {
    const c = sessionStorage.getItem("qwenpaw-agent-storage");
    if (c) {
      const i = JSON.parse(c), r = (t = i.state) == null ? void 0 : t.selectedAgent, u = ((o = (s = (a = i.state) == null ? void 0 : a.agents) == null ? void 0 : s[r]) == null ? void 0 : o.name) || "未命名Agent";
      return { agent_id: r, agent_name: u };
    }
  } catch (c) {
    console.error("Failed to get agent info:", c);
  }
  return { agent_id: "", agent_name: "未选择Agent" };
};
function se() {
  const [t, a] = d({ agent_id: "", agent_name: "" });
  return F(() => {
    const s = () => {
      a(ve());
    };
    s();
    const o = setInterval(s, 1e3);
    return () => clearInterval(o);
  }, []), /* @__PURE__ */ e.createElement("div", { style: {
    padding: "8px 16px",
    background: "#f0f2f5",
    borderBottom: "1px solid #d9d9d9",
    fontSize: "13px",
    color: "#666"
  } }, /* @__PURE__ */ e.createElement("span", null, "🤖 当前智能体: "), /* @__PURE__ */ e.createElement(_, { strong: !0 }, t.agent_name), /* @__PURE__ */ e.createElement(_, { type: "secondary", style: { marginLeft: 8 } }, "(", t.agent_id, ")"));
}
function _e() {
  const [t, a] = d({}), [s, o] = d(!1), c = L(async () => {
    o(!0);
    try {
      const r = await (await fetch(`${f()}/stats`, {
        headers: v()
      })).json();
      a(r);
    } catch (i) {
      console.error("Failed to fetch stats:", i);
    }
    o(!1);
  }, []);
  return F(() => {
    c();
  }, [c]), /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(ee, null), " 记忆统计"), /* @__PURE__ */ e.createElement(B, { spinning: s }, /* @__PURE__ */ e.createElement(X, { gutter: [16, 16] }, /* @__PURE__ */ e.createElement(S, { span: 8 }, /* @__PURE__ */ e.createElement(T, null, /* @__PURE__ */ e.createElement(C, { title: "总记忆", value: t.total_memories || 0 }))), /* @__PURE__ */ e.createElement(S, { span: 8 }, /* @__PURE__ */ e.createElement(T, null, /* @__PURE__ */ e.createElement(C, { title: "跨会话记忆", value: t.cross_session_memories || 0 }))), /* @__PURE__ */ e.createElement(S, { span: 8 }, /* @__PURE__ */ e.createElement(T, null, /* @__PURE__ */ e.createElement(C, { title: "冷藏记忆", value: t.frozen_memories || 0 }))), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(T, null, /* @__PURE__ */ e.createElement(C, { title: "活跃会话", value: t.active_sessions || 0 }))), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(T, null, /* @__PURE__ */ e.createElement(C, { title: "情感状态数", value: t.emotional_states || 0 })))), /* @__PURE__ */ e.createElement(R, null), /* @__PURE__ */ e.createElement(k, { icon: /* @__PURE__ */ e.createElement(ge, null), onClick: c }, "刷新数据")));
}
function be() {
  const [t, a] = d(""), [s, o] = d([]), [c, i] = d(!1), [r, u] = d([]), [n, x] = d(null), [b, O] = d(!1), [I, D] = d({ content: "", memory_type: "", importance: 3 }), m = L(async () => {
    if (t.trim()) {
      i(!0);
      try {
        const p = await (await fetch(`${f()}/search`, {
          method: "POST",
          headers: v(),
          body: JSON.stringify({ query: t, limit: 20 })
        })).json();
        o(p.memories || []);
      } catch (l) {
        console.error("Failed to search:", l);
      }
      i(!1);
    }
  }, [t]), h = async (l) => {
    try {
      (await fetch(`${f()}/memories/${l.id}`, {
        method: "PUT",
        headers: v(),
        body: JSON.stringify({
          content: l.content,
          memory_type: l.memory_type,
          importance: l.importance
        })
      })).ok && (M.success("保存成功"), l._modified = !1, o([...s]));
    } catch (p) {
      console.error("Failed to save:", p);
    }
  }, $ = async () => {
    try {
      (await fetch(`${f()}/memories/batch`, {
        method: "DELETE",
        headers: v(),
        body: JSON.stringify({ memory_ids: r })
      })).ok && (M.success(`已删除 ${r.length} 条记忆`), o(s.filter((p) => !r.includes(p.id))), u([]));
    } catch (l) {
      console.error("Failed to delete:", l);
    }
  }, oe = (l) => {
    x(l), D({
      content: l.content,
      memory_type: l.memory_type || "fact",
      importance: l.importance || 3
    }), O(!0);
  }, ie = async () => {
    if (n)
      try {
        if ((await fetch(`${f()}/memories/${n.id}`, {
          method: "PUT",
          headers: v(),
          body: JSON.stringify(I)
        })).ok) {
          M.success("保存成功");
          const p = s.map(
            (z) => z.id === n.id ? { ...z, ...I } : z
          );
          o(p), O(!1);
        }
      } catch (l) {
        console.error("Failed to save:", l);
      }
  }, Y = (l, p, z) => {
    const me = s.map((Q) => Q.id === l ? { ...Q, [p]: z, _modified: !0 } : Q);
    o(me);
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(W, null), " 记忆搜索"), /* @__PURE__ */ e.createElement(K, { style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement(
    G,
    {
      placeholder: "搜索记忆...",
      value: t,
      onChange: (l) => a(l.target.value),
      onPressEnter: m,
      style: { width: 300 }
    }
  ), /* @__PURE__ */ e.createElement(k, { type: "primary", icon: /* @__PURE__ */ e.createElement(W, null), onClick: m }, "搜索")), s.length > 0 && /* @__PURE__ */ e.createElement("div", { style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement(
    V,
    {
      checked: r.length === s.length && s.length > 0,
      indeterminate: r.length > 0 && r.length < s.length,
      onChange: (l) => u(l.target.checked ? s.map((p) => p.id) : [])
    },
    "全选"
  ), /* @__PURE__ */ e.createElement(_, { style: { marginLeft: 16 } }, "已选择 ", r.length, " 项")), /* @__PURE__ */ e.createElement(B, { spinning: c }, /* @__PURE__ */ e.createElement(
    H,
    {
      dataSource: s,
      renderItem: (l) => /* @__PURE__ */ e.createElement(H.Item, null, /* @__PURE__ */ e.createElement(T, { style: { width: "100%" }, size: "small" }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", alignItems: "flex-start", gap: 8 } }, /* @__PURE__ */ e.createElement(
        V,
        {
          checked: r.includes(l.id),
          onChange: (p) => {
            p.target.checked ? u([...r, l.id]) : u(r.filter((z) => z !== l.id));
          }
        }
      ), /* @__PURE__ */ e.createElement("div", { style: { flex: 1 } }, /* @__PURE__ */ e.createElement(
        "div",
        {
          style: { cursor: "pointer", marginBottom: 8 },
          onClick: () => oe(l)
        },
        /* @__PURE__ */ e.createElement(_, null, l.content),
        /* @__PURE__ */ e.createElement(te, { style: { marginLeft: 8, color: "#1890ff" } })
      ), /* @__PURE__ */ e.createElement(K, null, /* @__PURE__ */ e.createElement(_, { type: "secondary" }, "角色: ", l.role || "user"), /* @__PURE__ */ e.createElement(
        j,
        {
          size: "small",
          value: l.memory_type || "fact",
          onChange: (p) => Y(l.id, "memory_type", p),
          style: { width: 100 }
        },
        /* @__PURE__ */ e.createElement(E, { value: "fact" }, "事实"),
        /* @__PURE__ */ e.createElement(E, { value: "emotion" }, "情感"),
        /* @__PURE__ */ e.createElement(E, { value: "preference" }, "偏好"),
        /* @__PURE__ */ e.createElement(E, { value: "order" }, "订单"),
        /* @__PURE__ */ e.createElement(E, { value: "address" }, "地址"),
        /* @__PURE__ */ e.createElement(E, { value: "contact" }, "联系"),
        /* @__PURE__ */ e.createElement(E, { value: "other" }, "其他")
      ), /* @__PURE__ */ e.createElement(
        j,
        {
          size: "small",
          value: l.importance || 3,
          onChange: (p) => Y(l.id, "importance", p),
          style: { width: 80 }
        },
        /* @__PURE__ */ e.createElement(E, { value: 1 }, "1"),
        /* @__PURE__ */ e.createElement(E, { value: 2 }, "2"),
        /* @__PURE__ */ e.createElement(E, { value: 3 }, "3"),
        /* @__PURE__ */ e.createElement(E, { value: 4 }, "4"),
        /* @__PURE__ */ e.createElement(E, { value: 5 }, "5")
      ), /* @__PURE__ */ e.createElement(_, { type: "secondary" }, new Date(l.created_at).toLocaleString()))), /* @__PURE__ */ e.createElement(
        k,
        {
          type: "primary",
          size: "small",
          icon: /* @__PURE__ */ e.createElement(pe, null),
          disabled: !l._modified,
          onClick: () => h(l)
        },
        "保存"
      ))))
    }
  )), r.length > 0 && /* @__PURE__ */ e.createElement("div", { style: { position: "fixed", bottom: 20, right: 20 } }, /* @__PURE__ */ e.createElement(
    Z,
    {
      title: "确认批量删除",
      description: `确定要删除 ${r.length} 条记忆吗？此操作不可恢复！`,
      onConfirm: $,
      okText: "确认删除",
      cancelText: "取消"
    },
    /* @__PURE__ */ e.createElement(k, { type: "primary", danger: !0, icon: /* @__PURE__ */ e.createElement(ne, null) }, "批量删除(", r.length, ")")
  )), /* @__PURE__ */ e.createElement(
    ue,
    {
      title: "编辑记忆",
      open: b,
      onOk: ie,
      onCancel: () => O(!1)
    },
    /* @__PURE__ */ e.createElement(g, { layout: "vertical" }, /* @__PURE__ */ e.createElement(g.Item, { label: "记忆内容" }, /* @__PURE__ */ e.createElement(
      fe,
      {
        rows: 4,
        value: I.content,
        onChange: (l) => D({ ...I, content: l.target.value })
      }
    )), /* @__PURE__ */ e.createElement(g.Item, { label: "记忆类型" }, /* @__PURE__ */ e.createElement(
      j,
      {
        value: I.memory_type,
        onChange: (l) => D({ ...I, memory_type: l })
      },
      /* @__PURE__ */ e.createElement(E, { value: "fact" }, "事实"),
      /* @__PURE__ */ e.createElement(E, { value: "emotion" }, "情感"),
      /* @__PURE__ */ e.createElement(E, { value: "preference" }, "偏好"),
      /* @__PURE__ */ e.createElement(E, { value: "order" }, "订单"),
      /* @__PURE__ */ e.createElement(E, { value: "address" }, "地址"),
      /* @__PURE__ */ e.createElement(E, { value: "contact" }, "联系"),
      /* @__PURE__ */ e.createElement(E, { value: "other" }, "其他")
    )), /* @__PURE__ */ e.createElement(g.Item, { label: "重要性" }, /* @__PURE__ */ e.createElement(
      j,
      {
        value: I.importance,
        onChange: (l) => D({ ...I, importance: l })
      },
      /* @__PURE__ */ e.createElement(E, { value: 1 }, "1 - 低"),
      /* @__PURE__ */ e.createElement(E, { value: 2 }, "2"),
      /* @__PURE__ */ e.createElement(E, { value: 3 }, "3 - 中"),
      /* @__PURE__ */ e.createElement(E, { value: 4 }, "4"),
      /* @__PURE__ */ e.createElement(E, { value: 5 }, "5 - 高")
    )))
  ));
}
function Se() {
  const [t, a] = d([]), [s, o] = d(!1), [c, i] = d([]), [r, u] = d(null), [n, x] = d(""), b = L(async () => {
    o(!0);
    try {
      const h = await (await fetch(`${f()}/sessions`, {
        headers: v()
      })).json();
      a(h || []);
    } catch (m) {
      console.error("Failed to fetch sessions:", m);
    }
    o(!1);
  }, []);
  F(() => {
    b();
  }, [b]);
  const O = async (m) => {
    try {
      (await fetch(`${f()}/sessions/${m}/rename`, {
        method: "PUT",
        headers: v(),
        body: JSON.stringify({ session_name: n })
      })).ok && (M.success("重命名成功"), a(t.map(
        ($) => $.session_id === m ? { ...$, session_name: n } : $
      )), u(null));
    } catch (h) {
      console.error("Failed to rename:", h);
    }
  }, I = async () => {
    try {
      (await fetch(`${f()}/sessions/batch-delete`, {
        method: "POST",
        headers: v(),
        body: JSON.stringify({ session_ids: c })
      })).ok && (M.success(`已删除 ${c.length} 个会话`), a(t.filter((h) => !c.includes(h.session_id))), i([]));
    } catch (m) {
      console.error("Failed to delete:", m);
    }
  }, D = (m) => {
    var $;
    const h = window.QwenPaw;
    ($ = h == null ? void 0 : h.host) != null && $.openSession ? h.host.openSession(m) : window.open(`/console/chat/${m}`, "_blank");
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(ae, null), " 会话列表"), /* @__PURE__ */ e.createElement("div", { style: { marginBottom: 16 } }, /* @__PURE__ */ e.createElement(k, { onClick: () => i(c.length === t.length ? [] : t.map((m) => m.session_id)) }, c.length === t.length ? "取消全选" : "批量选择"), c.length > 0 && /* @__PURE__ */ e.createElement(_, { style: { marginLeft: 16 } }, "已选择 ", c.length, " 项")), /* @__PURE__ */ e.createElement(B, { spinning: s }, /* @__PURE__ */ e.createElement(
    H,
    {
      dataSource: t,
      renderItem: (m) => /* @__PURE__ */ e.createElement(H.Item, null, /* @__PURE__ */ e.createElement(T, { style: { width: "100%" }, size: "small" }, /* @__PURE__ */ e.createElement("div", { style: { display: "flex", alignItems: "flex-start", gap: 8 } }, /* @__PURE__ */ e.createElement(
        V,
        {
          checked: c.includes(m.session_id),
          onChange: (h) => {
            h.target.checked ? i([...c, m.session_id]) : i(c.filter(($) => $ !== m.session_id));
          }
        }
      ), /* @__PURE__ */ e.createElement("div", { style: { flex: 1 } }, r === m.session_id ? /* @__PURE__ */ e.createElement(K, null, /* @__PURE__ */ e.createElement(
        G,
        {
          value: n,
          onChange: (h) => x(h.target.value),
          size: "small"
        }
      ), /* @__PURE__ */ e.createElement(k, { size: "small", icon: /* @__PURE__ */ e.createElement(he, null), onClick: () => O(m.session_id) }), /* @__PURE__ */ e.createElement(k, { size: "small", icon: /* @__PURE__ */ e.createElement(ye, null), onClick: () => u(null) })) : /* @__PURE__ */ e.createElement(
        "div",
        {
          style: { cursor: "pointer", fontWeight: "bold" },
          onClick: () => {
            u(m.session_id), x(m.session_name || "");
          }
        },
        m.session_name || "未命名会话",
        /* @__PURE__ */ e.createElement(te, { style: { marginLeft: 8, color: "#1890ff" } })
      ), /* @__PURE__ */ e.createElement("div", { style: { marginTop: 4 } }, /* @__PURE__ */ e.createElement(_, { type: "secondary" }, "对话对象: ", m.user_name || "未知")), /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(_, { type: "secondary" }, "会话ID: "), /* @__PURE__ */ e.createElement("a", { onClick: () => D(m.session_id) }, m.session_id)), /* @__PURE__ */ e.createElement("div", null, /* @__PURE__ */ e.createElement(_, { type: "secondary" }, "记忆数: ", m.memory_count, " | 最后活跃: ", new Date(m.last_active).toLocaleString()))))))
    }
  )), c.length > 0 && /* @__PURE__ */ e.createElement("div", { style: { position: "fixed", bottom: 20, right: 20 } }, /* @__PURE__ */ e.createElement(
    Z,
    {
      title: "确认批量删除",
      description: `确定要删除 ${c.length} 个会话吗？此操作不可恢复！`,
      onConfirm: I,
      okText: "确认删除",
      cancelText: "取消"
    },
    /* @__PURE__ */ e.createElement(k, { type: "primary", danger: !0, icon: /* @__PURE__ */ e.createElement(ne, null) }, "批量删除(", c.length, ")")
  )));
}
function ke() {
  const [t, a] = d({}), [s, o] = d(!1), c = L(async () => {
    o(!0);
    try {
      const u = await (await fetch(`${f()}/emotion`, {
        headers: v()
      })).json();
      a(u);
    } catch (r) {
      console.error("Failed to fetch emotion:", r);
    }
    o(!1);
  }, []);
  F(() => {
    c();
  }, [c]);
  const i = (r) => ({ happy: "😊", sad: "😢", angry: "😠", neutral: "😐", excited: "🤩" })[r] || "😐";
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(le, null), " 情感状态"), /* @__PURE__ */ e.createElement(B, { spinning: s }, /* @__PURE__ */ e.createElement(T, { style: { textAlign: "center", marginBottom: 16 } }, /* @__PURE__ */ e.createElement("div", { style: { fontSize: 64, marginBottom: 16 } }, i(t.current_emotion)), /* @__PURE__ */ e.createElement(y, { level: 3 }, "当前: ", t.current_emotion || "neutral", " (", t.intensity || 0, ")")), /* @__PURE__ */ e.createElement(y, { level: 5 }, "情感历史"), /* @__PURE__ */ e.createElement(P, null, (t.history || []).map((r, u) => /* @__PURE__ */ e.createElement(P.Item, { key: u }, new Date(r.timestamp).toLocaleString(), " - ", r.emotion, " (", r.intensity, ")")))));
}
function we() {
  const [t, a] = d([]), [s, o] = d(!1), c = L(async () => {
    o(!0);
    try {
      const r = await (await fetch(`${f()}/memories/timeline`, {
        headers: v()
      })).json();
      a(r || []);
    } catch (i) {
      console.error("Failed to fetch timeline:", i);
    }
    o(!1);
  }, []);
  return F(() => {
    c();
  }, [c]), /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(re, null), " 记忆时间线"), /* @__PURE__ */ e.createElement(B, { spinning: s }, /* @__PURE__ */ e.createElement(P, { mode: "left" }, t.map((i, r) => /* @__PURE__ */ e.createElement(P.Item, { key: r, label: i.date }, /* @__PURE__ */ e.createElement(T, { size: "small" }, /* @__PURE__ */ e.createElement(_, { strong: !0 }, i.count, " 个事件"), /* @__PURE__ */ e.createElement("div", null, i.events.map((u, n) => /* @__PURE__ */ e.createElement(Ee, { key: n }, u)))))))));
}
function Ce() {
  const [t, a] = d({}), [s, o] = d(!1), [c, i] = d(!1), r = L(async () => {
    o(!0);
    try {
      const x = await (await fetch(`${f()}/config`, {
        headers: v()
      })).json();
      a(x);
    } catch (n) {
      console.error("Failed to fetch config:", n);
    }
    o(!1);
  }, []);
  F(() => {
    r();
  }, [r]);
  const u = async () => {
    i(!0);
    try {
      await fetch(`${f()}/config`, {
        method: "POST",
        headers: v(),
        body: JSON.stringify(t)
      }), M.success("配置已保存");
    } catch (n) {
      console.error("Failed to save config:", n);
    }
    i(!1);
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(U, null), " 配置"), /* @__PURE__ */ e.createElement(B, { spinning: s }, /* @__PURE__ */ e.createElement(g, { layout: "vertical" }, /* @__PURE__ */ e.createElement(g.Item, { label: "启用跨会话记忆" }, /* @__PURE__ */ e.createElement(
    J,
    {
      checked: t.enable_cross_session,
      onChange: (n) => a({ ...t, enable_cross_session: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "启用情感跟踪" }, /* @__PURE__ */ e.createElement(
    J,
    {
      checked: t.enable_emotion,
      onChange: (n) => a({ ...t, enable_emotion: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "最大搜索结果数" }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 1,
      max: 20,
      value: t.max_results,
      onChange: (n) => a({ ...t, max_results: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "冷藏天数" }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 7,
      max: 90,
      value: t.frozen_days,
      onChange: (n) => a({ ...t, frozen_days: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "归档天数" }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 30,
      max: 365,
      value: t.archive_days,
      onChange: (n) => a({ ...t, archive_days: n })
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: "删除天数" }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 90,
      max: 730,
      value: t.delete_days,
      onChange: (n) => a({ ...t, delete_days: n })
    }
  )), /* @__PURE__ */ e.createElement(k, { type: "primary", onClick: u, loading: c }, "保存配置"))));
}
function Te() {
  const [t, a] = d("stats");
  return /* @__PURE__ */ e.createElement("div", { style: { height: "100%", display: "flex", flexDirection: "column" } }, /* @__PURE__ */ e.createElement(se, null), /* @__PURE__ */ e.createElement(
    w,
    {
      activeKey: t,
      onChange: a,
      type: "card",
      style: { flex: 1, overflow: "auto" }
    },
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(ee, null), "统计"), key: "stats" }, /* @__PURE__ */ e.createElement(_e, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(W, null), "搜索"), key: "search" }, /* @__PURE__ */ e.createElement(be, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(ae, null), "会话"), key: "sessions" }, /* @__PURE__ */ e.createElement(Se, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(le, null), "情感"), key: "emotion" }, /* @__PURE__ */ e.createElement(ke, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(re, null), "时间线"), key: "timeline" }, /* @__PURE__ */ e.createElement(we, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(U, null), "配置"), key: "config" }, /* @__PURE__ */ e.createElement(Ce, null))
  ));
}
function xe() {
  const [t, a] = d({}), [s, o] = d(!1), c = L(async () => {
    try {
      const O = await (await fetch(`${f()}/sleep/status`, {
        headers: v()
      })).json();
      a(O);
    } catch (b) {
      console.error("Failed to fetch sleep status:", b);
    }
  }, []);
  F(() => {
    c();
    const b = setInterval(c, 5e3);
    return () => clearInterval(b);
  }, [c]);
  const i = async (b) => {
    try {
      await fetch(`${f()}/sleep/force`, {
        method: "POST",
        headers: v(),
        body: JSON.stringify({ sleep_type: b })
      }), M.success(`已进入${b}睡眠`), c();
    } catch (O) {
      console.error("Failed to force sleep:", O);
    }
  }, r = async () => {
    try {
      await fetch(`${f()}/sleep/wakeup`, {
        method: "POST",
        headers: v()
      }), M.success("已唤醒"), c();
    } catch (b) {
      console.error("Failed to wakeup:", b);
    }
  }, u = () => t.status === "active" ? "#52c41a" : t.sleep_type === "deep" ? "#722ed1" : t.sleep_type === "rem" ? "#1890ff" : t.sleep_type === "light" ? "#faad14" : "#d9d9d9", n = () => t.status === "active" ? "活跃状态" : t.sleep_type === "deep" ? "深层睡眠" : t.sleep_type === "rem" ? "REM阶段" : t.sleep_type === "light" ? "浅层睡眠" : "未知状态", x = () => t.status === "active" ? "☀️" : t.sleep_type === "deep" ? "🌙" : t.sleep_type === "rem" ? "💭" : t.sleep_type === "light" ? "⭐" : "❓";
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(q, null), " 睡眠状态"), /* @__PURE__ */ e.createElement(T, { style: { textAlign: "center", marginBottom: 24 } }, /* @__PURE__ */ e.createElement("div", { style: {
    width: 120,
    height: 120,
    borderRadius: "50%",
    background: u(),
    margin: "0 auto 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 48,
    boxShadow: `0 0 20px ${u()}80`
  } }, x()), /* @__PURE__ */ e.createElement(y, { level: 3, style: { color: u() } }, n()), /* @__PURE__ */ e.createElement(_, { type: "secondary" }, "上次活跃: ", t.last_active_time ? new Date(t.last_active_time * 1e3).toLocaleString() : "-")), /* @__PURE__ */ e.createElement(X, { gutter: [16, 16] }, /* @__PURE__ */ e.createElement(S, { span: 8 }, /* @__PURE__ */ e.createElement(
    k,
    {
      block: !0,
      onClick: () => i("light"),
      disabled: t.status !== "active"
    },
    "进入浅层睡眠"
  )), /* @__PURE__ */ e.createElement(S, { span: 8 }, /* @__PURE__ */ e.createElement(
    k,
    {
      block: !0,
      onClick: () => i("deep"),
      disabled: t.status !== "active"
    },
    "进入深层睡眠"
  )), /* @__PURE__ */ e.createElement(S, { span: 8 }, /* @__PURE__ */ e.createElement(
    k,
    {
      block: !0,
      type: "primary",
      onClick: r,
      disabled: t.status === "active"
    },
    "立即唤醒"
  ))));
}
function Ie() {
  const [t, a] = d({}), [s, o] = d(!1), [c, i] = d(!1), r = L(async () => {
    o(!0);
    try {
      const x = await (await fetch(`${f()}/sleep/config`, {
        headers: v()
      })).json();
      a(x);
    } catch (n) {
      console.error("Failed to fetch sleep config:", n);
    }
    o(!1);
  }, []);
  F(() => {
    r();
  }, [r]);
  const u = async () => {
    i(!0);
    try {
      await fetch(`${f()}/sleep/config`, {
        method: "POST",
        headers: v(),
        body: JSON.stringify(t)
      }), M.success("配置已保存");
    } catch (n) {
      console.error("Failed to save sleep config:", n);
    }
    i(!1);
  };
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(U, null), " 参数配置"), /* @__PURE__ */ e.createElement(B, { spinning: s }, /* @__PURE__ */ e.createElement(g, { layout: "vertical" }, /* @__PURE__ */ e.createElement(g.Item, { label: "启用Agent睡眠" }, /* @__PURE__ */ e.createElement(
    J,
    {
      checked: t.enable_agent_sleep,
      onChange: (n) => a({ ...t, enable_agent_sleep: n })
    }
  )), /* @__PURE__ */ e.createElement(R, { orientation: "left" }, "睡眠阶段时长"), /* @__PURE__ */ e.createElement(g.Item, { label: `进入睡眠状态时间: ${t.light_sleep_minutes || 30}分钟` }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 5,
      max: 120,
      value: t.light_sleep_minutes || 30,
      onChange: (n) => a({ ...t, light_sleep_minutes: n }),
      marks: { 5: "5分", 30: "30分", 60: "60分", 120: "120分" }
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: `浅层睡眠持续时间: ${t.rem_minutes || 60}分钟` }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 15,
      max: 180,
      value: t.rem_minutes || 60,
      onChange: (n) => a({ ...t, rem_minutes: n }),
      marks: { 15: "15分", 60: "60分", 120: "120分", 180: "180分" }
    }
  )), /* @__PURE__ */ e.createElement(g.Item, { label: `深层睡眠进入时间: ${t.deep_sleep_minutes || 120}分钟` }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 30,
      max: 240,
      value: t.deep_sleep_minutes || 120,
      onChange: (n) => a({ ...t, deep_sleep_minutes: n }),
      marks: { 30: "30分", 120: "120分", 180: "180分", 240: "240分" }
    }
  )), /* @__PURE__ */ e.createElement(R, { orientation: "left" }, "洞察灯功能"), /* @__PURE__ */ e.createElement(g.Item, { label: "启用洞察灯" }, /* @__PURE__ */ e.createElement(
    J,
    {
      checked: t.enable_insight,
      onChange: (n) => a({ ...t, enable_insight: n })
    }
  ), /* @__PURE__ */ e.createElement(N, { type: "secondary", style: { marginTop: 8 } }, "开启后，Agent在睡眠期间会生成记忆洞察和反思摘要")), /* @__PURE__ */ e.createElement(g.Item, { label: "启用梦境日志" }, /* @__PURE__ */ e.createElement(
    J,
    {
      checked: t.enable_dream_log,
      onChange: (n) => a({ ...t, enable_dream_log: n })
    }
  ), /* @__PURE__ */ e.createElement(N, { type: "secondary", style: { marginTop: 8 } }, "记录睡眠各阶段的处理日志，便于调试和分析")), /* @__PURE__ */ e.createElement(g.Item, { label: "记忆整合天数" }, /* @__PURE__ */ e.createElement(
    A,
    {
      min: 1,
      max: 30,
      value: t.consolidate_days || 7,
      onChange: (n) => a({ ...t, consolidate_days: n })
    }
  )), /* @__PURE__ */ e.createElement(k, { type: "primary", onClick: u, loading: c }, "保存配置"))));
}
function $e() {
  return /* @__PURE__ */ e.createElement("div", { style: { padding: 16 } }, /* @__PURE__ */ e.createElement(y, { level: 4 }, /* @__PURE__ */ e.createElement(ce, null), " 共轭能说明"), /* @__PURE__ */ e.createElement(P, { mode: "left" }, /* @__PURE__ */ e.createElement(P.Item, { label: "活跃状态", color: "green" }, /* @__PURE__ */ e.createElement(y, { level: 5 }, "☀️ 活跃状态 (Active)"), /* @__PURE__ */ e.createElement(N, null, /* @__PURE__ */ e.createElement(_, { strong: !0 }, "共轭能: 高 (High)"), /* @__PURE__ */ e.createElement("br", null), "Agent处于完全活跃状态，实时响应用户请求，记忆系统正常工作。 所有功能模块都处于待命状态。")), /* @__PURE__ */ e.createElement(P.Item, { label: "浅层睡眠", color: "orange" }, /* @__PURE__ */ e.createElement(y, { level: 5 }, "⭐ 浅层睡眠 (Light Sleep)"), /* @__PURE__ */ e.createElement(N, null, /* @__PURE__ */ e.createElement(_, { strong: !0 }, "共轭能: 中-高 (Medium-High)"), /* @__PURE__ */ e.createElement("br", null), "Agent进入轻度休息状态，但仍可快速唤醒。 此阶段会扫描最近7天的对话日志，进行去重和重要性标记。 适合短暂休息或低峰期使用。")), /* @__PURE__ */ e.createElement(P.Item, { label: "REM阶段", color: "blue" }, /* @__PURE__ */ e.createElement(y, { level: 5 }, "💭 REM阶段 (Rapid Eye Movement)"), /* @__PURE__ */ e.createElement(N, null, /* @__PURE__ */ e.createElement(_, { strong: !0 }, "共轭能: 中 (Medium)"), /* @__PURE__ */ e.createElement("br", null), '模拟人类的REM睡眠，Agent进行"梦境处理"。 提取对话主题，发现跨会话的关联模式，生成反思摘要。 识别"持久真理"(Lasting Truths)，为长期记忆做准备。 唤醒需要较长时间。')), /* @__PURE__ */ e.createElement(P.Item, { label: "深层睡眠", color: "purple" }, /* @__PURE__ */ e.createElement(y, { level: 5 }, "🌙 深层睡眠 (Deep Sleep)"), /* @__PURE__ */ e.createElement(N, null, /* @__PURE__ */ e.createElement(_, { strong: !0 }, "共轭能: 低 (Low)"), /* @__PURE__ */ e.createElement("br", null), "Agent进入深度整合状态，大部分功能暂停。 对候选记忆进行六维加权评分(相关性、频率、时效性、多样性、整合度、概念丰富度)。 高分记忆在数据库中标记为`long_term`长期记忆，并更新评分。 执行遗忘曲线算法，自动冷藏、归档、删除过期记忆。 唤醒需要重新加载上下文。"))), /* @__PURE__ */ e.createElement(R, null), /* @__PURE__ */ e.createElement(T, { type: "inner", title: "六维评分系统" }, /* @__PURE__ */ e.createElement(X, { gutter: [16, 16] }, /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(C, { title: "相关性 (30%)", value: "与用户长期兴趣的相关程度" })), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(C, { title: "频率 (24%)", value: "记忆被访问的频率" })), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(C, { title: "时效性 (15%)", value: "记忆的时效性权重" })), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(C, { title: "查询多样性 (15%)", value: "被查询的模式多样性" })), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(C, { title: "整合度 (10%)", value: "与其他记忆的关联程度" })), /* @__PURE__ */ e.createElement(S, { span: 12 }, /* @__PURE__ */ e.createElement(C, { title: "概念丰富度 (6%)", value: "内容的概念密度" })))));
}
function Fe() {
  const [t, a] = d("status");
  return /* @__PURE__ */ e.createElement("div", { style: { height: "100%", display: "flex", flexDirection: "column" } }, /* @__PURE__ */ e.createElement(se, null), /* @__PURE__ */ e.createElement(y, { level: 4, style: { padding: "0 16px", marginTop: 16 } }, /* @__PURE__ */ e.createElement(q, null), " HumanThinking 睡眠管理"), /* @__PURE__ */ e.createElement(
    w,
    {
      activeKey: t,
      onChange: a,
      type: "card",
      style: { flex: 1, overflow: "auto" }
    },
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(q, null), "睡眠状态"), key: "status" }, /* @__PURE__ */ e.createElement(xe, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(U, null), "参数配置"), key: "config" }, /* @__PURE__ */ e.createElement(Ie, null)),
    /* @__PURE__ */ e.createElement(w.TabPane, { tab: /* @__PURE__ */ e.createElement("span", null, /* @__PURE__ */ e.createElement(ce, null), "共轭能说明"), key: "energy" }, /* @__PURE__ */ e.createElement($e, null))
  ));
}
function Le() {
  return /* @__PURE__ */ e.createElement(Te, null);
}
export {
  se as AgentInfoBar,
  Ce as ConfigPanel,
  ke as EmotionIndicator,
  Le as HumanThinkingDashboard,
  Te as MemoryManagementSidebar,
  be as MemorySearch,
  _e as MemoryStatsPanel,
  we as MemoryTimeline,
  Se as SessionList,
  Ie as SleepConfigPanel,
  $e as SleepEnergyPanel,
  Fe as SleepManagementSidebar,
  xe as SleepStatusPanel,
  Te as default
};
