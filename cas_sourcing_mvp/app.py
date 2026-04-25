from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.pricing import (
    normalize_price_points,
    quantity_to_grams,
    choose_anchor_price,
    estimate_bulk_price,
)
from core.supplier_engine import find_suppliers_by_cas, supplier_search_links
from core.ranking import rank_supplier_rows
from utils.validation import is_valid_cas

st.set_page_config(
    page_title="CAS Sourcing MVP",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 CAS Sourcing & Procurement Intelligence MVP")
st.caption("Testable Streamlit prototype: CAS input → suppliers → visible pricing → normalized price → bulk estimate → shortlist.")

with st.sidebar:
    st.header("Search Inputs")
    cas_number = st.text_input("CAS Number", value="103-90-2", help="Example test CAS: 103-90-2")
    desired_quantity = st.number_input("Desired Quantity", min_value=0.0001, value=1.0, step=0.5)
    desired_unit = st.selectbox("Desired Unit", ["g", "kg", "mg"], index=1)
    required_purity = st.text_input("Required Purity / Grade", value="98%+")
    run_search = st.button("Run CAS Sourcing Search", type="primary")

st.info(
    "MVP rule: visible supplier/catalog prices are treated as facts. Bulk prices are clearly labeled estimates until confirmed by RFQ."
)

if run_search:
    cas_valid = is_valid_cas(cas_number)
    desired_qty_g = quantity_to_grams(desired_quantity, desired_unit)

    if not cas_valid:
        st.error("Invalid CAS number format or checksum. Please verify the CAS number.")
        st.stop()

    if desired_qty_g is None or desired_qty_g <= 0:
        st.error("Desired quantity must be convertible to grams and greater than zero.")
        st.stop()

    raw_results = find_suppliers_by_cas(cas_number)
    search_links = supplier_search_links(cas_number)

    if raw_results.empty:
        st.warning("No mock supplier data found yet for this CAS. Use the supplier search links below to manually check vendors.")
        st.dataframe(search_links, use_container_width=True, hide_index=True)
        st.stop()

    normalized = normalize_price_points(raw_results)
    ranked = rank_supplier_rows(normalized)

    st.subheader("1. Supplier Discovery")
    st.dataframe(
        ranked[
            [
                "supplier",
                "chemical_name",
                "cas_number",
                "region",
                "purity",
                "pack_size",
                "pack_unit",
                "listed_price_usd",
                "price_per_g",
                "stock_status",
                "score",
                "ranking_reason",
                "product_url",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("2. Visible Price Normalization")
    visible = ranked[ranked["has_visible_price"]].copy()
    if visible.empty:
        st.warning("No visible prices found in current data. The system can still provide supplier links, but bulk estimate needs at least one price point.")
    else:
        chart_df = visible.sort_values("price_per_g")
        fig = px.bar(
            chart_df,
            x="supplier",
            y="price_per_g",
            hover_data=["pack_size", "pack_unit", "listed_price_usd", "purity"],
            title="Visible Catalog Price Normalized to $/g",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            visible[["supplier", "pack_size", "pack_unit", "listed_price_usd", "pack_size_g", "price_per_g", "purity"]],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("3. Bulk Estimate Scenarios")
        anchor = choose_anchor_price(visible, desired_qty_g)
        if anchor is None:
            st.warning("Could not choose an anchor price from visible price points.")
        else:
            visible_count = len(visible)
            estimates = [
                estimate_bulk_price(
                    anchor_pack_g=float(anchor["pack_size_g"]),
                    anchor_total_price=float(anchor["listed_price_usd"]),
                    desired_qty_g=float(desired_qty_g),
                    scenario=scenario,
                    visible_price_points=visible_count,
                )
                for scenario in ["Conservative", "Base", "Aggressive"]
            ]
            est_df = pd.DataFrame([e.__dict__ for e in estimates])

            c1, c2, c3 = st.columns(3)
            base_row = est_df[est_df["scenario"] == "Base"].iloc[0]
            c1.metric("Desired Quantity", f"{desired_quantity:g} {desired_unit}")
            c2.metric("Base Estimated Total", f"${base_row['estimated_total_price']:,.2f}")
            c3.metric("Base Estimated $/g", f"${base_row['estimated_unit_price_per_g']:,.4f}")

            st.write(
                f"Anchor used: **{anchor['supplier']}**, {anchor['pack_size']:g} {anchor['pack_unit']} at "
                f"**${float(anchor['listed_price_usd']):,.2f}**."
            )
            st.dataframe(est_df, use_container_width=True, hide_index=True)

            fig2 = px.bar(
                est_df,
                x="scenario",
                y="estimated_total_price",
                hover_data=["estimated_unit_price_per_g", "discount_vs_anchor_pct", "confidence"],
                title="Estimated Total Price by Scenario",
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("4. Manual Supplier Search Links")
    st.caption("These links help us validate supplier availability while we build automated sourcing connectors later.")
    st.dataframe(search_links, use_container_width=True, hide_index=True)

    st.subheader("5. Export")
    export_df = ranked.copy()
    export_df["requested_quantity"] = desired_quantity
    export_df["requested_unit"] = desired_unit
    export_df["required_purity"] = required_purity
    csv = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Supplier Shortlist CSV",
        data=csv,
        file_name=f"cas_supplier_shortlist_{cas_number.replace('-', '_')}.csv",
        mime="text/csv",
    )
else:
    st.subheader("How to test")
    st.markdown(
        """
        1. Keep the default CAS `103-90-2` for the first test.
        2. Enter desired quantity, such as `1 kg`.
        3. Click **Run CAS Sourcing Search**.
        4. Review supplier ranking, visible price normalization, and bulk estimate scenarios.

        Current prototype uses mock supplier-price rows so we can validate the workflow before adding live web/API connectors.
        """
    )
