const express = require('express');
const sanitizeHtml = require('sanitize-html');
const cors = require('cors');

const app = express();
const port = 3010;

// Configure CORS
const corsOptions = {
  origin: ['https://allbeapi.top', 'https://res.allbeapi.top'], // Allow both origins
  methods: ['GET', 'POST', 'OPTIONS'], // Allow these methods
  allowedHeaders: ['Content-Type', 'Authorization'], // Allow these headers
  optionsSuccessStatus: 200, // some legacy browsers (IE11, various SmartTVs) choke on 204
  credentials: false // Explicitly set credentials
};

app.use(cors(corsOptions));
app.options('*', cors(corsOptions)); // Enable pre-flight requests for all routes

// Add explicit health check endpoint
app.get('/sanitize-html/health', (req, res) => {
  res.json({ status: 'ok', service: 'sanitize-html' });
});

app.use(express.json());

// Add logging middleware for debugging
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - Origin: ${req.get('Origin')}`);
    next();
});

// Sanitize HTML endpoint - both with and without prefix for flexibility
app.post('/sanitize-html', handleSanitizeRequest);


function handleSanitizeRequest(req, res) {
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
}

app.listen(port, () => {
    console.log(`Sanitize HTML API listening at http://localhost:${port}`);
});
