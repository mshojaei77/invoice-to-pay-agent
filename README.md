# Invoice-to-Pay Agent

## Project Goal
Build a lightweight AI agent that takes invoices, receipts, purchase orders, and delivery notes, then extracts fields, validates them, detects mismatches, routes approvals, and prepares ERP-ready output.

## MVP Features

| Feature | Description |
|---------|-------------|
| Document Upload | Accept invoice PDF/image + PO PDF |
| OCR/VLM Extraction | Extract to strict JSON with Pydantic schemas |
| Field Extraction | Vendor, IBAN, VAT, total, line-items, due-date |
| 2-way / 3-way Match | Simulate matching invoice vs PO vs delivery note |
| Duplicate Detection | Flag duplicate invoices before processing |
| Approval Queue | Human-in-the-loop approval workflow |
| ERP Mock Endpoint | "Post to ERP" simulation |
| Evaluation Report | Extraction accuracy, mismatch detection, hallucination rate |
| Audit Log | Every agent step logged with traceability |

## Stack
Python, FastAPI, Pydantic, PostgreSQL, MinIO, PySpark, MLflow, Docker Compose, GitHub Actions, LangGraph, OpenTelemetry/Langfuse, Ragas/DeepEval, Streamlit/Next.js dashboard

## Cloud Mapping
| Local | Cloud Target |
|-------|-------------|
| MinIO | Azure Data Lake / GCS |
| PySpark local | Databricks / Spark cluster |
| PostgreSQL | Azure PostgreSQL / Cloud SQL |
| FastAPI | Azure Container Apps / GKE |
| MLflow local | Databricks MLflow |


## Real product idea

A lightweight AI agent that takes invoices, receipts, purchase orders, and delivery notes, then extracts fields, validates them, detects mismatches, routes approvals, and prepares ERP-ready output.

## Why people would pay

This is one of the clearest market-demand areas. YC-backed Finto describes end-to-end invoice-to-pay automation: document classification, invoice reading, vendor/tax/bank checks, cost-center coding, three-way matching, approval chasing, and ERP posting. ([Y Combinator][2]) Reddit accounting/small-business threads also show that the pain is not only OCR; people complain about PO matching, approvals, duplicate checks, accounting entry, reconciliation, and copy-paste work across tools. ([Reddit][3])

## Why an investor would care

This sells to finance teams with existing budget. It replaces manual AP labor, reduces payment mistakes, creates audit trails, and can expand into procurement, vendor risk, compliance, and ERP integrations. YC’s own RFS says services spend is much larger than software spend and highlights accounting, tax, audit, compliance, and healthcare administration as areas where AI-native products can replace outsourced service work. ([Y Combinator][1])

## One-week prototype

Build a demo called:

```text
invoice-to-pay-agent
```

MVP features:

* Upload invoice PDF/image + PO PDF.
* OCR or VLM extraction into strict JSON.
* Vendor, IBAN, VAT, total, line-item, due-date extraction.
* 2-way or 3-way match simulation.
* Duplicate invoice detection.
* Human approval queue.
* “Post to ERP” mock endpoint.
* Evaluation report: extraction accuracy, mismatch detection, hallucination rate.
* Audit log with every agent step.

## Best stack

Use **Python, FastAPI, Pydantic, PostgreSQL, MinIO, PySpark, MLflow, Docker Compose, GitHub Actions, LangGraph, OpenTelemetry/Langfuse, Ragas or DeepEval, Streamlit/Next.js dashboard**.

For the cloud-readiness layer, document the mapping:

```text
Local MinIO      -> Azure Data Lake / GCS
PySpark local    -> Databricks / Spark cluster
Postgres         -> Azure PostgreSQL / Cloud SQL
FastAPI          -> Azure Container Apps / GKE
MLflow local     -> Databricks MLflow
```

## Which NL gaps it fills

This project covers KPN-style internal HR/Finance AI agents, automated invoice scanning, approval workflows, Azure, Docker, API integrations, and CI/CD. ([dutchstartup.ai][4]) It also maps to Stedin/enterprise MLOps requirements: Azure, Databricks, Airflow, Spark, Kubernetes. ([Stedin Careers][5])