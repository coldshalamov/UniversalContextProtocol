"""
UCP Debug Dashboard.

A Streamlit-based visualization for debugging UCP:
- Current session state
- Active tools and routing decisions
- Tool usage statistics
- Search interface for the Tool Zoo

Run with: streamlit run src/ucp/dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import streamlit as st
    import pandas as pd
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from ucp.config import UCPConfig
from ucp.tool_zoo import HybridToolZoo
from ucp.session import SessionManager
from ucp.router import AdaptiveRouter


def load_components(config_path: str | None = None):
    """Load UCP components."""
    config = UCPConfig.load(config_path)

    tool_zoo = HybridToolZoo(config.tool_zoo)
    tool_zoo.initialize()

    session_manager = SessionManager(config.session)

    router = AdaptiveRouter(config.router, tool_zoo)

    return config, tool_zoo, session_manager, router


def main():
    """Main dashboard entry point."""
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not installed. Run: pip install streamlit")
        return

    st.set_page_config(
        page_title="UCP Dashboard",
        page_icon="🔧",
        layout="wide",
    )

    st.title("🔧 Universal Context Protocol Dashboard")
    st.markdown("Debug and visualize UCP routing decisions")

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
        config, tool_zoo, session_manager, router = load_components(
            config_path if Path(config_path).exists() else None
        )
    except Exception as e:
        st.error(f"Failed to load configuration: {e}")
        st.info("Using default configuration")
        config, tool_zoo, session_manager, router = load_components(None)

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Tool Search",
        "📊 Tool Zoo Stats",
        "💬 Session Explorer",
        "📈 Router Learning"
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

    # Footer
    st.markdown("---")
    st.markdown(
        "UCP Dashboard | "
        f"Config: `{config_path}` | "
        f"Tools: {tool_zoo.get_stats()['total_tools']}"
    )


if __name__ == "__main__":
    main()
