# Inbox: documents collected by hand

Put a document you fetched yourself in the subfolder of its economy, by hand or through the interface's
**1 Scraping → 1.3 Hand-collected** block (choose the economy, drop the files), and it appears in the
**2 Extraction → Input** list at once. The interface creates one subfolder per economy built so far when it
starts, and the block offers those six:

```
inbox/
  AU/   Australia
  CN/   China          the national database forbids automated tools; its exports and attachments go here
  LA/   Lao PDR
  MY/   Malaysia
  SG/   Singapore
  TL/   Timor-Leste
```

- Each drop on the page lands in a dated batch subfolder, `inbox/CN/2026-09-30_101522/`. Extraction lists the
  economy folder (every batch) and each batch on its own, so one drop can be extracted by itself. A file you
  copy straight into `inbox/CN` belongs to no batch and is read with the whole economy.
- Formats: PDF (native or scanned), HTML, Word (.docx). Keep the file names you downloaded; the interface
  builds document ids from them.
- The folder names the economy, and the language follows from the stage's economy table (Chinese for CN,
  Lao for LA, Portuguese for TL, English for the others). Nothing to choose on the page.
- Before a run, **Check** reads the text of the files it can read and warns when a file's language does not
  fit its folder, for example a Lao text inside CN. Scanned PDFs cannot be checked before OCR.
- The interface writes the manifest and the law table for these files under `outputs/scrape/hand_*`; it
  never writes into this folder. Source addresses are blank unless typed on the page.
- One run can extract the whole inbox: choose the entry "inbox, every economy". The stage reads one pass per
  language.

Everything in this folder except this README stays out of git. The location is a setting,
`RDTII_INBOX_DIR`, default `inbox`.
