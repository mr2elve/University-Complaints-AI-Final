(() => {
  const config = __LOCALE_PAYLOAD__;
  window.universityLocaleObserver?.disconnect();
  document.documentElement.lang = config.language;
  document.title = config.title;
  const scopes = [
    '[data-testid="stFileUploader"]',
    '[data-testid="stApp"] > a',
    'a[href^="#"][class*="skip" i]',
    'a[href="#main"]',
    '[data-testid="stSkipToContent"]',
    '[role="log"][aria-live]',
    '[data-testid="stDialog"]',
    '[data-testid="stToolbar"]',
    '[role="status"][aria-live]',
    '[aria-live="polite"][aria-atomic="true"]',
    '[data-testid="stFileUploaderDeleteBtn"]',
    '[data-testid="stElementToolbar"]',
    '[data-testid="stDataFrameColumnVisibilityMenu"]',
    '.gdg-search-status',
    '[data-testid="stDataFrame"] button',
    '[data-testid="stTooltipContent"]',
    '[data-testid="InputInstructions"]',
    '[data-testid="stTextInputInstructions"]',
    '[data-testid="stTextAreaInstructions"]',
    '[data-testid="stHeader"]',
    '[data-testid="stSidebarCollapseButton"]',
    '[data-testid="stExpandSidebarButton"]',
    '[data-baseweb="select"]',
    '[data-baseweb="popover"] [role="menu"]',
    '[data-baseweb="popover"] [role="listbox"]',
    '[data-testid="stMainMenuPopover"]',
    '[data-baseweb="popover"]:has([role="menu"])'
  ].join(',');
  function translated(value) {
    const stripped = value.trim();
    const selected = stripped.match(/^(.*), (selected|таңдалды|выбрано)$/);
    if (selected) return selected[1] + ', ' + config.replacements['selected'];
    const available = stripped.match(/^(\d+) (options available\.|нұсқа қолжетімді\.|вариантов доступно\.)$/);
    if (available) return config.availableCount.replace('{count}', available[1]);
    const typeError = stripped.match(/^(?:Error: )?([^ ]+) files are not allowed\.$/);
    if (typeError) return config.fileTypeError.replace('{type}', typeError[1]);
    const sizeError = stripped.match(/^File must be (.+) or smaller\.$/);
    if (sizeError) return config.fileSizeError.replace('{size}', sizeError[1]);
    const searchPosition = stripped.match(/^(\d+) of (\d+) results?$/);
    if (searchPosition) return config.searchPosition.replace('{current}', searchPosition[1]).replace('{count}', searchPosition[2]);
    const searchResults = stripped.match(/^(\d+) results?$/);
    if (searchResults) return config.searchResults.replace('{count}', searchResults[1]);
    const selectMatches = stripped.match(/^Select (\d+) matches$/);
    if (selectMatches) return config.selectMatches.replace('{count}', selectMatches[1]);
    const replacement = config.replacements[stripped];
    return replacement === undefined ? value : value.replace(stripped, replacement);
  }
  window.universityNativeTextSources ||= new WeakMap();
  let queued = false;
  function apply() {
    queued = false;
    document.querySelectorAll(scopes).forEach(root => {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(node => {
        if (['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT'].includes(node.parentElement?.tagName)) return;
        if (node.parentElement?.closest('[translate="no"]')) return;
        const previous = window.universityNativeTextSources.get(node);
        const source = previous && node.data === previous.output ? previous.source : node.data;
        const next = translated(source);
        window.universityNativeTextSources.set(node, {source, output: next});
        if (node.data !== next) node.data = next;
      });
    });
    document.querySelectorAll('[data-testid="search-input"]').forEach(node => {
      const name = config.replacements['Search table'];
      if (node.getAttribute('aria-label') !== name) node.setAttribute('aria-label', name);
    });
    // Attribute values are only replaced on exact known framework phrases.
    document.querySelectorAll('[aria-label], [title], [placeholder], [aria-description]').forEach(node => {
      for (const attribute of ['aria-label', 'title', 'placeholder', 'aria-description']) {
        const current = node.getAttribute(attribute);
        if (current === null) continue;
        const next = translated(current);
        if (current !== next) node.setAttribute(attribute, next);
      }
    });
  }
  window.universityLocaleObserver = new MutationObserver(() => {
    if (!queued) { queued = true; requestAnimationFrame(apply); }
  });
  window.universityLocaleObserver.observe(document.body, {
    childList: true, subtree: true, characterData: true,
    attributes: true, attributeFilter: ['aria-label', 'title', 'placeholder', 'aria-description']
  });
  apply();
})();
