---
name: bilingual-paper-annotator
description: Make an English–Chinese two-column paper reader with paragraph-level argument annotations, evidence and bibliography links, and optional three-pass reading questions with folded answers. Use for 论文双栏批注、双栏精读、中英对照论证分析、双栏三遍阅读自测. Delivers offline HTML, with optional PDF export and Zotero import support.
metadata:
  version: "1.3.0"
---

# Bilingual Paper Annotator

Create a reader for a supplied paper or the requested excerpt. Default output is one offline HTML file for the browser. It can also be imported into Zotero for reading and annotation. Generate PDF when requested, or both from the same reading data. Routine abstracts and literature screening do not need this workflow.

1. **Prepare the source.** Reuse supplied Markdown or a reviewed conversion that matches the source and scope. Otherwise, prepare local Markdown with `scripts/prepare_source.py` via MarkItDown. Use the original PDF or page-aware tools to verify paragraph order and physical page numbers. Follow [source preparation](references/source-preparation.md) for reuse, excerpt handling and targeted OCR or visual checks. Keep supplements, unavailable pages and uncertain extractions explicit.
2. **Build aligned blocks.** Follow [the input contract](references/input-format.md). Preserve source prose, qualifications, units, citation markers and order. Give each original paragraph an idiomatic Chinese translation, a source locator, exact highlight spans, and three distinct notes: paragraph function, role in the argument, and a technique or evidence gap. Track the paper's claim strength separately from the reader's assessment. Split only when the source has distinct paragraphs or a long block would be unreadable, and retain stable IDs.
3. **Ground the argument.** Include source crops of material figures, tables and uncertain display equations. Tie each cited visual to the relevant block. Map original citation markers to the verified bibliography entries using `citations`; keep unmatched markers as source text and disclose material gaps. Write a short chain from question through claim and evidence to rebuttal or evidence boundary and conclusion. State the author's claim, strongest support, and weakest link. When the paper omits a rebuttal or the data supporting a claim, record the gap instead of inventing one.
4. **Render and verify.** Run the selected command below. Inspect readable text and layout at the intended width. Check that figure and bibliography links land on the right entries and return to their paragraphs. The HTML uses ordinary fragment links and visible figures because the Zotero snapshot reader disables page JavaScript. For PDF, reopen and render representative pages, verify text selection and any split paragraphs.
5. **Deliver.** Provide the requested format and disclose source gaps. For Zotero use, follow [the attachment guide](references/zotero.md). Preserve an already annotated snapshot as a versioned attachment. Writing to a Zotero library needs authorization for that action.

When the user asks for the three-pass worksheet or contextual self-test, follow [the three-pass questions](references/three-pass.md). Use the optional HTML input field `study` to place prompts beside relevant passages and keep reference answers folded. A first-pass-only request uses Q1–6. PDF continues to provide the fixed-layout reading edition.

```text
python <skill-dir>/scripts/prepare_source.py paper.pdf -o work/paper-source.md
python <skill-dir>/scripts/render_html.py reader.json paper-reader.html
python <skill-dir>/scripts/render_pdf.py reader.json paper-reader.pdf [--zh-font path/to/CJK.ttf] [--en-font path/to/serif.ttf]
```

HTML rendering uses Python 3.10+ and the standard library. PDF additionally uses ReportLab and an embeddable CJK TrueType font. See [the PDF guide](references/pdf.md) when exporting PDF. Both renderers leave a pre-existing output file intact.
