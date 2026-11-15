# Prepare the source for close reading

Run `scripts/prepare_source.py` with a Python environment that already has Microsoft MarkItDown. For a fresh environment, install only the extras needed for the source format. PDF and DOCX use the corresponding extras. See the [official MarkItDown documentation](https://github.com/microsoft/markitdown).

```text
python -m pip install "markitdown[pdf]"
python scripts/prepare_source.py "paper.pdf" -o "work/paper-source.md"
```

- **Reuse first.** Start from a supplied Markdown source or an already reviewed conversion when its source and scope match. For a long paper you expect to reopen, add `--reuse` on the first run and later runs. That mode keeps a task-local `.meta.json` beside the Markdown and verifies the source file, converter environment and result before reusing it. Use a new output filename for a revised source or edited Markdown. A one-off run skips the cache checks.
- **Keep the reading scope.** For a page-limited request, use an existing page-level extraction or convert a temporary PDF containing only the requested pages. Retain a mapping to physical pages in the original. Markdown supports navigation and search. Read only the passages needed and use the original PDF or a page-aware extraction for source locators, column order and paragraph boundaries.
- **Check the content.** Compare the relevant passages, citations, units and captions with the original. Render the pages needed to confirm important graphs, formulas, missing text or uncertain reading order. For scan-only or mixed PDFs, use available local OCR or visual reading on the affected pages. Keep source gaps explicit. A successful conversion confirms basic text availability, and a cache hit confirms file identity.
- **Keep work local.** The helper runs local text extraction through the official CLI. Exit status 2 means the source needs review. An empty or marker-only extraction leaves the output path available. An extraction with Unicode replacement characters is kept for comparison with the source. If the dependency is unavailable, use an existing MarkItDown installation, a verified page-aware extraction or supplied Markdown and continue the close reading.

Keep the extracted Markdown, original pages and verified notes separate. Follow the [reading data contract](input-format.md) after preparing the source.
