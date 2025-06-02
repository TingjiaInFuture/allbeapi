const express = require('express');
const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const port = 3009;

app.use(express.json());

// Ensure the output directory exists
const outputDir = path.join(__dirname, 'output');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

app.post('/pdfkit/generate-pdf', (req, res) => {
    const { text_content } = req.body;

    if (!text_content) {
        return res.status(400).json({ error: 'Missing text_content in request body' });
    }

    const filename = `document-${uuidv4()}.pdf`;
    const outputPath = path.join(outputDir, filename);

    try {
        const doc = new PDFDocument();
        const stream = fs.createWriteStream(outputPath);
        doc.pipe(stream);

        // Add content to the PDF
        doc.fontSize(12).text(text_content, {
            align: 'left'
        });

        doc.end();

        stream.on('finish', () => {
            res.json({ message: 'PDF generated successfully', filePath: `/pdfkit/output/${filename}` });
        });

        stream.on('error', (err) => {
            console.error('Error writing PDF to stream:', err);
            res.status(500).json({ error: 'Error generating PDF' });
        });

    } catch (error) {
        console.error('Error generating PDF:', error);
        res.status(500).json({ error: 'Error generating PDF', details: error.message });
    }
});

// Serve static files from the output directory
app.use('/pdfkit/output', express.static(outputDir));

app.listen(port, () => {
    console.log(`PDFKit API listening at http://localhost:${port}`);
});
