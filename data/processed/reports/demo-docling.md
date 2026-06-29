# Invoice-to-Pay Demo Run

## Summary

- Run ID: `7a96c18a-7152-4253-9adf-78d104064bab`
- Final status: `completed`
- Risk level: `low`
- ERP status: `posted`
- Audit log: `data/processed/audit.jsonl`

## Parser Route

- Parser: `docling`; reason: `cli_selected`

## Parsed Documents

### Document 1: invoice

- Parser: `docling`
- Pages: `2`
- Confidence: `0.85`
- Raw artifact: `data\processed\parser_raw\docling-20bf9e46-2750-44f2-b0be-e28751aff1c4.json`

#### Preview

<!-- image --> Page 1 / 2 Invoice date (Y-M-D) Customer number Invoice number Customer ref. 1 Customer ref. 2 90000001620 2025-06-21 1234567 ## Contact us | Your payment is due by (Y-M-D) | 2025-07-06 | | | | | |----------------------------------|--------------|-----|-------------|---------|--------

### Document 2: purchase_order

- Parser: `docling`
- Pages: `1`
- Confidence: `0.85`
- Raw artifact: `data\processed\parser_raw\docling-c87c9efe-bb86-4430-abb2-fcc755282c0d.json`

#### Preview

Polychemtex Inc. 1 Main Street Townsville DH9 OTB Phone 496 0123 ## VENDOR Phone 496 0123 ## PURCHASE ORDER PURCHASE ORDER NO 576759 VENDOR NUMBER 730001 CHANGE ORDER PRINTED ON 6/14/2026 | | SHIP TO | BILL TO | |------------------|-------------|-------------| | Polychemtex Inc. | ACME Inc | ACME In

### Document 3: delivery_note

- Parser: `docling`
- Pages: `1`
- Confidence: `0.85`
- Raw artifact: `data\processed\parser_raw\docling-98c0f295-d99b-417b-aab6-38275f94be7e.json`

#### Preview

© 2006 <!-- image --> ## IBIA Standard Bunker Delivery Note / Receipt ## Product Details Date Port Grade/ISO Designation Nomination No. Company Name Density @ 15°C (kg/m³) Supplier Details Vessel Name Calculated from Components Company Name IMO Number Shore Tank measurement Address 1 Flag Bunker Tan

## Risk Reasons

No risk reasons were recorded.
