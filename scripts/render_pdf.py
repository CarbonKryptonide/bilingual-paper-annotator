"""Render a selectable-text PDF from the same data as the HTML snapshot."""

from argparse import ArgumentParser
from io import BytesIO
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from reader_data import COLORS, NOTE_FIELDS, load_reader


def render(data, zh_font, en_font):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import Paragraph

    if zh_font is None:
        zh_font = next((p for p in map(Path, [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            '/System/Library/Fonts/PingFang.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf',
        ]) if p.is_absolute() and p.is_file()), None)
    if zh_font is None:
        raise ValueError('Set --zh-font to an embeddable CJK TrueType font (.ttf or TrueType .ttc).')
    if en_font is None:
        en_font = next((p for p in map(Path, [
            'C:/Windows/Fonts/georgia.ttf',
            '/System/Library/Fonts/Supplemental/Georgia.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        ]) if p.is_absolute() and p.is_file()), None)
    pdfmetrics.registerFont(TTFont('ReaderCJK', str(zh_font)))
    if en_font:
        pdfmetrics.registerFont(TTFont('ReaderSerif', str(en_font)))
    serif = 'ReaderSerif' if en_font else 'Times-Roman'

    w, h = landscape(A4)
    margin, gap, left, bottom = 37, 20, 488, 43
    width = w - 2*margin
    right = width - left - gap
    note_x = margin + left + gap
    ink, navy, muted, line, paper = '#17283a', '#12233a', '#40566c', '#dedbd2', '#faf8f2'
    buffer = BytesIO()
    canvas = Canvas(buffer, pagesize=(w, h), pageCompression=1)
    canvas.setTitle(data['title_zh'] + ' · 双栏精读')
    canvas.setSubject(data['citation'])
    styles = {}
    for key, font, size, lead, color in [
        ('en', serif, 11, 15, ink), ('zh', 'ReaderCJK', 11, 16, ink),
        ('note', 'ReaderCJK', 10.5, 15, ink), ('small', 'ReaderCJK', 9, 13, muted),
        ('title', 'ReaderCJK', 24, 31, navy), ('caption', serif, 9.5, 13, muted),
    ]:
        styles[key] = ParagraphStyle(key, fontName=font, fontSize=size, leading=lead,
                                     textColor=HexColor(color), wordWrap='CJK' if font == 'ReaderCJK' else None)

    def p(text, key):
        return Paragraph(text, styles[key])

    def fill(x, top, wide, tall, color):
        canvas.setFillColor(HexColor(color))
        canvas.rect(x, top-tall, wide, tall, stroke=0, fill=1)

    def size(para, wide):
        return para.wrap(wide, 10000)[1]

    def draw(para, x, top, wide):
        tall = size(para, wide)
        para.drawOn(canvas, x, top-tall)
        return tall

    def link(key, text):
        return f'<link href="#{key}" color="#215f88">{escape(text)}</link>'

    y = 0

    def page_frame():
        nonlocal y
        fill(0, h, w, h, paper)
        fill(0, h, w, 33, navy)
        canvas.setFont('ReaderCJK', 10.5)
        canvas.setFillColor(HexColor('#ffffff'))
        canvas.drawString(margin, h-21, '论文双栏精读')
        fill(margin, 31, width, .6, line)
        canvas.setFont(serif, 9)
        canvas.setFillColor(HexColor(muted))
        canvas.drawRightString(w-margin, 17, str(canvas.getPageNumber()))
        y = h-56

    def new_page():
        canvas.showPage()
        page_frame()

    def heading(text, key=None, level=0):
        nonlocal y
        if key:
            canvas.bookmarkHorizontalAbsolute(key, y)
            canvas.addOutlineEntry(text, key, level=level, closed=False)
        y -= draw(p(f'<font color="{navy}" size="16">{escape(text)}</font>', 'title'), margin, y, width)
        fill(margin, y+4, width, .7, line)
        y -= 6

    def prose(para, x=margin, wide=width, spacing=7, target=None):
        """Flow auxiliary prose across pages while preserving full text."""
        nonlocal y
        remaining = [para]
        while remaining:
            chunk = remaining[0]
            if y-bottom < 30:
                new_page()
            chunks = [chunk] if size(chunk, wide) <= y-bottom else chunk.split(wide, y-bottom)
            if not chunks:
                new_page()
                continue
            if target:
                canvas.bookmarkHorizontalAbsolute(target, y)
                target = None
            y -= draw(chunks[0], x, y, wide) + spacing
            remaining[:1] = chunks[1:]
            if remaining:
                new_page()

    page_frame()
    prose(p(escape(data['title_zh']), 'title'))
    prose(p(escape(data['title']), 'en'))
    meta = escape(data['citation'])
    if 'course' in data:
        meta += ' · ' + escape(data['course'])
    if 'source_url' in data:
        meta += f' · <link href={quoteattr(data["source_url"])} color="#215f88">原论文</link>'
    prose(p(meta, 'small'))
    x = margin
    for bg, _, name in COLORS.values():
        fill(x, y, 70, 20, bg)
        draw(p(name, 'small'), x+8, y-3, 55)
        x += 76
    y -= 29
    prose(p(escape(data['scope']), 'small'))

    for section in data['sections']:
        is_first_block = True
        for block in section['blocks']:
            tone = next((kind for kind, _, _ in block['runs'] if kind), 'method')
            bg, edge, category = COLORS[tone]
            fields = '<br/><br/>'.join(f'<font color="{edge}">{label}</font><br/>{escape(block["annotation"][key])}'
                                       for key, label in NOTE_FIELDS.items())
            note = p(fields, 'note')
            note_h = size(note, right-23)
            locator = f'{escape(block["id"])} · {escape(block["source"])}'
            if block['evidence']:
                locator += ' · ' + ' · '.join(link(key, '查看' + data['evidence'][key]['title']) for key in block['evidence'])
            locator = p(locator, 'small')
            heading_h = (size(p(escape(section['title']),'title'),width)+6) if is_first_block else 0
            subheading = p(escape(block['heading']), 'zh') if 'heading' in block else None
            if subheading:
                heading_h += size(subheading, width)+5
            need = max(112, note_h+44, size(locator,left)+40)+heading_h
            if need > h-56-bottom:
                raise ValueError(f'{block["id"]}: shorten the annotation or heading for PDF pagination')
            if y-bottom < need:
                new_page()
            if is_first_block:
                heading(section['title'], section['id'])
                is_first_block = False
            if subheading:
                y -= draw(subheading, margin, y, width)+5
            canvas.bookmarkHorizontalAbsolute(block['id'], y)
            en = []
            for target, runs in groupby(block['runs'], key=itemgetter(1)):
                passage = ''.join(
                    f'<font backColor="{COLORS[kind][0]}">{escape(text)}</font>'
                    if kind else escape(text) for kind, _, text in runs
                )
                en.append(f'<link href="#{target}" color="#215f88"><u>{passage}</u></link>' if target else passage)
            parts = [(
                p(''.join(en).replace('\n', '<br/>'), 'en'), False
            ), (p(escape(block['zh']).replace('\n', '<br/>'), 'zh'), True)]
            first = True
            while parts:
                start = y
                if first:
                    fill(note_x, y, right, note_h+34, bg)
                    fill(note_x, y, 3, note_h+34, edge)
                    draw(p(category, 'small'), note_x+11, y-8, right-23)
                    draw(note, note_x+11, y-22, right-23)
                    y -= draw(locator, margin, y, left)+5
                else:
                    y -= draw(p(escape(block['id']) + ' · 续上页　' + link(block['id'],'返回本段批注'), 'small'), margin, y, left)+5

                while parts:
                    para, chinese = parts[0]
                    wide, pad = (left-21,14) if chinese else (left,0)
                    available = y-bottom-12-pad
                    pieces = [para] if size(para,wide) <= available else para.split(wide,available) if available >= 30 else []
                    if not pieces:
                        break
                    chunk = pieces[0]
                    tall = size(chunk,wide)
                    if chinese:
                        fill(margin,y,left,tall+pad,'#f0ece2')
                        fill(margin,y,1.5,tall+pad,'#b5a684')
                    draw(chunk,margin+11 if chinese else margin,y-7 if chinese else y,wide)
                    y -= tall+pad+7
                    parts[:1] = [(piece,chinese) for piece in pieces[1:]]
                    if len(pieces)>1:
                        break
                if first:
                    y = min(y,start-note_h-43)
                if parts:
                    new_page()
                    first = False
            fill(margin,y,width,.6,line)
            y -= 15

    if y-bottom < 160:
        new_page()
    heading('论证结构总览','argument-summary')
    summary = data['summary']
    for step in summary['chain']:
        line_text = f'<font color="{navy}">{escape(step["label"])}</font>　{escape(step["text"])}'
        if 'target' in step:
            line_text += '　' + link(step['target'],'查看对应原文或证据')
        prose(p(line_text,'zh'))
    for label,key in [('作者核心主张','claim'),('论证最强处','strongest'),('论证最弱处','weakest')]:
        prose(p(f'<font color="{navy}">{label}</font>　{escape(summary[key])}','zh'))

    if data['evidence']:
        new_page()
        heading('图表与原文证据','reader-evidence')
    for index, item in enumerate(data['evidence'].values()):
        if index:
            new_page()
        heading(item['title'],item['id'],level=1)
        y -= draw(p(escape(item['source'])+'　'+link(item['after'],'返回对应段落与批注'),'small'),margin,y,width)+8
        zh = p(escape(item['caption_zh']),'zh')
        en = p(escape(item['caption_en']),'caption')
        image = ImageReader(str(item['image_path']))
        iw, ih = image.getSize()
        caption_height = size(zh,width)+size(en,width)
        caption_reserve = min(caption_height+24,155)
        scale = min(width/iw,(y-bottom-caption_reserve)/ih)
        canvas.drawImage(image,(w-iw*scale)/2,y-ih*scale,iw*scale,ih*scale)
        y -= ih*scale+9
        if caption_height+24 <= 155:
            y -= draw(zh,margin,y,width)+5
            y -= draw(en,margin,y,width)
        else:
            prose(zh)
            prose(en)

    if data['references']:
        new_page()
        heading('参考文献','reader-references')
        for entry in data['references']:
            text = escape(entry['text'])
            if entry.get('cited_by'):
                returns = '　'.join(link(key, f'返回正文 {key}') for key in entry['cited_by'])
                text += f'<br/><font name="ReaderCJK">{returns}</font>'
            prose(p(text, 'caption'), target=entry.get('id'))
    canvas.showPage()
    canvas.save()
    return buffer.getbuffer()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--zh-font', type=Path)
    parser.add_argument('--en-font', type=Path)
    args = parser.parse_args()
    try:
        content = render(load_reader(args.input), args.zh_font, args.en_font)
        with args.output.open('xb') as file:
            file.write(content)
    except ModuleNotFoundError as error:
        parser.exit(1, f'{error}. Install ReportLab in the Python environment used for PDF output.\n')
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(args.output.resolve())


if __name__ == '__main__':
    main()
