const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const fileList = document.getElementById('file-list');
const uploadForm = document.getElementById('upload-form');
const statusMessage = document.getElementById('status-message');
const resultMarkdown = document.getElementById('result-markdown');
const downloadButton = document.getElementById('download-button');
const processButton = document.getElementById('process-button');
const tourButton = document.getElementById('tour-button');
const tourModal = document.getElementById('tour-modal');
const modalClose = document.getElementById('modal-close');

let selectedFiles = [];
let lastFileName = 'documento-unificado.md';

function renderFileList() {
  fileList.innerHTML = '';
  if (!selectedFiles.length) {
    const empty = document.createElement('li');
    empty.textContent = 'Nenhum arquivo selecionado ainda.';
    empty.classList.add('file-list__empty');
    fileList.appendChild(empty);
    return;
  }

  selectedFiles.forEach((file) => {
    const item = document.createElement('li');
    const nameSpan = document.createElement('span');
    const sizeSmall = document.createElement('small');

    nameSpan.textContent = file.name;
    sizeSmall.textContent = `${(file.size / 1024).toFixed(1)} KB`;

    item.appendChild(nameSpan);
    item.appendChild(sizeSmall);
    fileList.appendChild(item);
  });
}

function setStatus(message, type = 'info') {
  statusMessage.textContent = message;
  statusMessage.dataset.state = type;
}

function toggleProcessingState(isProcessing) {
  processButton.disabled = isProcessing;
  downloadButton.disabled = isProcessing;
  if (isProcessing) {
    processButton.textContent = 'Processando…';
    setStatus('Executando OCR e convertendo para Markdown, aguarde…', 'loading');
  } else {
    processButton.textContent = 'Converter para Markdown';
  }
}

function handleFiles(files) {
  selectedFiles = Array.from(files);
  renderFileList();
  if (selectedFiles.length) {
    setStatus(`${selectedFiles.length} arquivo(s) pronto(s) para conversão.`);
  }
}

fileInput.addEventListener('change', (event) => {
  handleFiles(event.target.files);
});

['dragenter', 'dragover'].forEach((type) => {
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    event.stopPropagation();
    dropzone.classList.add('is-dragover');
  });
});

['dragleave', 'drop'].forEach((type) => {
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    event.stopPropagation();
    dropzone.classList.remove('is-dragover');
  });
});

dropzone.addEventListener('drop', (event) => {
  if (event.dataTransfer?.files?.length) {
    handleFiles(event.dataTransfer.files);
  }
});

uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!selectedFiles.length) {
    setStatus('Selecione ao menos um arquivo para converter.', 'error');
    return;
  }

  const formData = new FormData();
  selectedFiles.forEach((file) => formData.append('files', file, file.name));

  toggleProcessingState(true);
  try {
    const response = await fetch('/api/process', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      const errorMessage = errorPayload.error || 'Erro ao processar os arquivos.';
      throw new Error(errorMessage);
    }

    const payload = await response.json();
    resultMarkdown.value = payload.markdown;
    lastFileName = payload.fileName || lastFileName;
    downloadButton.disabled = false;
    setStatus('Conversão concluída com sucesso! Faça o download do Markdown.', 'success');
  } catch (error) {
    console.error(error);
    setStatus(error.message || 'Erro inesperado durante a conversão.', 'error');
    resultMarkdown.value = '';
    downloadButton.disabled = true;
  } finally {
    toggleProcessingState(false);
  }
});

downloadButton.addEventListener('click', () => {
  if (!resultMarkdown.value) {
    return;
  }
  const blob = new Blob([resultMarkdown.value], { type: 'text/markdown;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = lastFileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
});

function toggleModal(show) {
  tourModal.hidden = !show;
  document.body.style.overflow = show ? 'hidden' : '';
}

tourButton.addEventListener('click', () => toggleModal(true));
modalClose.addEventListener('click', () => toggleModal(false));
tourModal.addEventListener('click', (event) => {
  if (event.target === tourModal) {
    toggleModal(false);
  }
});

renderFileList();
setStatus('Selecione arquivos para começar.');
