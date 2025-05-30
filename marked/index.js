const express = require('express');
const { marked } = require('marked');

const app = express();
const port = process.env.PORT || 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// API endpoint to render markdown
app.post('/render', (req, res) => {
  const { markdown } = req.body;

  if (typeof markdown !== 'string') {
    return res.status(400).json({ error: 'Markdown content must be a string.' });
  }

  try {
    const html = marked(markdown);
    res.send(html);
  } catch (error) {
    console.error('Error processing markdown:', error);
    res.status(500).json({ error: 'Failed to render markdown.' });
  }
});

app.listen(port, () => {
  console.log(`Marked API server listening at http://localhost:${port}`);
});
