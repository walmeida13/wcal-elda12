const express = require('express');
const path = require('path');

const app = express();

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Servir arquivos estáticos da pasta public/
app.use(express.static(path.join(__dirname, '..', 'public')));

// Healthcheck
app.get('/api/health', (req, res) => {
  res.json({ ok: true, ts: Date.now(), app: 'wcal-elda12' });
});

// (gancho para futura rota de conversão)
// app.post('/api/convert', (req, res) => { res.json({ ok: true }); });

module.exports = app;

// Em dev local apenas
if (!process.env.VERCEL) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log(`Dev: http://localhost:${port}`));
}
