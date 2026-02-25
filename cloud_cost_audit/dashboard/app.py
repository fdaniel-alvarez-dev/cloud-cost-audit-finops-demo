from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


def _load_table(db_path: Path, query: str) -> pd.DataFrame:
    with duckdb.connect(str(db_path), read_only=True) as con:
        return con.execute(query).df()


def main() -> None:
    st.set_page_config(page_title="Cloud Cost Audit (Demo)", layout="wide")
    st.title("Cloud Cost Audit (Demo)")

    db_path_str = st.sidebar.text_input("DuckDB path", value="out/audit.duckdb")
    db_path = Path(db_path_str)
    if not db_path.exists():
        st.error(f"DuckDB not found at {db_path}. Run `make demo` first.")
        return

    cost_query = """
    select provider, service, sum(cost_usd) as cost_usd
    from unified_line_items
    group by 1,2
    order by cost_usd desc
    """
    cost_by_service = _load_table(
        db_path,
        cost_query,
    )
    quick_wins = _load_table(db_path, "select * from quick_wins order by rank asc")

    left, right = st.columns(2)
    with left:
        st.subheader("Cost by provider/service")
        fig = px.bar(
            cost_by_service,
            x="cost_usd",
            y=cost_by_service["provider"] + " / " + cost_by_service["service"],
            orientation="h",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Top 10 quick wins")
        st.dataframe(quick_wins, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
