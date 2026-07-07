"""Payload Classes: compare ADC-payload mechanism classes (tubulin vs topoisomerase)."""

import streamlit as st

from dashboard import charts, data, logic

_INTRO = """
Compounds grouped by **ADC-payload mechanism class** (from the target they act on),
so the tubulin and topoisomerase classes compare head to head. This is the chemistry
behind the ADC-payload shift from tubulin inhibitors (auristatins, maytansinoids)
toward topoisomerase-I inhibitors (camptothecin / exatecan).
"""

_CLASS_LABELS = {
    "tubulin_inhibitor": "Tubulin inhibitor",
    "topo1_inhibitor": "Topoisomerase-I inhibitor",
    "topo2_inhibitor": "Topoisomerase-II inhibitor",
}


def _relabel(series):
    return series.map(lambda c: _CLASS_LABELS.get(c, c))


def render(con, scope):
    st.markdown(_INTRO)

    profile = data.load_payload_class_profile(con)
    if profile.empty:
        st.info("No payload-class profile is available in this warehouse yet.")
        return

    display = profile.copy()
    display["payload_class"] = _relabel(display["payload_class"])
    display = display.rename(
        columns={
            "payload_class": "payload class",
            "n_compounds": "compounds",
            "n_measurements": "measurements",
            "median_pchembl": "median pChEMBL",
            "max_pchembl": "max pChEMBL",
            "p25_pchembl": "p25",
            "p75_pchembl": "p75",
            "n_sub_nanomolar": "sub-nM compounds",
        }
    )
    st.dataframe(display, hide_index=True, width="stretch")

    st.divider()
    st.subheader("Potency distribution by class")
    catalog = data.load_compound_catalog(con)
    potency = logic.payload_class_potency(catalog)
    if potency.empty:
        st.info("No per-compound potency available to plot.")
        return
    potency = potency.assign(payload_class=_relabel(potency["payload_class"]))
    st.plotly_chart(charts.payload_class_potency(potency), use_container_width=True)
    st.caption(
        "Best per-compound pChEMBL across the class's targets. Higher is more potent; "
        "pChEMBL >= 9 is sub-nanomolar, the potency band that makes a viable ADC payload."
    )
