# Optional PDF output

Use PDF when the reader prefers fixed page layout, printer-friendly output, or the PDF annotation workflow. Use the same verified JSON file and source crops as the HTML. PDF uses horizontal A4, selectable English and Chinese, section bookmarks, highlight colors, links to evidence and links back to the text.

```text
python -m pip install reportlab
python scripts/render_pdf.py examples/reader.json reading.pdf --zh-font path/to/CJK.ttf
```

The PDF script tries common Windows, macOS and Linux TrueType font locations. If an appropriate font is elsewhere, pass `--zh-font` with an embeddable CJK TrueType file and optionally `--en-font` with a serif TrueType file. No fonts are downloaded at runtime. CJK system fonts stay on the machine where they are installed. If a symbol is absent in the selected font, use a suitable font or a verified equation crop.

When an original paragraph has to continue onto a new page, the new page carries its block ID and a link back to the aligned note. Check that all text is selectable, no note is clipped, and page breaks do not obscure the block identity. Add the PDF to Zotero as a separate child attachment if desired.
