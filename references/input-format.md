# Shared reading data

Use UTF-8 JSON. Keep the data and evidence crops in the task workspace. The renderers lay out prose and preserve anchors. Source recovery, translation, and scientific judgment happen before rendering.

| Key | Shape |
| --- | --- |
| `title`, `title_zh` | English source title and Chinese title, both strings |
| `citation` | Authors, venue and year as a string |
| `course`, `source_url` | Optional course or project name and verified HTTPS/HTTP DOI or publisher link |
| `scope` | Verified scope and any important coverage gaps, as a string |
| `sections` | Ordered list of objects with `id`, `title`, `blocks` |
| `evidence` | Optional list of image assets with `id`, `title`, `file`, `source`, `caption_en`, `caption_zh`, `after`, and optional `annotation` |
| `summary` | Object with `chain`, `claim`, `strongest`, `weakest`. Each chain item contains `label`, `text` and optional `target` |
| `references` | Optional list of source bibliography entries. Use objects with `id` and `text` for linkable entries. Plain strings are supported for text-only entries. |
| `study` | Optional list of three-pass prompts for the HTML renderer. Each has `number` (unique 1–16), `at` (block ID), `question`, `answer`, and optionally `sources` (list of objects with `target` and `label`) |

Each block needs `id`, `source`, `en`, `zh`, and `annotation`. Write new annotations as a plain Chinese string, with blank lines between paragraphs. The older object with `function`, `role`, and `critique` also renders. Optional block keys are `heading`, `marks`, `evidence`, and `citations`. The `evidence` list contains the IDs of assets cited by the block. The image's `after` is the block ID where it appears in HTML and the destination of its return link in either format. If that block has no explicit link to the asset, the renderer adds one. The PDF groups evidence after the argument overview and links to it from the text.

For an image or table, use the asset's optional `annotation` string for the reader's interpretation. It appears separately from `caption_en` and `caption_zh`. Use blank lines to separate paragraphs in the interpretation. See [the annotation guide](annotations.md) for attribution and examples.

- IDs must be unique across sections, paragraphs and assets, and use ASCII letters, digits, hyphens or underscores. Start with a letter. Keep IDs stable when revising. `reader-content`, `argument-summary`, `reader-references` and `reader-evidence` are reserved.
- Put real PDF physical page labels in `source` (for example `PDF p. 5–6`), or a verified heading or paragraph label when pagination is unavailable. Do not transpose journal numbering into file page numbering.
- A mark is `{"kind":"data","text":"12 independent samples"}`. Valid kinds are `thesis` (yellow), `term` (red), `data` (blue), `limit` (green), and `method` (purple). Text must be an exact substring of `en`. The first occurrence is marked unless a one-based `occurrence` is set. Marks cannot overlap. Chinese text stays unmarked.
- Use a block's optional `citations` list to link exact spans in `en` to the bibliography, for example `{"text":"Chen et al., 2025","target":"ref-chen-2025"}` or `{"text":"[12]","target":"ref-12"}`. Each item can use a one-based `occurrence`. Citation spans cannot overlap each other, but can overlap highlight marks. Both renderers keep the original citation text and add one return link per citing paragraph to each matched reference.
- Keep the bibliography in the source order. Reference IDs use the same rules as section, block and evidence IDs. Include a printed number in the entry's `text` when it is part of the source label. For grouped citations such as `[2, 5]` or `(Chen, 2025; Wang, 2020)`, map each visible citation separately. For a range such as `[2–5]`, map the two visible endpoints and keep intermediate entries in the bibliography. Verify the match using the original numbering or author and year, including suffixes such as 2025a. When the match is uncertain or the reference section is missing, preserve the marker as plain text.
- All prose inputs are plain text. Use Unicode notation for inline symbols that extract correctly. For complex or uncertain equation notation, add a crop with a source label and a Chinese explanation. PNG and JPEG evidence paths are relative to the JSON directory and may not point outside it.
- Use top-level sections for navigation. Group detailed paper subsections with a block's optional `heading`.
- Mark the approach as excerpted or incomplete where applicable. Do not present missing supplementary data as reviewed. Keep the original article and generated translation private unless redistribution is permitted.
- For `study`, the question number determines the pass (1–6, 7–13 or 14–16). Place each prompt at a block the reader can use to answer it. Supporting source links can target a section, block, evidence or bibliography ID. `study-guide` and `study-q1` through `study-q16` are reserved when this field is used. Use newlines within long answers when they improve readability. See [the question list](three-pass.md).

See [the self-contained example](../examples/reader.json) for valid input.
