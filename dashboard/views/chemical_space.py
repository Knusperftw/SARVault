"""Chemical-space page."""

import streamlit as st

from dashboard import charts, data, logic

_AXES = ["mw_freebase", "alogp", "psa", "qed_weighted", "rotatable_bonds"]


def render(con, scope):
    st.header("🧪 Chemical space")
    target_sar = data.load_target_sar(con)
    catalog = data.load_compound_catalog(con)
    keys = logic.resolve_scope_keys(target_sar, catalog, scope)
    chem = data.load_chemical_space(con)
    chem = chem[chem["compound_key"].isin(keys)]
    if chem.empty:
        st.info("No compounds in the current scope.")
        return

    col_x, col_y = st.columns(2)
    x_col = col_x.selectbox("X axis", _AXES, index=0)
    y_col = col_y.selectbox("Y axis", _AXES, index=1)
    st.caption(f"{len(chem)} compounds")
    st.plotly_chart(charts.chemical_space_scatter(chem, x_col, y_col), width="stretch")
    st.plotly_chart(charts.property_histogram(chem, x_col), width="stretch")
