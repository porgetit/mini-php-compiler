import { els, sampleCode } from './dom.js';

export const state = {
  path: null,
  dirty: false,
  running: false,
};

function setBadgeTone(tone) {
  const toneClass = tone === 'success' ? 'success' : tone === 'warning' ? 'warning' : 'transparent';
  els.statusBadge.className = `badge rounded-pill status-pill bg-${toneClass}`;
}

export function setStatus(text, tone = 'info') {
  els.statusBadge.textContent = text;
  setBadgeTone(tone);
}

export function setPath(path) {
  state.path = path;
  els.pathLabel.textContent = path || 'Sin archivo seleccionado';
}

export function markDirty() {
  state.dirty = true;
  setStatus('Cambios sin guardar', 'warning');
}

export function markClean() {
  state.dirty = false;
  setStatus('Listo', 'info');
}

export function basename(path) {
  if (!path) return '';
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1];
}

export function renderMessages(result) {
  const combined = [
    ...(result.lexical_messages || []).map((m) => ({ ...m, bucket: 'Lexico' })),
    ...(result.syntax_messages || []).map((m) => ({ ...m, bucket: 'Sintactico' })),
  ];
  els.messagesBox.innerHTML = '';

  if (combined.length === 0) {
    els.messagesBox.innerHTML = '<div class="text-secondary small">Sin mensajes. Ejecuta el compilador para ver resultados.</div>';
    return;
  }

  const list = document.createElement('ul');
  list.className = 'list-unstyled mb-0';
  combined.forEach((entry) => {
    const li = document.createElement('li');
    li.className = 'py-2';
    li.innerHTML = `
      <div class="d-flex align-items-center justify-content-between">
        <span class="badge text-bg-${entry.level === 'error' ? 'danger' : entry.level === 'warning' ? 'warning' : 'secondary'}">${entry.bucket}</span>
        <span class="text-secondary small">${entry.level?.toUpperCase() || 'INFO'}</span>
      </div>
      <div class="mt-1 small">${entry.message}</div>
    `;
    list.appendChild(li);
  });
  els.messagesBox.appendChild(list);
}

export function renderTokens(tokens) {
  els.tokensBody.innerHTML = '';
  if (!tokens || tokens.length === 0) {
    els.tokensBody.innerHTML = '<tr><td colspan="3" class="text-center text-secondary">Sin datos</td></tr>';
    return;
  }
  const rows = tokens.map((t) => {
    const line = typeof t.lineno === 'number' ? t.lineno.toString().padStart(3, '0') : '-';
    const value = typeof t.value === 'string' ? t.value : JSON.stringify(t.value);
    return `<tr><td class="text-secondary">${line}</td><td class="text-info">${t.type}</td><td class="text-light">${value}</td></tr>`;
  });
  els.tokensBody.innerHTML = rows.join('');
}

export function renderAst(astJson) {
  els.astPre.textContent = astJson || 'Sin AST disponible';
}

export function updateSummary(result) {
  const total = (result.lexical_errors || 0) + (result.syntax_errors || 0);
  const color = total === 0 ? 'text-success' : 'text-warning';
  els.summaryLabel.className = `small ${color}`;
  els.summaryLabel.textContent = `Errores -> Lexico: ${result.lexical_errors} | Sintactico: ${result.syntax_errors}`;
}

export function showError(message) {
  els.messagesBox.innerHTML = `<div class="text-danger small">${message}</div>`;
}

export function resetOutputs() {
  renderMessages({ lexical_messages: [], syntax_messages: [] });
  renderTokens([]);
  renderAst(null);
  els.summaryLabel.textContent = 'Sin ejecuciones';
}

export function resetEditorToSample() {
  els.editor.value = sampleCode;
  setPath(null);
  markClean();
  updateLineNumbers();
  resetOutputs();
}

export function initEditorContent() {
  els.editor.value = sampleCode;
}

export function updateLineNumbers() {
  const value = els.editor.value || '';
  const lines = (value.match(/\n/g)?.length || 0) + 1;
  const gutter = Array.from({ length: lines }, (_, i) => `<div class="line-number-row">${i + 1}</div>`).join('');
  els.lineNumbers.innerHTML = gutter;
}

export function syncLineNumbersScroll() {
  els.lineNumbers.scrollTop = els.editor.scrollTop;
}
