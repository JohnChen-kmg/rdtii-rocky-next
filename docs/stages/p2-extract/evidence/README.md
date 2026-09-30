# evidence/

Proof that the extraction claims are measured rather than asserted. This task must produce
four things and each one is consumed by a named rubric criterion or submission field.

| Evidence | Consumed by |
| :---- | :---- |
| A gold-page character error rate report per script, copied from `stages\p2-extract\fixtures\ocr_reference\<doc_id>\cer_report.json`, with the page image and the hand-keyed transcription it was measured against | C1c, linguistic versatility, ten marks. Also the accuracy claim in section 2 of the Word template |
| The before and after OCR of one Lao page, English pack against the Lao pack, same page, same preprocessing | C1c, and the pitch. It is the single clearest picture of what the language work bought |
| A grounding re-verification run over the full corpus, showing the record count and zero offset mismatches, from `p2-extract validate` | C2b, citation fidelity, ten marks |
| The `tessdata` licence check: the release URL, the commit hash and the LICENSE file of every language pack committed to the repo | C4a, technical handover and open-source compliance. The host forbids shipping licensed text |

Keep the raw output, not a retyped summary. A judge or the secretariat may ask to see the file
the number came from. Where a figure here and a figure in the submission disagree, the
submission is wrong until this folder is re-run. No figure from this folder enters the
submission until it also agrees with
`C:\Users\woshi\Desktop\RDTII Finale Plan\3_Final_Stage\AUTHORITATIVE_NUMBERS.md`, or that file
is updated in the same sitting.
