"""
UCP Debug Dashboard - Extended with SOTA Metrics.

A Streamlit-based visualization for debugging UCP:
- Current session state
- Active tools and routing decisions
- Tool usage statistics
- Search interface for the Tool Zoo
- SOTA pipeline metrics: bandit stats, bias learning, telemetry

Run with: streamlit run src/ucp/dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import streamlit as st
    import pandas as pd
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from ucp.config import UCPConfig
from ucp.tool_zoo import HybridToolZoo
from ucp.session import SessionManager
from ucp.router import AdaptiveRouter, SOTARouter, create_router


def load_components(config_path: str | None = None):
    """Load UCP components."""
    config = UCPConfig.load(config_path)

    tool_zoo = HybridToolZoo(config.tool_zoo)
    tool_zoo.initialize()

    session_manager = SessionManager(config.session)

    # Load telemetry store if enabled
    telemetry_store = None
    if config.telemetry.enabled:
        from ucp.telemetry import SQLiteTelemetryStore
        if Path(config.telemetry.db_path).exists():
            telemetry_store = SQLiteTelemetryStore(config.telemetry.db_path)

    router = create_router(config.router, tool_zoo, telemetry_store)

    return config, tool_zoo, session_manager, router, telemetry_store


def render_sota_tab(router: Any, telemetry_store: Any) -> None:
    """Render the SOTA pipeline metrics tab."""
    st.header("🚀 SOTA Pipeline Metrics")
    
    if not isinstance(router, SOTARouter):
        st.info("SOTA mode not enabled. Set router.strategy: sota in config.")
        return
    
    # Get SOTA stats
    stats = router.get_sota_stats()
    
    # Bandit Statistics
    st.subheader("🎰 Bandit Scorer")
    if "bandit" in stats:
        bandit = stats["bandit"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Updates", bandit.get("update_count", 0))
        with col2:
            st.metric("Feature Dim", bandit.get("feature_dim", 0))
        with col3:
            st.metric("Exploration", bandit.get("exploration_type", "N/A"))
        
        st.markdown(f"**Weight Mean:** {bandit.get('weight_mean', 0):.4f}")
        st.markdown(f"**Weight Std:** {bandit.get('weight_std', 0):.4f}")
        st.markdown(f"**Bias:** {bandit.get('bias', 0):.4f}")
    else:
        st.info("Bandit scorer not initialized")
    
    st.divider()
    
    # Bias Learning Statistics
    st.subheader("📈 Per-Tool Bias Learning")
    if "bias" in stats:
        bias = stats["bias"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tools Tracked", bias.get("tool_count", 0))
        with col2:
            st.metric("Total Updates", bias.get("total_updates", 0))
        with col3:
            st.metric("Mean Bias", f"{bias.get('mean_bias', 0):.3f}")
        
        # Show top biased tools
        if router.bias_store:
            st.markdown("**Top Positive Biases:**")
            top_pos = router.bias_store.get_top_biased_tools(5, positive=True)
            if top_pos:
                for tool, b in top_pos:
                    st.markdown(f"  • `{tool}`: {b:+.3f}")
            
            st.markdown("**Top Negative Biases:**")
            top_neg = router.bias_store.get_top_biased_tools(5, positive=False)
            if top_neg:
                for tool, b in top_neg:
                    st.markdown(f"  • `{tool}`: {b:+.3f}")
    else:
        st.info("Bias learning not initialized")
    
    st.divider()
    
    # Telemetry Statistics
    st.subheader("📊 Telemetry Summary")
    if "telemetry" in stats:
        telem = stats["telemetry"]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Routing Events", telem.get("routing_events", 0))
            st.metric("Tool Calls", telem.get("tool_calls", 0))
        with col2:
            st.metric("Success Rate", f"{telem.get('overall_success_rate', 0):.1%}")
            st.metric("Exploration Rate", f"{telem.get('exploration_rate', 0):.1%}")
        
        st.metric("Avg Tools Selected", f"{telem.get('avg_tools_selected', 0):.1f}")
        st.metric("Avg Selection Time (ms)", f"{telem.get('avg_selection_time_ms', 0):.1f}")
    else:
        st.info("Telemetry not available")


def render_telemetry_details(telemetry_store: Any) -> None:
    """Render detailed telemetry analysis."""
    st.header("📈 Telemetry Analysis")
    
    if not telemetry_store:
        st.info("Telemetry store not available")
        return
    
    # Recent routing events
    st.subheader("Recent Routing Events")
    events = telemetry_store.get_routing_events(limit=20)
    
    if events:
        event_data = []
        for e in events:
            event_data.append({
                "Timestamp": e.timestamp.strftime("%H:%M:%S"),
                "Strategy": e.strategy,
                "Candidates": e.total_candidates,
                "Selected": len(e.selected_tools),
                "Tokens": e.context_tokens_used,
                "Time (ms)": f"{e.selection_time_ms:.1f}",
                "Explored": "✓" if e.exploration_triggered else "",
            })
        st.dataframe(pd.DataFrame(event_data), use_container_width=True)
    else:
        st.info("No routing events recorded")
    
    st.divider()
    
    # Tool success heatmap
    st.subheader("Tool Success Rates")
    all_stats = telemetry_store.get_tool_stats()
    
    if all_stats:
        heatmap_data = []
        for tool_name, stats in all_stats.items():
            heatmap_data.append({
                "Tool": tool_name[:30],  # Truncate
                "Calls": stats.get("total_calls", 0),
                "Success Rate": stats.get("rolling_success_rate", 0.5),
                "Avg Latency (ms)": stats.get("avg_latency_ms", 0),
                "Avg Reward": stats.get("avg_reward", 0),
            })
        
        df = pd.DataFrame(heatmap_data)
        if not df.empty:
            # Sort by calls
            df = df.sort_values("Calls", ascending=False).head(20)
            
            # Create bar chart for success rates
            st.bar_chart(df.set_index("Tool")["Success Rate"])
            
            # Full table
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No tool statistics available")
    
    st.divider()
    
    # Recent rewards
    st.subheader("Recent Reward Signals")
    rewards = telemetry_store.get_recent_rewards(limit=20)
    
    if rewards:
        reward_data = []
        for r in rewards:
            reward_data.append({
                "Timestamp": r.timestamp.strftime("%H:%M:%S"),
                "Tool": r.tool_name[:30],
                "Success": f"{r.success_reward:+.1f}",
                "Latency": f"{r.latency_penalty:+.2f}",
                "Context": f"{r.context_cost_penalty:+.2f}",
                "Total": f"{r.total_reward:+.2f}",
            })
        st.dataframe(pd.DataFrame(reward_data), use_container_width=True)
    else:
        st.info("No reward signals recorded")


def main():
    """Main dashboard entry point."""
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not installed. Run: pip install streamlit pandas")
        return

    st.set_page_config(
        page_title="UCP Dashboard",
        page_icon="🔧",
        layout="wide",
    )

    st.title("🔧 Universal Context Protocol Dashboard")
    st.markdown("Debug and visualize UCP routing decisions - **SOTA Edition**")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        config_path = st.text_input(
            "Config file path",
            value="ucp_config.yaml",
            help="Path to UCP configuration file"
        )

        if st.button("Reload Configuration"):
            st.cache_data.clear()
            st.rerun()

    # Load components
    try:
        config, tool_zoo, session_manager, router, telemetry_store = load_components(
            config_path if Path(config_path).exists() else None
        )
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
        st.info("Using default configuration")
        config, tool_zoo, session_manager, router, telemetry_store = load_components(None)

    # Display strategy mode
    strategy = getattr(config.router, 'strategy', 'baseline')
    st.markdown(f"**Strategy Mode:** `{strategy.upper()}`")

    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Tool Search",
        "📊 Tool Zoo Stats",
        "💬 Session Explorer",
        "📈 Router Learning",
        "🚀 SOTA Metrics",
        "📉 Telemetry Details",
    ])

    # Tab 1: Tool Search
    with tab1:
        st.header("Search Tools")

        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input(
                "Search query",
                placeholder="e.g., send email, create PR, schedule meeting"
            )
        with col2:
            top_k = st.number_input("Results", min_value=1, max_value=20, value=5)

        search_mode = st.radio(
            "Search mode",
            ["Hybrid (Recommended)", "Semantic Only", "Keyword Only"],
            horizontal=True
        )

        if query:
            with st.spinner("Searching..."):
                if search_mode == "Hybrid (Recommended)":
                    results = tool_zoo.hybrid_search(query, top_k=top_k)
                elif search_mode == "Semantic Only":
                    results = tool_zoo.search(query, top_k=top_k)
                else:
                    results = tool_zoo.keyword_search(query, top_k=top_k)

            if results:
                st.subheader(f"Found {len(results)} tools")

                for tool, score in results:
                    with st.expander(f"**{tool.name}** - Score: {score:.3f}"):
                        st.markdown(f"**Description:** {tool.description}")
                        st.markdown(f"**Server:** `{tool.server_name}`")
                        st.markdown(f"**Tags:** {', '.join(tool.tags) if tool.tags else 'None'}")
                        st.markdown(f"**Domain:** {tool.domain or 'Unspecified'}")

                        if tool.input_schema:
                            st.markdown("**Input Schema:**")
                            st.json(tool.input_schema)
            else:
                st.info("No tools found matching your query")

        # Domain detection preview
        st.subheader("Domain Detection")
        test_context = st.text_area(
            "Test context for domain detection",
            placeholder="Enter a sample conversation to test domain detection"
        )
        if test_context:
            domains = router.detect_domain(test_context)
            if domains:
                st.success(f"Detected domains: {', '.join(domains)}")
            else:
                st.warning("No specific domain detected")

    # Tab 2: Tool Zoo Stats
    with tab2:
        st.header("Tool Zoo Statistics")

        stats = tool_zoo.get_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tools", stats["total_tools"])
        with col2:
            st.metric("Servers", len(stats["servers"]))
        with col3:
            st.metric("Domains", len(stats["domains"]))

        # Server breakdown
        st.subheader("Tools by Server")
        all_tools = tool_zoo.get_all_tools()

        if all_tools:
            server_counts = {}
            for tool in all_tools:
                server_counts[tool.server_name] = server_counts.get(tool.server_name, 0) + 1

            df = pd.DataFrame([
                {"Server": k, "Tool Count": v}
                for k, v in sorted(server_counts.items(), key=lambda x: -x[1])
            ])
            st.bar_chart(df.set_index("Server"))

            # Domain breakdown
            st.subheader("Tools by Domain")
            domain_counts = {}
            for tool in all_tools:
                domain = tool.domain or "Unspecified"
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

            df_domain = pd.DataFrame([
                {"Domain": k, "Tool Count": v}
                for k, v in sorted(domain_counts.items(), key=lambda x: -x[1])
            ])
            st.bar_chart(df_domain.set_index("Domain"))

            # Full tool list
            st.subheader("All Tools")
            tool_data = [
                {
                    "Name": t.name,
                    "Server": t.server_name,
                    "Domain": t.domain or "",
                    "Tags": ", ".join(t.tags),
                    "Description": t.description[:100] + "..." if len(t.description) > 100 else t.description
                }
                for t in all_tools
            ]
            st.dataframe(pd.DataFrame(tool_data), use_container_width=True)
        else:
            st.info("No tools indexed yet. Run `ucp index` to populate the Tool Zoo.")

    # Tab 3: Session Explorer
    with tab3:
        st.header("Session Explorer")

        # Tool usage stats
        usage_stats = session_manager.get_tool_usage_stats()

        if usage_stats:
            st.subheader("Global Tool Usage")

            usage_data = [
                {
                    "Tool": name,
                    "Uses": stats["uses"],
                    "Success Rate": f"{stats['success_rate']:.1%}",
                    "Avg Time (ms)": f"{stats['avg_time_ms']:.1f}" if stats['avg_time_ms'] else "N/A"
                }
                for name, stats in sorted(usage_stats.items(), key=lambda x: -x[1]["uses"])
            ]
            st.dataframe(pd.DataFrame(usage_data), use_container_width=True)

            # Visualize usage
            st.subheader("Tool Usage Distribution")
            usage_df = pd.DataFrame([
                {"Tool": name[:20], "Uses": stats["uses"]}
                for name, stats in usage_stats.items()
            ])
            if not usage_df.empty:
                st.bar_chart(usage_df.set_index("Tool"))
        else:
            st.info("No tool usage data yet")

        # Session cleanup
        st.subheader("Session Management")
        if st.button("Cleanup Old Sessions"):
            cleaned = session_manager.cleanup_old_sessions()
            st.success(f"Cleaned up {cleaned} old sessions")

    # Tab 4: Router Learning
    with tab4:
        st.header("Router Learning Statistics")

        if isinstance(router, AdaptiveRouter):
            learning_stats = router.get_learning_stats()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predictions", learning_stats.get("predictions", 0))
            with col2:
                precision = learning_stats.get("avg_precision", 0)
                st.metric("Avg Precision", f"{precision:.1%}" if precision else "N/A")
            with col3:
                recall = learning_stats.get("avg_recall", 0)
                st.metric("Avg Recall", f"{recall:.1%}" if recall else "N/A")

            st.metric("Co-occurrence Pairs", learning_stats.get("cooccurrence_pairs", 0))

            # Export training data
            st.subheader("Training Data Export")
            st.markdown("""
            Export collected data for RAFT fine-tuning. The data includes:
            - Query: The context used for routing
            - Candidates: Tools that were predicted
            - Correct: Tools that were actually used
            """)

            if st.button("Export Training Data"):
                training_data = router.export_training_data()
                if training_data:
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(training_data, indent=2),
                        file_name="ucp_training_data.json",
                        mime="application/json"
                    )
                    st.success(f"Exported {len(training_data)} training examples")
                else:
                    st.info("No training data available yet")

            # Co-occurrence explorer
            st.subheader("Tool Co-occurrence")
            st.markdown("Tools that are frequently used together")

            if router._tool_cooccurrence:
                cooccur_data = []
                for tool_a, related in router._tool_cooccurrence.items():
                    for tool_b, count in related.items():
                        cooccur_data.append({
                            "Tool A": tool_a,
                            "Tool B": tool_b,
                            "Co-occurrences": count
                        })

                if cooccur_data:
                    df = pd.DataFrame(cooccur_data)
                    df = df.sort_values("Co-occurrences", ascending=False).head(20)
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No co-occurrence data yet. Use tools to generate patterns.")
        else:
            st.info("Adaptive learning requires AdaptiveRouter")

    # Tab 5: SOTA Metrics
    with tab5:
        render_sota_tab(router, telemetry_store)

    # Tab 6: Telemetry Details
    with tab6:
        render_telemetry_details(telemetry_store)

    # Footer
    st.markdown("---")
    st.markdown(
        f"UCP Dashboard | "
        f"Config: `{config_path}` | "
        f"Strategy: `{strategy}` | "
        f"Tools: {tool_zoo.get_stats()['total_tools']}"
    )


if __name__ == "__main__":
    main()
