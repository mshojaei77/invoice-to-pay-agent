# Security Policy

## Supported Versions

This repository is a prototype. Security fixes are accepted for the latest `main` branch and tagged releases.

## Reporting a Vulnerability

Please do not open public issues for vulnerabilities involving financial documents, parser artifacts, uploaded files, payment details, credentials, or audit logs.

Report privately by emailing the maintainer listed in `pyproject.toml` with:

- a short description of the issue,
- affected files or routes,
- reproduction steps,
- impact assessment,
- any suggested fix.

## Sensitive Data Rules

- Do not commit real invoices, bank data, tax identifiers, ERP credentials, customer files, or vendor master data.
- Treat files under `data/processed/` as sensitive when running with real documents.
- Keep future API keys, ERP credentials, object-storage secrets, and database URLs in environment variables.
- Scrub generated reports before sharing them publicly.
