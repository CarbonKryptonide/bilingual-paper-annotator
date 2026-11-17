(() => {
  const fragments = Array.from(document.querySelectorAll('main [data-alignment]'), element => ({
    element,
    text: element.firstChild,
    groups: element.dataset.alignment.split(' '),
    lane: element.dataset.alignmentLane,
  }));

  function overlaps(range, text) {
    // Touching the first or last character boundary does not select this fragment.
    return range.intersectsNode(text)
      && !(range.endContainer === text && range.endOffset === 0)
      && !(range.startContainer === text && range.startOffset === text.length);
  }

  function update() {
    const selection = document.getSelection();
    const selected = new Map();
    if (selection && !selection.isCollapsed) {
      const ranges = Array.from({ length: selection.rangeCount }, (_, i) => selection.getRangeAt(i));
      for (const { text, groups, lane } of fragments) {
        if (!ranges.some(range => overlaps(range, text))) continue;
        for (const group of groups) {
          if (!selected.has(group)) selected.set(group, new Set());
          selected.get(group).add(lane);
        }
      }
    }

    for (const { element, groups, lane } of fragments) {
      const matched = groups.some(group => selected.has(group) && !selected.get(group).has(lane));
      element.classList.toggle('alignment-match', matched);
    }
  }

  document.documentElement.classList.add('alignment-enabled');
  document.addEventListener('selectionchange', update);
})();
