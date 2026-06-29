from __future__ import annotations


CAPTURE_CHANNELS = {
    "email": ("email", "inbox", "imap", "gmail", "outlook"),
    "supplier_portal": ("portal", "supplier_portal", "vendor_portal"),
    "edi": ("edi", "xml", "cxml", "peppol"),
    "physical_mail": ("physical_mail", "postal_mail", "scan", "scanned", "paper"),
    "manual_upload": ("upload", "pdf", "xlsx", "excel"),
}


def build_invoice_capture_plan(uploaded_documents: list[dict], parser_route: list[dict], parser_warnings: list[dict]) -> dict:
    evidence = " ".join(
        f"{document.get('filename', '')} {document.get('path', '')}".lower()
        for document in uploaded_documents
    )
    detected_channels = [
        channel
        for channel, tokens in CAPTURE_CHANNELS.items()
        if any(token in evidence for token in tokens)
    ]
    if not detected_channels:
        detected_channels = ["manual_upload"]

    connected_channels = [
        {
            "channel": channel,
            "status": "connected" if channel == "manual_upload" else "connector_planned",
            "agent": f"{channel}_capture_agent",
        }
        for channel in detected_channels
    ]

    return {
        "capture_status": "ready" if not parser_warnings else "review_parser_warnings",
        "detected_channels": detected_channels,
        "connected_channels": connected_channels,
        "coverage": {
            "email": "planned",
            "supplier_portals": "planned",
            "edi": "planned",
            "physical_mail": "planned",
            "manual_upload": "ready",
        },
        "parser_route": parser_route,
        "warnings_count": len(parser_warnings),
    }
