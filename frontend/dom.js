export const els = {
  editor: document.getElementById('editor'),
  lineNumbers: document.getElementById('line-numbers'),
  pathLabel: document.getElementById('path-label'),
  statusBadge: document.getElementById('status-badge'),
  summaryLabel: document.getElementById('summary-label'),
  messagesBox: document.getElementById('messages'),
  tokensBody: document.getElementById('tokens-body'),
  astPre: document.getElementById('ast-pre'),
  semanticResult: document.getElementById('semantic-result'),
  buttons: {
    open: document.getElementById('open-btn'),
    save: document.getElementById('save-btn'),
    saveAs: document.getElementById('save-as-btn'),
    run: document.getElementById('run-btn'),
    newFile: document.getElementById('new-btn'),
    semantic: document.getElementById('semantic-btn'),
  },
};

// Contenido inicial vacio para empezar a trabajar sin snippet pre-cargado.
export const sampleCode = "";
