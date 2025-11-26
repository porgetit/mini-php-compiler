import { els } from './dom.js';
import {
  state,
  setStatus,
  setPath,
  markDirty,
  markClean,
  basename,
  renderMessages,
  renderTokens,
  renderAst,
  updateSummary,
  showError,
  resetOutputs,
  resetEditorToSample,
  initEditorContent,
  updateLineNumbers,
  syncLineNumbersScroll,
} from './ui.js';
import { backendApi } from './backend.js';

async function handleOpenFile() {
  try {
    setStatus('Abriendo archivo...', 'info');
    const result = await backendApi.openFileDialog();
    if (result.cancelled) {
      setStatus('Accion cancelada', 'info');
      return;
    }
    if (!result.ok) {
      setStatus('No se pudo abrir', 'warning');
      showError(result.error);
      return;
    }
    els.editor.value = result.content || '';
    setPath(result.path || null);
    updateLineNumbers();
    markClean();
  } catch (err) {
    setStatus('Fallo al abrir', 'warning');
    showError(err);
  }
}

async function handleSaveFile() {
  try {
    if (!state.path) {
      await handleSaveFileAs();
      return;
    }
    const result = await backendApi.saveFile(state.path, els.editor.value);
    if (!result.ok) {
      setStatus('No se pudo guardar', 'warning');
      showError(result.error);
      return;
    }
    setPath(result.path);
    markClean();
    setStatus('Guardado', 'success');
  } catch (err) {
    setStatus('Fallo al guardar', 'warning');
    showError(err);
  }
}

async function handleSaveFileAs() {
  try {
    const suggested = basename(state.path) || 'codigo.php';
    const result = await backendApi.saveFileAs(suggested, els.editor.value);
    if (result.cancelled) {
      setStatus('Guardado cancelado', 'info');
      return;
    }
    if (!result.ok) {
      setStatus('No se pudo guardar', 'warning');
      showError(result.error);
      return;
    }
    setPath(result.path);
    markClean();
    setStatus('Guardado', 'success');
  } catch (err) {
    setStatus('Fallo al guardar', 'warning');
    showError(err);
  }
}

async function handleRunCompiler() {
  if (state.running) return;
  state.running = true;
  setStatus('Compilando...', 'info');
  try {
    const result = await backendApi.compile(els.editor.value, state.path);
    renderMessages(result);
    renderTokens(result.tokens);
    renderAst(result.ast_json);
    updateSummary(result);
    setStatus(result.ok ? 'Compilacion exitosa' : 'Compilacion con errores', result.ok ? 'success' : 'warning');
  } catch (err) {
    setStatus('Fallo al compilar', 'warning');
    showError(err);
  } finally {
    state.running = false;
  }
}

async function handleSemanticPreview() {
  try {
    els.semanticResult.textContent = 'Ejecutando preview...';
    const result = await backendApi.semanticPreview(els.editor.value);
    els.semanticResult.textContent = result.message || (result.ok ? 'Listo' : 'No implementado aun.');
  } catch (err) {
    els.semanticResult.textContent = `Error: ${err}`;
  }
}

function wireEvents() {
  els.buttons.open.addEventListener('click', handleOpenFile);
  els.buttons.save.addEventListener('click', handleSaveFile);
  els.buttons.saveAs.addEventListener('click', handleSaveFileAs);
  els.buttons.run.addEventListener('click', handleRunCompiler);
  els.buttons.newFile.addEventListener('click', resetEditorToSample);
  els.buttons.semantic.addEventListener('click', handleSemanticPreview);
  const updateOnChange = () => {
    markDirty();
    updateLineNumbers();
  };
  ['input', 'change', 'keyup', 'cut', 'paste', 'drop'].forEach((evt) => {
    els.editor.addEventListener(evt, updateOnChange);
  });
  els.editor.addEventListener('scroll', syncLineNumbersScroll);
}

function start() {
  initEditorContent();
  updateLineNumbers();
  wireEvents();
  markClean();
  resetOutputs();
  els.semanticResult.textContent = 'Pendiente de implementacion.';
}

if (window.pywebview) {
  start();
} else {
  window.addEventListener('pywebviewready', start);
}
