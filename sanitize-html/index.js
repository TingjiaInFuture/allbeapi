const express = require('express');
const sanitizeHtml = require('sanitize-html');
const cors = require('cors');

const app = express();
const port = 3010;

app.use(cors());
app.use(express.json());

app.post('/sanitize-html', (req, res) => {
    const { html_content, options } = req.body;

    if (html_content === undefined) { // html_content can be an empty string
        return res.status(400).json({ error: 'Missing html_content in request body' });
    }

    // Default sanitization options (very restrictive)
    let sanitizationOptions = {
        allowedTags: [],
        allowedAttributes: {},
    };

    // If user provides options, merge them or use them directly
    // For simplicity, this example uses provided options directly if they exist.
    // In a real app, you might want to merge or have more sophisticated option handling.
    if (options) {
        sanitizationOptions = options;
    }

    try {
        const cleanHtml = sanitizeHtml(html_content, sanitizationOptions);
        res.json({ sanitized_html: cleanHtml });
    } catch (error) {
        console.error('Error sanitizing HTML:', error);
        res.status(500).json({ error: 'Error sanitizing HTML', details: error.message });
    }
});

app.listen(port, () => {
    console.log(`Sanitize HTML API listening at http://localhost:${port}`);
});
