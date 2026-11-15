# 论文双栏批注 · Bilingual Paper Annotator

左栏逐段对照英文原文和中文译文，论点、术语、数据、让步和方法用五色标出；右栏拆解这段在论证里起什么作用、证据能支持到哪一步。读到关键结论，可以跳到原图核对，再返回正文。

默认生成可离线打开的单文件 HTML，也可导出 PDF。

**支持导入 Zotero 阅读。**

## 在 Codex 使用

把整个 `bilingual-paper-annotator` 目录放进 Codex 的用户 skills 目录（通常是 `~/.codex/skills/`），然后提供有权处理的论文文件，并在 Codex 中输入：

> 用 `$bilingual-paper-annotator` 精读这篇论文，保留逐段中英对照、五色高亮和图文跳转。输出 HTML，再导出一份 PDF。

想先自己想一遍，可以加一句「启用三遍阅读自测」。题目跟着相关段落走，AI 参考答案默认折叠。第一次可以只做前 6 题。详见 [三遍阅读题库](references/three-pass.md)。

只说“双栏精读”也可以自动匹配，是否自动选择由宿主决定。翻译和批注由 agent 根据原文完成。本项目脚本从已对齐的阅读数据生成版面。

## 不用 agent 试跑样例

需要 Python 3.10 或更高版本。从项目根目录执行：

```text
python scripts/render_html.py examples/reader.json demo.html
python -m pip install reportlab
python scripts/render_pdf.py examples/reader.json demo.pdf
```

HTML 无 Python 第三方依赖。样例 HTML 带第一遍自测，PDF 保持固定版式，折叠自测只在 HTML 中显示。PDF 如果找不到中文字体，按提示用 `--zh-font` 指定本机 CJK TrueType 字体。更详细的字段见 [阅读数据格式](references/input-format.md)。

## 可选用法：导入 Zotero 阅读

把生成的 HTML 拖到 Zotero 里原论文的条目上，作为子附件。确认「设置 → 常规 → 阅读器」中快照使用 Zotero 打开，然后双击附件，即可选中文字、划线和写批注。详见 [Zotero 附件与版本说明](references/zotero.md)。

## 致谢

最初的双栏精读构想来自 X 上的一则分享。感谢原作者分享这个读法，并同意在介绍本 skill 时引用原帖。本项目把原构想做成可复用的阅读模板，并补上原文页码标记、图表与批注往返、可选 PDF 导出，以及 Zotero 快照阅读支持。

三轮阅读自测借鉴了 S. Keshav 的三遍阅读法。本项目把它改编为 16 道贴在相关段落旁的自测题，先抓主旨，再核对方法与证据，最后按需深入。AI 参考答案默认折叠。[How to Read a Paper](https://cs.uwaterloo.ca/~brecht/courses/Perf-Eval-Shared/readings/keshav-paper-reading.pdf)

示例使用虚构研究和自制图，仅演示工作流。HTML 内嵌的 Lora、IBM Plex Sans 拉丁子集使用 SIL Open Font License，许可证位于 `assets/fonts/`。
