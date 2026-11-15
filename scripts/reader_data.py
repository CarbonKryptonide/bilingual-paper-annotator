"""Load and validate the shared reading data for both renderers."""

import json
import re
from itertools import pairwise
from pathlib import PureWindowsPath
from urllib.parse import urlsplit

COLORS = {
    'thesis': ('#fbe79e', '#835a00', '核心论点'),
    'term': ('#f9d0cb', '#944338', '关键概念'),
    'data': ('#d0e8ff', '#275e89', '证据与数据'),
    'limit': ('#d9edcb', '#3f643c', '让步与反驳'),
    'method': ('#e9ddfc', '#674884', '方法说明'),
}
NOTE_FIELDS = {'function': '段落功能', 'role': '逻辑角色', 'critique': '技巧与局限'}
SYSTEM_IDS = {'reader-content', 'argument-summary', 'reader-references', 'reader-evidence'}
STUDY_IDS = {'study-guide'} | {f'study-q{n}' for n in range(1, 17)}


def fields(obj, keys, location):
    if not isinstance(obj, dict):
        raise ValueError(f'{location} must be an object')
    for key in keys:
        if not isinstance(obj.get(key), str) or not obj[key].strip():
            raise ValueError(f'{location}.{key} must be non-empty text')


def array(obj, key, required=False):
    value = obj.get(key) if required else obj.get(key, [])
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f'{key} must be {"a non-empty" if required else "an"} array')
    return value


def locate_spans(text, items, value_key, location):
    spans = []
    for item in items:
        fields(item, (value_key, 'text'), location)
        phrase = item['text']
        count = item.get('occurrence', 1)
        if type(count) is not int or count < 1:
            raise ValueError(f'{location}: invalid occurrence')
        start = -len(phrase)
        for _ in range(count):
            start = text.find(phrase, start + len(phrase))
            if start < 0:
                raise ValueError(f'{location}: missing exact text {phrase!r}')
        spans.append((start, start + len(phrase), item[value_key]))
    spans.sort()
    cursor = 0
    for start, end, _ in spans:
        if cursor > start:
            raise ValueError(f'{location}: overlapping spans')
        cursor = end
    return spans


def inline_runs(text, marks, citations):
    # A citation may cross a highlight boundary. Track the two layers separately.
    changes = {0: {}, len(text): {}}
    for layer, spans in enumerate((marks, citations)):
        for start, end, value in spans:
            changes.setdefault(start, {})[layer] = value
            changes.setdefault(end, {})[layer] = None
    active = [None, None]
    for start, end in pairwise(sorted(changes)):
        for layer, value in changes[start].items():
            active[layer] = value
        yield active[0], active[1], text[start:end]


def load_reader(path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    fields(data, ('title', 'title_zh', 'citation', 'scope'), 'reader')
    for key in ('course', 'source_url'):
        if key in data:
            fields(data, (key,), 'reader')
    if 'source_url' in data:
        url = urlsplit(data['source_url'])
        if url.scheme not in ('https', 'http') or not url.hostname:
            raise ValueError('source_url must be an HTTP(S) link')
    study = array(data, 'study')
    reserved = SYSTEM_IDS | STUDY_IDS if study else SYSTEM_IDS
    ids = set(reserved)

    def register(obj, location):
        key = obj['id']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', key) or key in ids:
            raise ValueError(f'{location}: invalid or duplicate ID {key!r}')
        ids.add(key)

    references = []
    linked_refs = {}
    for entry in array(data, 'references'):
        if isinstance(entry, str):
            if not entry.strip():
                raise ValueError('references must contain non-empty entries')
            references.append({'text': entry})
            continue
        fields(entry, ('id', 'text'), 'reference')
        register(entry, 'reference')
        reference = {'id': entry['id'], 'text': entry['text'], 'cited_by': []}
        references.append(reference)
        linked_refs[entry['id']] = reference
    data['references'] = references

    blocks = {}
    for section in array(data, 'sections', required=True):
        fields(section, ('id', 'title'), 'section')
        register(section, 'section')
        for block in array(section, 'blocks', required=True):
            fields(block, ('id', 'source', 'en', 'zh'), 'block')
            key = block['id']
            register(block, 'block')
            fields(block.get('annotation'), NOTE_FIELDS, f'{key}.annotation')
            if 'heading' in block:
                fields(block, ('heading',), key)
            marks = locate_spans(block['en'], array(block, 'marks'), 'kind', f'{key}.marks')
            if any(kind not in COLORS for _, _, kind in marks):
                raise ValueError(f'{key}.marks: unknown highlight kind')
            citations = locate_spans(block['en'], array(block, 'citations'), 'target', f'{key}.citations')
            for target in dict.fromkeys(target for _, _, target in citations):
                if target not in linked_refs:
                    raise ValueError(f'{key}.citations: unknown reference {target!r}')
                linked_refs[target]['cited_by'].append(key)
            block['runs'] = list(inline_runs(block['en'], marks, citations))
            blocks[key] = block

    parent = path.resolve().parent
    evidence = {}
    for item in array(data, 'evidence'):
        fields(item, ('id', 'title', 'file', 'source', 'caption_en', 'caption_zh', 'after'), 'evidence')
        register(item, 'evidence')
        filename = PureWindowsPath(item['file'])
        source = parent.joinpath(*filename.parts).resolve()
        if (not source.is_relative_to(parent) or filename.drive or filename.root
                or source.suffix.lower() not in ('.png', '.jpg', '.jpeg') or not source.is_file()):
            raise ValueError(f'{item["id"]}: expected a relative PNG or JPEG beside the input')
        if item['after'] not in blocks:
            raise ValueError(f'{item["id"]}: unknown evidence placement {item["after"]!r}')
        item['image_path'] = source
        evidence[item['id']] = item

    for block in blocks.values():
        links = array(block, 'evidence')
        if any(not isinstance(key, str) or key not in evidence for key in links):
            raise ValueError(f'{block["id"]}: unknown evidence link')
        block['evidence'] = list(dict.fromkeys(links))
    for key, item in evidence.items():
        links = blocks[item['after']]['evidence']
        if key not in links:
            links.append(key)
    data['evidence'] = evidence

    summary = data.get('summary')
    fields(summary, ('claim', 'strongest', 'weakest'), 'summary')
    for point in array(summary, 'chain', required=True):
        fields(point, ('label', 'text'), 'summary.chain')
        if 'target' in point:
            fields(point, ('target',), 'summary.chain')
            if point['target'] not in ids - reserved:
                raise ValueError(f'Unknown summary target {point["target"]!r}')
    numbers = set()
    for prompt in study:
        fields(prompt, ('at', 'question', 'answer'), 'study')
        n = prompt.get('number')
        if type(n) is not int or not 1 <= n <= 16 or n in numbers:
            raise ValueError(f'study: expected a unique question number from 1 to 16, got {n!r}')
        numbers.add(n)
        if prompt['at'] not in blocks:
            raise ValueError(f'study Q{n}: unknown paragraph {prompt["at"]!r}')
        for source in array(prompt, 'sources'):
            fields(source, ('target', 'label'), f'study Q{n}.sources')
            if source['target'] not in ids - reserved:
                raise ValueError(f'study Q{n}: unknown source {source["target"]!r}')
    data['study'] = sorted(study, key=lambda prompt: prompt['number'])
    return data
