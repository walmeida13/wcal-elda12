const Turndown = require('turndown');
const mammoth = require('mammoth');
const pdf = require('pdf-parse');

const td = new Turndown({ headingStyle: 'atx', codeBlockStyle: 'fenced' });

async function docxToMarkdown(buffer) {
  const { value: html } = await mammoth.convertToHtml({ buffer });
  return td.turndown(html || '');
}

async function pdfToMarkdown(buffer) {
  const data = await pdf(buffer).catch(() => ({ text: '' }));
  const text = (data.text || '').trim();
  if (!text) {
    return [
      '# PDF sem texto extraível',
      '',
      '> Parece digitalizado (imagem). Envie as páginas como PNG/JPG para OCR,',
      '> ou depois ativamos o fluxo de OCR de PDF via GCS.'
    ].join('\n');
  }
  return text.replace(/\r/g,'')
             .split('\n\n')
             .map(p=>p.trim()).filter(Boolean)
             .map(p=>p.replace(/\n/g,' '))
             .join('\n\n');
}

async function imageToMarkdownWithVision(base64, apiKey) {
  if (!apiKey) {
    return '# OCR não habilitado. Defina GOOGLE_VISION_API_KEY na Vercel.';
  }
  const fetch = (await import('node-fetch')).default;
  const body = { requests: [{ image: { content: base64 }, features: [{ type: 'DOCUMENT_TEXT_DETECTION' }] }] };
  const r = await fetch(`https://vision.googleapis.com/v1/images:annotate?key=${encodeURIComponent(apiKey)}`, {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
  });
  const j = await r.json();
  const text = j?.responses?.[0]?.fullTextAnnotation?.text || '';
  if (!text) return '# OCR não retornou texto';
  return text.trim().replace(/\r/g,'').split('\n\n').map(s=>s.trim()).filter(Boolean).join('\n\n');
}

module.exports = { docxToMarkdown, pdfToMarkdown, imageToMarkdownWithVision };
