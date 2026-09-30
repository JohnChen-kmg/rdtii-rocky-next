"""RDTII Project 1 — Web Scraping / Retrieval.

Crawls live SG/AU/MY government legal portals (Pillars 6 & 7), retrieves raw
bytes (HTML, native PDF, scanned PDF) with full HTTP provenance, and emits
Hand-off #1 (handoff1/ = manifest.csv + manifest.jsonl + raw/** + crawl_log.jsonl
+ cost_report.json). No OCR, cleaning, tagging, or mapping — those are P2/P3.
"""

__version__ = "0.1.0"
