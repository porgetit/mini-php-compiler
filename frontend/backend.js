async function invoke(apiName, ...args) {
  if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api[apiName] !== 'function') {
    throw new Error('API de PyWebView no disponible.');
  }
  return await window.pywebview.api[apiName](...args);
}

export const backendApi = {
  openFileDialog: () => invoke('open_file_dialog'),
  saveFile: (path, content) => invoke('save_file', path, content),
  saveFileAs: (suggested, content) => invoke('save_file_as', suggested, content),
  compile: (code, path) => invoke('compile', code, path),
  semanticPreview: (code) => invoke('semantic_preview', code),
};
