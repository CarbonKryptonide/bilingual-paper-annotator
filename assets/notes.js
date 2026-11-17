(() => {
  const get = id => document.getElementById(id);
  const reader = get('reader-content');
  const panel = get('reader-notes');
  if (typeof panel.showModal !== 'function') return;

  const tools = get('reading-tools');
  const editor = get('note-editor');
  const status = get('note-status');
  const comment = get('note-comment');
  const fields = ['en', 'zh', 'annotation'];
  const labels = { en: '原文', zh: '译文', annotation: '段落批注' };
  const readerId = reader.dataset.readerId;
  const storageKey = `bilingual-paper-notes:${readerId}`;
  const canHighlight = Boolean(globalThis.CSS?.highlights && globalThis.Highlight);
  let notes = [];
  let selected = null;
  let draft = null;

  function parse(text) {
    const backup = JSON.parse(text);
    if (!backup || backup.version !== 1 || !Array.isArray(backup.notes)) {
      throw new Error('无法识别这个笔记文件。');
    }
    if (backup.readerId !== readerId) throw new Error('这份笔记属于另一份读稿。');
    for (const item of backup.notes) {
      if (!item || !fields.includes(item.field) || !Number.isSafeInteger(item.start) || item.start < 0
          || !['id', 'block', 'quote'].every(key => typeof item[key] === 'string' && item[key].trim())
          || !['before', 'after', 'comment'].every(key => typeof item[key] === 'string')) {
        throw new Error('笔记文件含有无效条目。');
      }
    }
    return [...new Map(backup.notes.map(item => [item.id, item])).values()];
  }

  function serialize() {
    return JSON.stringify({ version: 1, readerId, notes }, null, 2);
  }

  function save(message) {
    try {
      localStorage.setItem(storageKey, serialize());
      status.textContent = `${message} · 已自动保存`;
    } catch {
      status.textContent = `${message} · 自动保存不可用，请导出 JSON`;
    }
    render();
  }

  function fieldAt(node) {
    const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    return element?.closest('[data-note-field]');
  }

  function readSelection() {
    const selection = document.getSelection();
    // Keep a readable preview when focus moves from the selection to the toolbar.
    if (!selection || selection.isCollapsed) return;
    const range = selection.getRangeAt(0);
    const field = fieldAt(range.startContainer);
    const block = field?.closest('article.pair');
    if (!block || field !== fieldAt(range.endContainer)) {
      setSelection(null);
      return;
    }
    const prefix = document.createRange();
    prefix.selectNodeContents(field);
    prefix.setEnd(range.startContainer, range.startOffset);
    const start = prefix.toString().length;
    const quote = range.toString();
    const text = field.textContent;
    setSelection(quote.trim() ? {
      block: block.id, field: field.dataset.noteField, start, quote,
      before: text.slice(Math.max(0, start - 24), start), after: text.slice(start + quote.length, start + quote.length + 24),
    } : null);
  }

  function setSelection(value) {
    selected = value;
    get('note-highlight').disabled = !value || !canHighlight;
    get('note-write').disabled = !value;
    const excerpt = value?.quote.trim().replace(/\s+/g, ' ');
    get('note-selection').textContent = excerpt
      ? `已选 ${excerpt.length > 48 ? excerpt.slice(0, 48) + '…' : excerpt}` : '请在同一段原文、译文或段落批注内划选文字';
  }

  function locate(item) {
    const block = document.getElementById(item.block);
    const field = block?.querySelector(`[data-note-field="${item.field}"]`);
    if (!field) return null;
    const text = field.textContent;
    const matches = [];
    const contextual = [];
    for (let index = text.indexOf(item.quote); index >= 0; index = text.indexOf(item.quote, index + 1)) {
      matches.push(index);
      if (text.slice(0, index).endsWith(item.before) && text.startsWith(item.after, index + item.quote.length)) {
        contextual.push(index);
      }
    }
    const start = contextual.includes(item.start) ? item.start
      : contextual.length === 1 ? contextual[0] : matches.length === 1 ? matches[0] : -1;
    if (start < 0) return null;

    const end = start + item.quote.length;
    const walker = document.createTreeWalker(field, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    let offset = 0;
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const next = offset + node.length;
      if (offset <= start && start < next) range.setStart(node, start - offset);
      if (offset < end && end <= next) {
        range.setEnd(node, end - offset);
        return range;
      }
      offset = next;
    }
    return null;
  }

  function action(label, handler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', handler);
    return button;
  }

  function render() {
    const entries = [];
    const ranges = [];
    for (const item of notes) {
      const range = locate(item);
      const row = document.createElement('li');
      const quote = document.createElement('p');
      quote.textContent = `${labels[item.field]} · ${item.quote}`;
      quote.lang = item.field === 'en' ? 'en' : 'zh-CN';
      row.append(quote);
      if (item.comment) {
        const body = document.createElement('p');
        body.textContent = item.comment;
        row.append(body);
      }
      const actions = document.createElement('div');
      actions.className = 'note-actions';
      if (range) {
        ranges.push(range);
        actions.append(action('定位', () => {
          panel.close();
          const bounds = range.getBoundingClientRect();
          const top = window.scrollY + bounds.top - tools.getBoundingClientRect().bottom - 24;
          window.scrollTo({ top, behavior: 'instant' });
        }));
      } else {
        actions.append('待定位');
      }
      actions.append(action('编辑', () => edit(item)), action('删除', () => {
        notes = notes.filter(note => note.id !== item.id);
        save('已删除');
        panel.querySelector('header button').focus();
      }));
      row.append(actions);
      entries.push(row);
    }
    get('note-entries').replaceChildren(...entries);
    get('notes-empty').hidden = notes.length > 0;
    get('note-export').disabled = notes.length === 0;
    if (canHighlight) CSS.highlights.set('reader-notes', new Highlight(...ranges));
  }

  function edit(item) {
    draft = item;
    editor.hidden = false;
    get('note-quote').textContent = item.quote;
    comment.value = item.comment ?? '';
    if (!panel.open) panel.showModal();
    comment.focus();
  }

  function create(target, text = '') {
    const id = crypto.randomUUID?.() ?? crypto.getRandomValues(new Uint32Array(4)).join('-');
    notes.push({ ...target, id, comment: text });
    setSelection(null);
    document.getSelection().removeAllRanges();
  }

  try {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      notes = parse(saved);
      if (notes.length) status.textContent = `已恢复 ${notes.length} 条笔记`;
    }
  } catch {
    status.textContent = '无法读取自动保存的笔记，可尝试导入 JSON。';
  }
  render();
  document.documentElement.classList.add('notes-enabled');
  tools.hidden = false;
  const controls = tools.closest('.reader-controls');
  const sizing = new ResizeObserver(() => {
    const height = Math.max(controls.offsetHeight, tools.offsetHeight);
    document.documentElement.style.setProperty('--reader-scroll-padding', `${height + 12}px`);
  });
  sizing.observe(controls);
  sizing.observe(tools);

  document.addEventListener('selectionchange', readSelection);
  reader.addEventListener('pointerdown', event => { if (!event.shiftKey) setSelection(null); });
  get('note-select').addEventListener('click', () => {
    document.getSelection().removeAllRanges();
    setSelection(null);
  });
  get('note-highlight').addEventListener('click', () => {
    create(selected);
    save('已高亮');
  });
  get('note-write').addEventListener('click', () => edit(selected));
  get('note-list-open').addEventListener('click', () => panel.showModal());
  panel.addEventListener('close', () => { editor.hidden = true; });
  get('note-cancel').addEventListener('click', () => {
    editor.hidden = true;
    panel.querySelector('header button').focus();
  });
  editor.addEventListener('submit', event => {
    event.preventDefault();
    const text = comment.value.trim();
    if (!text) return;
    if (draft.id) draft.comment = text;
    else create(draft, text);
    save('已保存笔记');
    panel.close();
  });

  const file = get('note-file');
  const menu = file.closest('details');
  get('note-import').addEventListener('click', () => file.click());
  file.addEventListener('change', async () => {
    if (!file.files.length) return;
    try {
      const incoming = parse(await file.files[0].text());
      const ids = new Set(notes.map(item => item.id));
      const newNotes = incoming.filter(item => !ids.has(item.id));
      notes.push(...newNotes);
      save(`已导入 ${newNotes.length} 条笔记`);
    } catch (error) {
      status.textContent = error instanceof SyntaxError ? '无法读取 JSON，请检查文件格式。' : error.message;
    } finally {
      file.value = '';
      menu.open = false;
    }
  });
  get('note-export').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([serialize()], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'paper-reader.notes.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    menu.open = false;
  });
})();
