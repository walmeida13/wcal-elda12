let turndownInstance;
let mammothModule;
let pdfParseModule;

function requireOptional(moduleName) {
  try {
    return require(moduleName);
  } catch (error) {
    if (error?.code === 'MODULE_NOT_FOUND') {
      throw new Error(
        `Dependência ausente: instale "${moduleName}" executando npm install`
      );
    }
    throw error;
  }
}

function getTurndown() {
  if (!turndownInstance) {
    const Turndown = requireOptional('turndown');
    turndownInstance = new Turndown({ headingStyle: 'atx', codeBlockStyle: 'fenced' });
  }
  return turndownInstance;
}

function getMammoth() {
  if (!mammothModule) {
    mammothModule = requireOptional('mammoth');
  }
  return mammothModule;
}

function getPdfParse() {
  if (!pdfParseModule) {
    pdfParseModule = requireOptional('pdf-parse');
  }
  return pdfParseModule;
}

async function docxToMarkdown(buffer, overrides = {}) {
  const mammoth = overrides.mammoth || getMammoth();
  const td = overrides.turndown || getTurndown();

  const { value: html } = await mammoth.convertToHtml({ buffer });
  return td.turndown(html || '');
}

async function pdfToMarkdown(buffer, parser) {
  const parsePdf = parser || getPdfParse();

  const data = await parsePdf(buffer).catch(() => ({ text: '' }));
  const text = (data.text || '').trim();
  if (!text) {
    return [
      '# PDF sem texto extraível',
      '',
      '> Parece digitalizado (imagem). Envie páginas como PNG/JPG para OCR',
      '> ou ative o OCR automático de PDFs para continuar.'
    ].join('\n');
  }

  return text
    .replace(/\r/g, '')
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph) => paragraph.replace(/\s*\n\s*/g, ' '))
    .join('\n\n');
}

async function imageToMarkdownWithVision(base64, apiKey, fetchImpl) {
  if (!apiKey) {
    return '# OCR não habilitado. Defina GOOGLE_VISION_API_KEY na Vercel.';
  }

  const fetch = fetchImpl || (await import('node-fetch')).default;

  const body = {
    requests: [
      {
        image: { content: base64 },
        features: [{ type: 'DOCUMENT_TEXT_DETECTION' }]
      }
    ]
  };

  const response = await fetch(
    `https://vision.googleapis.com/v1/images:annotate?key=${encodeURIComponent(apiKey)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }
  );

  if (!response.ok) {
    const errorText = await safeReadBody(response);
    throw new Error(`Vision API retornou ${response.status}: ${errorText}`);
  }

  const payload = await response.json();
  const text = payload?.responses?.[0]?.fullTextAnnotation?.text || '';

  if (!text.trim()) {
    return '# OCR não retornou texto';
  }

  return text
    .trim()
    .replace(/\r/g, '')
    .split(/\n{2,}/)
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .join('\n\n');
}

async function safeReadBody(response) {
  try {
    return await response.text();
  } catch (error) {
    return '<sem corpo>';
  }
}

module.exports = { docxToMarkdown, pdfToMarkdown, imageToMarkdownWithVision };
