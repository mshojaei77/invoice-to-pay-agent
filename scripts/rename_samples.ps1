Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$samplesRoot = Join-Path $repoRoot "samples"

$renames = [ordered]@{
    "2403-Return-Delivery-Note.pdf" = "delivery_note_004_return_2403.pdf"
    "AWSEurope_Mocks_Website_VATinvoice.pdf" = "invoice_007_aws_europe_vat.pdf"
    "Bank-Statement-Example.pdf" = "bank_statement_001_example.pdf"
    "CMR-KDE-Transport-GmbH-Rodgau.pdf" = "delivery_note_005_cmr_kde_transport.pdf"
    "Delivery-Note-Receipt-PDF-Download.pdf" = "delivery_note_001_bunker_receipt.pdf"
    "Delivery-Note-Template-2.pdf" = "delivery_note_002_template.pdf"
    "EN_Delivery_Note.pdf" = "delivery_note_003_en_sample.pdf"
    "FOI-25-26-020-Document-21.pdf" = "reference_doc_005_foi_25_26_020_document_21.pdf"
    "FOI-25-26-020-Document-4.pdf" = "reference_doc_004_foi_25_26_020_document_4.pdf"
    "Understanding+Your+Utility+Bill+-+English.pdf" = "utility_bill_001_english.pdf"
    "XHVYHRSKXHMKBI9WW2CQ_eSupplierTrng-ViewPOs_R3.pdf" = "purchase_order_005_esupplier_training.pdf"
    "cfpb_building_block_activities_sample-credit-card-statement_handout.pdf" = "card_statement_001_cfpb_sample.pdf"
    "chinese-invoice.pdf" = "invoice_006_chinese.pdf"
    "demo-credit-note-1.pdf" = "credit_note_001_demo.pdf"
    "demo-credit-note-2.pdf" = "credit_note_002_demo.pdf"
    "demo-credit-note-3.pdf" = "credit_note_003_demo.pdf"
    "demo-invoice-20tax-1.pdf" = "invoice_020_demo_20tax_001.pdf"
    "demo-invoice-20tax-10.pdf" = "invoice_020_demo_20tax_010.pdf"
    "demo-invoice-20tax-2.pdf" = "invoice_020_demo_20tax_002.pdf"
    "demo-invoice-20tax-3.pdf" = "invoice_020_demo_20tax_003.pdf"
    "demo-invoice-20tax-4.pdf" = "invoice_020_demo_20tax_004.pdf"
    "demo-invoice-20tax-5.pdf" = "invoice_020_demo_20tax_005.pdf"
    "demo-invoice-20tax-6.pdf" = "invoice_020_demo_20tax_006.pdf"
    "demo-invoice-20tax-7.pdf" = "invoice_020_demo_20tax_007.pdf"
    "demo-invoice-20tax-8.pdf" = "invoice_020_demo_20tax_008.pdf"
    "demo-invoice-20tax-9.pdf" = "invoice_020_demo_20tax_009.pdf"
    "demo-invoice-no-tax-1.pdf" = "invoice_030_demo_no_tax_001.pdf"
    "demo-invoice-no-tax-10.pdf" = "invoice_030_demo_no_tax_010.pdf"
    "demo-invoice-no-tax-2.pdf" = "invoice_030_demo_no_tax_002.pdf"
    "demo-invoice-no-tax-3.pdf" = "invoice_030_demo_no_tax_003.pdf"
    "demo-invoice-no-tax-4.pdf" = "invoice_030_demo_no_tax_004.pdf"
    "demo-invoice-no-tax-5.pdf" = "invoice_030_demo_no_tax_005.pdf"
    "demo-invoice-no-tax-6.pdf" = "invoice_030_demo_no_tax_006.pdf"
    "demo-invoice-no-tax-7.pdf" = "invoice_030_demo_no_tax_007.pdf"
    "demo-invoice-no-tax-8.pdf" = "invoice_030_demo_no_tax_008.pdf"
    "demo-invoice-no-tax-9.pdf" = "invoice_030_demo_no_tax_009.pdf"
    "demo-invoice-swiss-qr.pdf" = "invoice_005_swiss_qr.pdf"
    "demo-remittance-advice-1.pdf" = "remittance_advice_001_demo.pdf"
    "demo-remittance-advice-2.pdf" = "remittance_advice_002_demo.pdf"
    "demo-remittance-advice-3.pdf" = "remittance_advice_003_demo.pdf"
    "demo-remittance-advice-4.pdf" = "remittance_advice_004_demo.pdf"
    "dfat-foi-lex11688.pdf" = "reference_doc_001_dfat_foi_lex11688.pdf"
    "dfat-foi-lex11918.pdf" = "reference_doc_002_dfat_foi_lex11918.pdf"
    "doc.pdf" = "reference_doc_003_general.pdf"
    "example-invoice-priparcel (1).pdf" = "invoice_010_priparcel_duplicate.pdf"
    "example-invoice-priparcel.pdf" = "invoice_009_priparcel.pdf"
    "fedex-wht-invoice-en-th.pdf" = "invoice_008_fedex_wht_en_th.pdf"
    "foi-24-25-049-documents-16-30.pdf" = "reference_doc_006_foi_24_25_049_documents_16_30.pdf"
    "foi-25-26-021-documents-01-to-30_0.pdf" = "reference_doc_007_foi_25_26_021_documents_01_30.pdf"
    "handwritten-invoice-20tax.pdf" = "invoice_003_handwritten_20tax.pdf"
    "handwritten-invoice-no-tax.pdf" = "invoice_004_handwritten_no_tax.pdf"
    "purchase-order-1.pdf" = "purchase_order_001_polychemtex.pdf"
    "purchase-order-2.pdf" = "purchase_order_002_sample.pdf"
    "purchase-order-3.pdf" = "purchase_order_003_sample.pdf"
    "purchase-order-4.pdf" = "purchase_order_004_sample.pdf"
    "rp-return-form-emergency-and-safety-luminaires.pdf" = "return_form_001_emergency_luminaires.pdf"
    "sample-pdf-invoice.pdf" = "invoice_001_canada_post_sample.pdf"
    "sample-tax-invoice.pdf" = "invoice_002_tax_sample_local_supply.pdf"
    "tarievenfolder-en-15_tcm10-214766.pdf" = "rate_card_001_tarievenfolder_en.pdf"
    "wordpress-pdf-invoice-plugin-sample (1).pdf" = "invoice_012_wordpress_plugin_duplicate.pdf"
    "wordpress-pdf-invoice-plugin-sample.pdf" = "invoice_011_wordpress_plugin.pdf"
}

$newNames = @{}
foreach ($entry in $renames.GetEnumerator()) {
    if ($newNames.ContainsKey($entry.Value)) {
        throw "Duplicate target filename: $($entry.Value)"
    }
    $newNames[$entry.Value] = $true
}

foreach ($entry in $renames.GetEnumerator()) {
    $oldPath = Join-Path $samplesRoot $entry.Key
    $newPath = Join-Path $samplesRoot $entry.Value
    if (-not (Test-Path -LiteralPath $oldPath)) {
        Write-Host "skip missing: $($entry.Key)"
        continue
    }
    if (Test-Path -LiteralPath $newPath) {
        throw "Target already exists: $newPath"
    }
    git -C $repoRoot mv -- "samples/$($entry.Key)" "samples/$($entry.Value)"
}

$textFiles = @(
    Join-Path $repoRoot "README.md"
    Join-Path $repoRoot "samples/eval_manifest.jsonl"
) + (Get-ChildItem -Path (Join-Path $repoRoot "tests") -Recurse -File -Include "*.py").FullName

foreach ($file in $textFiles) {
    $content = Get-Content -LiteralPath $file -Raw -Encoding UTF8
    $updated = $content
    foreach ($entry in $renames.GetEnumerator()) {
        $updated = $updated.Replace($entry.Key, $entry.Value)
    }
    if ($updated -ne $content) {
        [System.IO.File]::WriteAllText($file, $updated, [System.Text.UTF8Encoding]::new($false))
    }
}

Write-Host "Renamed $($renames.Count) sample PDFs and updated references."
