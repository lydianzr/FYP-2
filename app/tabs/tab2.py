# app/tabs/tab2.py
import os
import streamlit as st
import pandas as pd

def render_tab2(project_root: str):
    st.header("2. Benchmark Dashboard (Pre-computed Results)")
    st.write("Interactive visualization of pre-computed RQ1 and RQ2 benchmarking metrics across dataset formats and extraction paradigms.")

    results_dir = os.path.join(project_root, "results")
    summary_path = os.path.join(results_dir, "summary_metrics.csv")
    detailed_path = os.path.join(results_dir, "benchmark_results.csv")

    if not os.path.exists(summary_path) or not os.path.exists(detailed_path):
        st.warning("Pre-computed benchmark results not found in `results/`. Please run `python scripts/run_benchmark.py` first.")
        return

    summary_df = pd.read_csv(summary_path)
    detailed_df = pd.read_csv(detailed_path)

    # Sidebar Filter Controls for Interactive Data Slicing
    st.subheader("📊 Interactive Data Filters")
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        selected_paradigms = st.multiselect(
            "Filter Paradigm / Method:",
            options=detailed_df["paradigm"].unique().tolist(),
            default=detailed_df["paradigm"].unique().tolist()
        )

    with col_f2:
        available_formats = detailed_df["file_format"].unique().tolist() if "file_format" in detailed_df.columns else []
        selected_formats = st.multiselect(
            "Filter File Format:",
            options=available_formats,
            default=available_formats
        )

    # Filtered DataFrames
    filtered_df = detailed_df[
        (detailed_df["paradigm"].isin(selected_paradigms)) &
        (detailed_df["file_format"].isin(selected_formats) if available_formats else True)
    ]

    # Overview Cards
    st.markdown("---")
    st.subheader("Aggregated Macro Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average ANLS", f"{filtered_df['macro_anls'].mean():.4f}" if not filtered_df.empty else "N/A")
    c2.metric("Average Exact Match", f"{(filtered_df['macro_exact_match'].mean() * 100):.1f}%" if not filtered_df.empty else "N/A")
    c3.metric("Average Latency", f"{filtered_df['latency_seconds'].mean():.2f}s" if not filtered_df.empty else "N/A")
    c4.metric("Average Cost / Doc", f"${filtered_df['cost_usd'].mean():.4f}" if not filtered_df.empty else "N/A")

    # Visual Comparison Charts
    st.markdown("---")
    st.subheader("Method Comparison Visualizations")

    chart_tab1, chart_tab2 = st.tabs(["Accuracy Comparison (ANLS vs EM)", "Trade-off Analysis (Accuracy vs Latency)"])

    with chart_tab1:
        if not filtered_df.empty:
            chart_data = filtered_df.groupby("paradigm")[["macro_anls", "macro_exact_match", "line_item_f1"]].mean()
            st.bar_chart(chart_data)

    with chart_tab2:
        if not filtered_df.empty:
            tradeoff_data = filtered_df.groupby("paradigm")[["macro_anls", "latency_seconds"]].mean()
            st.scatter_chart(tradeoff_data, x="latency_seconds", y="macro_anls")

    # Filtered Data Table
    st.markdown("---")
    st.subheader("Detailed Evaluation Records")
    st.dataframe(filtered_df, use_container_width=True)