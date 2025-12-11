//
// CONFIGURATION
//

const DEFAULT_TEXT_FILE = 'content.txt';
const AUTO_REFRESH_INTERVAL_MS = 1000; // change if you want faster/slower polling

//
// PUBLIC ENTRY POINT
//

document.addEventListener('DOMContentLoaded', setupViewer);

function setupViewer() {
  const fileName = getRequestedTextFileName(DEFAULT_TEXT_FILE);
  const state = createViewerState(fileName);

  showCurrentFileName(state.fileName);
  startAutoRefresh(state, AUTO_REFRESH_INTERVAL_MS);
}

//
// STATE MANAGEMENT
//

function createViewerState(fileName) {
  return {
    fileName,
    lastRenderedText: null
  };
}

//
// URL / FILE HANDLING
//

function getRequestedTextFileName(defaultName) {
  const params = new URLSearchParams(window.location.search);
  let file = params.get('file');

  if (!file || file.trim() === '') {
    return defaultName;
  }

  file = file.trim();

  // If no extension given, assume ".txt"
  if (!file.includes('.')) {
    file += '.txt';
  }

  // Optional: very basic sanitisation – avoid directory traversal
  file = file.replace(/[/\\]/g, '');

  return file;
}

function buildTextFileUrl(fileName) {
  const cacheBust = Date.now();
  return `${encodeURIComponent(fileName)}?cacheBust=${cacheBust}`;
}

//
// NETWORK: LOADING THE TEXT FILE
//

async function loadTextFile(fileName) {
  const url = buildTextFileUrl(fileName);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to load "${fileName}": ${response.status} ${response.statusText}`);
    }
    return await response.text();
  } catch (error) {
    console.error(error);
    return '';
  }
}

//
// TEXT → PARAGRAPH MODEL
//

function splitIntoParagraphBlocks(rawText) {
  const normalised = rawText.replace(/\r\n/g, '\n');
  const lines = normalised.split('\n');

  const blocks = [];
  let buffer = [];

  function flushBuffer() {
    if (buffer.length === 0) {
      return;
    }
    const combined = buffer.join(' ').trim();
    buffer = [];
    if (combined) {
      blocks.push(combined);
    }
  }

  for (const line of lines) {
    if (line.trim() === '') {
      // Blank line ends a paragraph
      flushBuffer();
    } else {
      buffer.push(line.trim());
    }
  }

  // Last paragraph if any
  flushBuffer();

  return blocks;
}

function transformBlockToParagraph(blockText) {
  // Detect "H1 " prefix (H1 followed by whitespace)
  const h1Match = /^H1\s+(.*)$/.exec(blockText);

  if (h1Match) {
    return {
      type: 'heading1',
      text: h1Match[1]
    };
  }

  return {
    type: 'paragraph',
    text: blockText
  };
}

function buildParagraphModel(rawText) {
  const blocks = splitIntoParagraphBlocks(rawText);
  return blocks.map(transformBlockToParagraph);
}

//
// DOM RENDERING
//

function getContentContainer() {
  return document.getElementById('content');
}

function clearContent(container) {
  container.innerHTML = '';
}

function createDomNodeForParagraph(paragraph) {
  if (paragraph.type === 'heading1') {
    const h1 = document.createElement('h1');
    h1.textContent = paragraph.text;
    return h1;
  }

  // Default: normal paragraph
  const p = document.createElement('p');
  p.textContent = paragraph.text;
  return p;
}

function renderParagraphs(paragraphs, container) {
  clearContent(container);
  for (const paragraph of paragraphs) {
    const node = createDomNodeForParagraph(paragraph);
    container.appendChild(node);
  }
}

//
// SCROLL POSITION HANDLING
//

function rememberScrollPosition() {
  return window.scrollY || document.documentElement.scrollTop || 0;
}

function restoreScrollPosition(scrollY) {
  window.scrollTo(0, scrollY);
}

//
// AUTO-REFRESH LOOP
//

async function refreshViewOnce(state) {
  const rawText = await loadTextFile(state.fileName);

  // If nothing changed, skip re-render and keep scroll
  if (rawText === state.lastRenderedText) {
    return;
  }

  const previousScrollY = rememberScrollPosition();

  state.lastRenderedText = rawText;

  const paragraphs = buildParagraphModel(rawText);
  const container = getContentContainer();
  renderParagraphs(paragraphs, container);

  restoreScrollPosition(previousScrollY);
}

function startAutoRefresh(state, intervalMs) {
  // Initial render
  refreshViewOnce(state);

  // Periodic updates (on save the file changes, so we re-render)
  setInterval(() => {
    refreshViewOnce(state);
  }, intervalMs);
}

//
// UI UTILITIES
//

function showCurrentFileName(fileName) {
  const indicator = document.getElementById('file-indicator');
  if (!indicator) return;
  indicator.textContent = `Viewing: ${fileName}`;
}

