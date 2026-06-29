# Invoice-to-Pay Demo Report

This is the short, shareable version of what the project demonstrates. It is written for AP managers, controllers, ERP consultants, and hiring reviewers who need to understand the workflow before reading the code.

## Clean Invoice Scenario

| Control | Result |
| --- | --- |
| Invoice status | Ready to post |
| Risk | Low |
| PO match | Passed |
| Delivery match | Passed |
| Duplicate check | Clear |
| Fraud controls | Clear |
| Approval route | Auto-post |
| Payment status | Scheduled |
| ERP action | Mock posted |
| Audit trail | Available |

## Exception Scenario

| Control | Result |
| --- | --- |
| Invoice status | Blocked |
| Reason | Missing PO + missing delivery evidence |
| Next reviewer | AP manager or buyer/receiving owner |
| Payment status | Hold |
| ERP action | Not posted |
| Audit trail | Exception reason, approval requirement, and decision state recorded |

## What This Shows

- The agent is not only extracting invoice fields.
- Matching, risk, approval, payment readiness, ERP handoff, and auditability are modeled as explicit graph stages.
- Human review is required when controls are missing or risk is not recoverable.
- ERP posting is mocked on purpose; this repo demonstrates the control contract before money movement or certified ERP integration.

## Reproduce Locally

```bash
uv run python scripts/run_demo.py \
  --invoice samples/invoice_001_canada_post_sample.pdf \
  --po samples/purchase_order_001_polychemtex.pdf \
  --delivery-note samples/delivery_note_003_en_sample.pdf \
  --output-md data/processed/reports/latest-demo.md
```

The generated markdown report includes parser route, parsed documents, risk reasons, exception queue, fraud controls, approval route, GL coding, compliance controls, payment plan, ERP sync plan, KPI snapshot, and audit pointers.
