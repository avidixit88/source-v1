# CAS Sourcing & Procurement Intelligence MVP

A first testable Streamlit prototype for CAS-number-based sourcing.

## What it does

- Inputs CAS number, desired quantity, unit, and required purity
- Validates CAS checksum
- Finds suppliers from a mock supplier dataset
- Normalizes visible catalog prices into $/g
- Estimates bulk pricing using conservative/base/aggressive quantity-scaling curves
- Ranks suppliers by CAS match, visible pricing, purity, region, and product URL availability
- Provides manual supplier search links
- Exports a supplier shortlist CSV

## How to run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Recommended Python

Use Python 3.12 for the first stable deployment.

## First test CAS

Use:

```text
103-90-2
```

This has mock visible pricing so the full workflow can be tested.

## Design rule

Visible catalog pricing is factual. Bulk pricing is an estimate. RFQ pricing is confirmed truth.
