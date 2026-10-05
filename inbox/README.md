# Inbox: documents collected by hand

Some sources cannot be crawled: a robots.txt ban, a host that refuses an automated client, a portal with no
machine-readable list. Files fetched from them by hand go here, one folder per economy, one dated subfolder
per drop. No source is asked for: how a file is read follows from what it is and from the economy's
language, not from which office published it.

```
inbox/
  CN/                               China
    Hand_collected/                 every file fetched by hand for China
      2026-10-05_101522/            one drop on the page = one dated batch
        catalogue.pdf
        provenance.tsv              the address each file came from
  SG/
    Hand_collected/
      ...
```

**How to add files.** Open **1 Scraping → 1.3 Hand-collected**, choose the economy, drop the files. They
appear in **2 Extraction → Input** at once, as the folder (every batch) and as each batch. The interface
creates the folders when it starts.

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

**Addresses.** A saved web page is the one kind of file whose reading depends on where it came from: it is
read by the parser of its portal, so it needs its address. A saved page usually brings its own; otherwise
type it in the file list. For anything else, paste the document's address so the output can cite it; a file
with none has no address in the output. Addresses are kept in `provenance.tsv` beside the files; that sheet
is the only thing the interface writes here.

**Language.** The folder names the economy and the language follows from the stage's economy table (Chinese
for CN, Lao for LA, Portuguese for TL, English for the others). Before a run, **Check** reads the text it
can and warns when a file does not fit its folder.

**What a run writes.** The manifest and the law table go under
`outputs/scrape/<economy>/Hand_collected/hand_<batch>_<time>/`, beside that economy's crawl results.

**Older files.** Before 5 October 2026 each designated source had a folder of its own
(`inbox/CN/miit`, `inbox/SG/pdpc-gov-sg`), and before that files sat directly in `inbox/<economy>`. Files in
either place are still listed and still go to Extraction. An empty folder of that kind can be deleted.

Everything in this folder except this README stays out of git. The location is a setting,
`RDTII_INBOX_DIR`, default `inbox`.
