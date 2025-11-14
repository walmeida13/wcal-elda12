const express = require('express');
const path = require('path');
const multer = require('multer');
const { docxToMarkdown, pdfToMarkdown, imageToMarkdownWithVision } = require('./conversion');

const app = express();

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.static(path.join(__dirname, '..', 'public')));

const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 10 * 1024 * 1024 } });

app.get('/api/health', (req, res) => {
  res.json({ ok: true, ts: Date.now(), app: 'wcal-elda12' });
});

app.post('/api/convert', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: 'Envie um arquivo em "file".' });

    const mime = req.file.mimetype || '';
    const name = req.file.originalname || 'arquivo';
    let md = '';

    if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || name.toLowerCase().endsWith('.docx')) {
      md = await docxToMarkdown(req.file.buffer);
    } else if (mime === 'application/pdf' || name.toLowerCase().endsWith('.pdf')) {
      md = await pdfToMarkdown(req.file.buffer);
    } else if (mime.startsWith('image/')) {
      md = await imageToMarkdownWithVision(req.file.buffer.toString('base64'), process.env.GOOGLE_VISION_API_KEY);
    } else {
      return res.status(415).json({ error: `Tipo não suportado: ${mime}` });
    }

    const out = name.replace(/\.[^.]+$/, '') + '.md';
    res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
    res.setHeader('Content-Disposition', `attachment; filename="${out}"`);
    res.send(md || '');
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: 'Falha na conversão', detail: String(e?.message || e) });
  }
});

module.exports = app;

if (!process.env.VERCEL) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log(`Dev: http://localhost:${port}`));
}
