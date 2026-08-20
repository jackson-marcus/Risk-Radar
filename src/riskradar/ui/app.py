"""Streamlit demo: risk board, vendor detail with gaps, diligence assistant."""

from __future__ import annotations

import os

import httpx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

API_URL = os.environ.get("RISKRADAR_API_URL", "http://localhost:8360")

st.set_page_config(page_title="riskradar", page_icon="🛰️", layout="wide")
st.title("🛰️ riskradar")
st.caption("Vendor risk: time-decayed scoring, deterioration watchlist, policy-grounded diligence")


def _ok() -> bool:
    try:
        return httpx.get(f"{API_URL}/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


if not _ok():
    st.error(f"API not reachable at {API_URL}. Start it with `make api`.")
    st.stop()

tab_board, tab_vendor, tab_ask = st.tabs(
    ["📊 Risk board", "🏢 Vendor detail", "📖 Diligence assistant"]
)

with tab_board:
    body = httpx.get(f"{API_URL}/vendors", timeout=60).json()
    m = body["metrics"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Ranking vs latent truth (Spearman)", f"{m['rank_spearman']:.2f}")
    c2.metric(
        "Watchlist",
        m["watchlist_size"],
        f"caught {m['deteriorating_caught']}/{m['deteriorating_planted']} deteriorating",
    )
    c3.metric("Watch recall / precision", f"{m['watch_recall']:.0%} / {m['watch_precision']:.0%}")

    df = pd.DataFrame(body["vendors"])
    st.dataframe(df.head(20), hide_index=True, use_container_width=True)

    watch = httpx.get(f"{API_URL}/watchlist", timeout=30).json()
    if watch:
        st.subheader("⚠️ Watchlist (score or 30-day trend)")
        st.dataframe(pd.DataFrame(watch), hide_index=True, use_container_width=True)

with tab_vendor:
    body = httpx.get(f"{API_URL}/vendors", timeout=60).json()
    options = {v["vendor_id"]: v["name"] for v in body["vendors"]}
    pick = st.selectbox("Vendor", list(options), format_func=options.get)
    detail = httpx.get(f"{API_URL}/vendor/{pick}", timeout=30).json()
    v = detail["vendor"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Composite score", v["score"], f"{v['trend_30d']:+.1f} in 30d")
    c2.metric("Sector", v["sector"])
    c3.metric("Annual spend", f"${v['annual_spend_usd']:,}")

    hist = detail["history"]
    fig = go.Figure(
        go.Scatter(x=[h["day"] for h in hist], y=[h["score"] for h in hist], mode="lines+markers")
    )
    fig.update_layout(height=300, xaxis_title="Day", yaxis_title="Composite risk score")
    st.plotly_chart(fig, use_container_width=True)

    if detail["diligence_gaps"]:
        st.subheader("Diligence gaps (policy-grounded)")
        for gap in detail["diligence_gaps"]:
            st.markdown(f"**§ {gap['rule_id']}** — {gap['finding']}")
            st.caption(gap["policy"] + "…")
    st.subheader("Recent events")
    st.dataframe(pd.DataFrame(detail["recent_events"]), hide_index=True, use_container_width=True)

with tab_ask:
    question = st.text_input("Ask the diligence policy", "When do we need a second source?")
    if st.button("Ask", type="primary"):
        body = httpx.post(
            f"{API_URL}/diligence/ask", json={"question": question}, timeout=30
        ).json()
        if not body["matched"]:
            st.warning("No policy covers that — consider drafting one.")
        for rule in body["rules"]:
            with st.expander(f"§ {rule['rule_id']} (score {rule['score']})", expanded=True):
                st.write(rule["body"])
