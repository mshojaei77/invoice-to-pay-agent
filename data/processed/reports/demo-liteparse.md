# Invoice-to-Pay Demo Run

## Summary

- Run ID: `75491fec-94bf-4521-bc6d-01d539cd0275`
- Final status: `completed`
- Risk level: `low`
- ERP status: `posted`
- Audit log: `data/processed/audit.jsonl`

## Parser Route

- Parser: `liteparse`; reason: `cli_selected`

## Parsed Documents

### Document 1: invoice

- Parser: `liteparse`
- Pages: `2`
- Confidence: `0.8`
- Raw artifact: `data\processed\parser_raw\liteparse-4aeb708d-015c-40d8-8f08-c348cdfb6109.json`

#### Preview

CANADA POSTES Page 1 / 2 Invoice date (Y-M-D) 2025-06-21 Customer number 1234567 Sample invoice Invoice number 90000001620 Customer ref. 1 Customer ref. 2 Contact us CLIENT1, CLIENT2 General inquiries | Tracking SAMPLE BUSINESS NM 1-866-607-6301 ADDRESS LINE1 Questions about your invoice / account B

### Document 2: purchase_order

- Parser: `liteparse`
- Pages: `1`
- Confidence: `0.8`
- Raw artifact: `data\processed\parser_raw\liteparse-96abd00f-795c-4931-a5ab-08ef8cabafb2.json`

#### Preview

Polychemtex Inc. PURCHASE ORDER 1 Main Street Townsville DH9 OTB PURCHASE ORDER NO 576759 Phone 496 0123 VENDOR NUMBER 730001 CHANGE ORDER PRINTED ON 6/14/2026 VENDOR SHIP TO BILL TO Polychemtex Inc. ACME Inc ACME Inc 1 Main Street 44 Shore St 44 Shore St Townsville Macduff Macduff DH9 OTB AB4 1TX A

### Document 3: delivery_note

- Parser: `liteparse`
- Pages: `1`
- Confidence: `0.8`
- Raw artifact: `data\processed\parser_raw\liteparse-ff38b5e8-d395-48ae-9842-6a2a75c250b9.json`

#### Preview

© 2006 IBIA Standard Bunker Delivery Note / Receipt Product Details Date Port | Grade/ISO Designation Nomination No. | | Company Name Density @ 15°C (kg/m³) Supplier Details Vessel Name Calculated from Components YES / NO Company Name IMO Number Shore Tank measurement YES / NO Address 1 Flag Bunker 

## Risk Reasons

No risk reasons were recorded.
