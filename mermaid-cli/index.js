const express = require('express');
const { MermaidAPI } = require('mermaid.cli');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const port = 3008;

app.use(express.json());

// Ensure the output directory exists
const outputDir = path.join(__dirname, 'output');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

app.post('/generate-diagram', async (req, res) => {
    const { definition, format } = req.body;

    if (!definition) {
        return res.status(400).json({ error: 'Missing definition in request body' });
    }
    const outputFormat = format || 'svg'; // Default to svg
    if (!['svg', 'png'].includes(outputFormat)) {
        return res.status(400).json({ error: 'Invalid format. Supported formats are svg and png.' });
    }

    const filename = `diagram-${uuidv4()}.${outputFormat}`;
    const outputPath = path.join(outputDir, filename);

    try {
        const { data } = await MermaidAPI.render(
            definition,
            { outputFormat },
        );
        fs.writeFileSync(outputPath, data);
        // Send the file path or the file itself depending on your needs
        // For simplicity, sending the path to the generated file
        // In a real application, you might want to serve this as a static file or return the image data directly
        res.json({ message: 'Diagram generated successfully', filePath: `/mermaid-cli/output/${filename}` });
    } catch (error) {
        console.error('Error generating diagram:', error);
        res.status(500).json({ error: 'Error generating diagram', details: error.message });
    }
});

// Serve static files from the output directory
app.use('/mermaid-cli/output', express.static(outputDir));

app.listen(port, () => {
    console.log(`Mermaid CLI API listening at http://localhost:${port}`);
});
