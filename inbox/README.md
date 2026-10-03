# Inbox: documents collected by hand

Some sources cannot be crawled: a robots.txt ban, a host that refuses an automated client, a portal with no
machine-readable list. Each economy has a short list of them, and each source has its own folder here.
Files from anywhere else are not taken.

```
inbox/
  CN/                               China
    npc-database/                   the national database: its exports go here
    miit/                           MIIT pages and attachments
      2026-10-03_101522/            one drop on the page = one dated batch
        catalogue.pdf
        provenance.tsv              the address each file came from
    customs/
  SG/
    pdpc-gov-sg/
    ...
```

**How to add files.** Open **1 Scraping → 1.3 Hand-collected**, choose the economy, choose the source, drop
the files. They appear in **2 Extraction → Input** at once, as the source (every batch) and as each batch.
The interface creates the folders when it starts.

**Where the sources come from.** Nothing is listed here by hand. An economy's sources are the rows of its
watchlist (`stages/p1-scrape/.../<adapter>/watchlist.tsv`); China's are the publishers its tools mark "by
hand". A folder is named from the source's address (`pdpc.gov.sg` → `pdpc-gov-sg`), so it is the same on
every machine.

**What can be read.** The page judges each file from what it is, not from its name, and says so at the drop:

| File | Read as |
| :-- | :-- |
| PDF | its text layer, or OCR when it has none |
| Word `.docx` (also when named `.doc`) | Word |
| A web page saved from a portal the reader has a parser for | that parser |
| Old Word `.doc` | not read: open it and Save As `.docx` |
| A web page from another site | not read: print the page to PDF and drop the PDF |
| `.zip` | unpacked on arrival; its PDF, HTML and Word files are taken |

Files that cannot be read stay in the folder, are left out of the run, and are listed in `left_out.csv`
beside the manifest.

**Addresses.** A saved web page brings its own address. For anything else, paste the document's address in
the file list. A file with none is cited to its source's page, and its manifest row says so. Addresses are
kept in `provenance.tsv` beside the files; that sheet is the only thing the interface writes here.

**Language.** The folder names the economy and the language follows from the stage's economy table (Chinese
for CN, Lao for LA, Portuguese for TL, English for the others). Before a run, **Check** reads the text it
can and warns when a file does not fit its folder.

**What a run writes.** The manifest and the law table go under
`outputs/scrape/<economy>/<source>/hand_<batch>_<time>/`, beside that source's crawl results.

**Older files.** Files and dated batches sitting directly in `inbox/<economy>` (the layout before sources
had folders) are still listed and still go to Extraction. Move them into a source's folder to file them.

Everything in this folder except this README stays out of git. The location is a setting,
`RDTII_INBOX_DIR`, default `inbox`.
