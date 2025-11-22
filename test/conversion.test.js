const test = require('node:test');
const assert = require('node:assert/strict');

const { pdfToMarkdown, imageToMarkdownWithVision } = require('../src/conversion');

// Even though the buffer begins like a PDF, pdf-parse will fail because it's incomplete.
const BROKEN_PDF_BUFFER = Buffer.from('%PDF-1.4\n1 0 obj\n<<>>\nendobj');

test('pdfToMarkdown falls back to guidance message when text is not extractable', async () => {
  const markdown = await pdfToMarkdown(BROKEN_PDF_BUFFER, async () => ({ text: '' }));
  assert.ok(markdown.includes('# PDF sem texto extraível'));
  assert.ok(markdown.includes('Parece digitalizado'));
});

test('imageToMarkdownWithVision returns message when API key is missing', async () => {
  const markdown = await imageToMarkdownWithVision('Zm9v', '');
  assert.strictEqual(markdown, '# OCR não habilitado. Defina GOOGLE_VISION_API_KEY na Vercel.');
});

test('imageToMarkdownWithVision normalises text blocks from Vision API responses', async () => {
  const fakeFetch = async () => ({
    ok: true,
    json: async () => ({
      responses: [
        {
          fullTextAnnotation: {
            text: 'Linha 1\nLinha 2\n\nLinha 3'
          }
        }
      ]
    })
  });

  const markdown = await imageToMarkdownWithVision('Zm9v', 'test-key', fakeFetch);
  assert.strictEqual(markdown, 'Linha 1\nLinha 2\n\nLinha 3');
});

test('imageToMarkdownWithVision surfaces Vision API HTTP errors', async () => {
  const fakeFetch = async () => ({
    ok: false,
    status: 403,
    text: async () => 'forbidden'
  });

  await assert.rejects(
    () => imageToMarkdownWithVision('Zm9v', 'test-key', fakeFetch),
    /Vision API retornou 403: forbidden/
  );
});
