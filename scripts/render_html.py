"""Render a single, script-free HTML reader for browsers and Zotero."""

from argparse import ArgumentParser
from base64 import b64encode
from html import escape
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from string import Template

from reader_data import COLORS, NOTE_FIELDS, load_reader, paragraphs

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def render(data):
    font_dir = ASSETS / 'fonts'
    font_faces = []
    for family, filename in [('Lora', 'Lora-Latin'), ('IBM Plex Sans', 'IBM-Plex-Sans-Latin')]:
        encoded = b64encode((font_dir / (filename + '.woff2')).read_bytes()).decode('ascii')
        font_faces.append(f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{encoded}) format('woff2');font-style:normal;font-weight:400;font-display:swap}}")
    mark_colors = '\n'.join(f'.{k}{{--mark:{bg};--edge:{edge}}}' for k, (bg, edge, _) in COLORS.items())
    legend = ''.join(f'<span class="chip {key}">{label}</span>' for key, (_, _, label) in COLORS.items())

    def anchor(key, label):
        return f'<a href="#{key}">{escape(label)}</a>'

    def note_prose(text):
        return '<div class="note-prose">' + ''.join(f'<p>{escape(para)}</p>' for para in paragraphs(text)) + '</div>'

    prompts_by_block = {}
    study_links = []
    for low, high, phase, label in [
        (1, 6, '第一遍', '抓主旨，决定是否继续'),
        (7, 13, '第二遍', '看方法与证据'),
        (14, 16, '第三遍', '可选深入'),
    ]:
        prompts = [prompt for prompt in data['study'] if low <= prompt['number'] <= high]
        if prompts:
            first = prompts[0]['number']
            last = prompts[-1]['number']
            numbers = [prompt['number'] for prompt in prompts]
            span = f'Q{first}–{last}' if first < last and numbers == list(range(first,last+1)) else '、'.join(f'Q{n}' for n in numbers)
            study_links.append(f'<li>{anchor(f"study-q{first}", f"{phase} · {label}（{span}）")}</li>')
        for index, prompt in enumerate(prompts):
            n = prompt['number']
            sources = prompt.get('sources', [])
            answer = ''.join(f'<p>{escape(paragraph)}</p>' for paragraph in prompt['answer'].split('\n\n') if paragraph.strip())
            if sources:
                answer += '<p class="study-sources">回看依据 ' + ' · '.join(anchor(s['target'], s['label']) for s in sources) + '</p>'
            onward = ''
            if index + 1 < len(prompts):
                following = prompts[index+1]['number']
                onward = f'<p class="study-next">{anchor(f"study-q{following}", f"下一题 · Q{following}")}</p>'
            prompts_by_block.setdefault(prompt['at'], []).append(
                f'<div class="study-prompt" id="study-q{n}" tabindex="-1">'
                f'<p class="study-label">{phase} · Q{n}</p><p class="study-question">{escape(prompt["question"])}</p>'
                f'<details class="study-answer"><summary aria-label="查看 AI 参考答案 · Q{n}">查看 AI 参考答案</summary>'
                f'<div class="study-answer-body">{answer}</div></details>{onward}</div>'
            )
    study_guide = ''
    if study_links:
        study_guide = (
            '<section class="study-guide" id="study-guide" tabindex="-1"><h2>三遍阅读自测</h2>'
            '<p>按遍次进入，先自己作答，再展开参考答案。读完第一遍就可以决定是否继续。</p>'
            '<ul>' + ''.join(study_links) + '</ul></section>'
        )

    visuals = {}
    for key, item in data['evidence'].items():
        image = item['image_path']
        encoded = b64encode(image.read_bytes()).decode('ascii')
        subtype = 'png' if image.suffix.lower() == '.png' else 'jpeg'
        title = escape(item['title'])
        caption_zh = escape(item['caption_zh'])
        reading = ''
        if 'annotation' in item:
            reading = (
                f'<aside class="annotation data figure-note" aria-label="{title} · 图表解读">'
                f'<p class="figure-note-title"><strong>图表解读</strong></p>{note_prose(item["annotation"])}</aside>'
            )
        visuals.setdefault(item['after'], []).append(
            f'<div class="evidence" id="{key}" tabindex="-1"><figure><p class="figure-name">{title} · {escape(item["source"])}</p>'
            f'<img src="data:image/{subtype};base64,{encoded}" alt="{title}"><figcaption>'
            f'<p lang="en">{escape(item["caption_en"])}</p><p>{caption_zh}</p></figcaption></figure>{reading}'
            f'<p class="evidence-return">{anchor(item["after"], "返回对应段落与批注")}</p></div>'
        )

    sections = []
    for section in data['sections']:
        sections.append(f'<section id="{section["id"]}" tabindex="-1"><h2>{escape(section["title"])}</h2>')
        for item in section['blocks']:
            key = item['id']
            if 'heading' in item:
                sections.append(f'<h3>{escape(item["heading"])}</h3>')
            en = []
            for target, runs in groupby(item['runs'], key=itemgetter(1)):
                passage = ''.join(
                    f'<mark class="{kind}" title="{COLORS[kind][2]}">{escape(text)}</mark>'
                    if kind else escape(text) for kind, _, text in runs
                )
                en.append(f'<a href="#{target}">{passage}</a>' if target else passage)
            tone = next((kind for kind, _, _ in item['runs'] if kind), 'method')
            annotation = item['annotation']
            if isinstance(annotation, str):
                body = note_prose(annotation)
            else:
                fields = ''.join(f'<dt>{label}</dt><dd>{escape(annotation[k])}</dd>' for k, label in NOTE_FIELDS.items())
                body = f'<dl>{fields}</dl>'
            links = ''.join(anchor(k, f'查看{data["evidence"][k]["title"]}') for k in item['evidence'])
            actions = f'<p class="evidence-links">{links}</p>' if links else ''
            notes = f'<aside class="annotation {tone}" aria-label="段落批注">{body}{actions}</aside>'
            if key in prompts_by_block:
                notes = '<div>' + ''.join(prompts_by_block[key]) + notes + '</div>'
            sections.append(
                f'<article class="pair" id="{key}" tabindex="-1"><div>'
                f'<p class="source">{key} · {escape(item["source"])}</p>'
                f'<p class="en" lang="en">{"".join(en)}</p><p class="zh">{escape(item["zh"])}</p></div>'
                f'{notes}</article>'
            )
            sections.extend(visuals.get(key, []))
        sections.append('</section>')

    summary = data['summary']
    chain = ''.join(f'<li><strong>{escape(step["label"])}</strong>{escape(step["text"])}'
                    + (anchor(step['target'], '查看对应原文或证据') if 'target' in step else '') + '</li>'
                    for step in summary['chain'])
    overview = (
        '<section id="argument-summary" tabindex="-1"><h2>论证结构总览</h2>'
        f'<ol class="chain">{chain}</ol><p><strong>作者核心主张</strong>　{escape(summary["claim"])}</p>'
        f'<div class="bounds"><div><strong>论证最强处</strong><p>{escape(summary["strongest"])}</p></div>'
        f'<div><strong>论证最弱处</strong><p>{escape(summary["weakest"])}</p></div></div></section>'
    )
    navigation = ''.join(anchor(s['id'], s['title']) for s in data['sections'])
    if study_guide:
        navigation = anchor('study-guide', '三遍自测') + navigation
    navigation += anchor('argument-summary', '论证总览')
    references = ''
    if data['references']:
        navigation += anchor('reader-references', '参考文献')
        entries = []
        for entry in data['references']:
            citation = escape(entry['text'])
            if 'id' not in entry:
                entries.append(f'<li>{citation}</li>')
                continue
            returns = ' · '.join(anchor(key, f'返回正文 {key}') for key in entry['cited_by'])
            links = f'<div class="reference-links">{returns}</div>' if returns else ''
            entries.append(f'<li class="reference-entry" id="{entry["id"]}" tabindex="-1">{citation}{links}</li>')
        references = (
            '<section id="reader-references" tabindex="-1"><h2>参考文献</h2>'
            f'<ol class="references">{"".join(entries)}</ol></section>'
        )
    course = f' · {escape(data["course"])}' if 'course' in data else ''
    source_url = f' · <a href="{escape(data["source_url"], quote=True)}">原论文</a>' if 'source_url' in data else ''
    font_licenses = ''.join(f'<pre>{escape((font_dir / name).read_text(encoding="utf-8-sig"))}</pre>'
                           for name in ['OFL-Lora.txt', 'OFL-IBM-Plex-Sans.txt'])
    return Template((ASSETS / 'reader.html').read_text(encoding='utf-8')).substitute(
        title_zh=escape(data['title_zh']), title=escape(data['title']), citation=escape(data['citation']),
        scope=escape(data['scope']), course=course, source_url=source_url, legend=legend,
        font_faces='\n'.join(font_faces), mark_colors=mark_colors, font_licenses=font_licenses,
        navigation=navigation, study_guide=study_guide, sections='\n'.join(sections), summary=overview, references=references,
    )


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        html = render(load_reader(args.input))
        with args.output.open('x', encoding='utf-8', newline='\n') as file:
            file.write(html)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(args.output.resolve())


if __name__ == '__main__':
    main()
