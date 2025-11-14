module.exports = (req, res) => {
  res.status(200).json({ ok: true, ts: Date.now(), app: 'wcal-elda12' });
};
