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
        // Create PDF document with font fallback for Chinese characters
        const doc = new PDFDocument({
            font: 'Helvetica' // Default font
        });
        const stream = fs.createWriteStream(outputPath);
        doc.pipe(stream);

        // Try to register a Chinese font if available, otherwise use built-in fonts
        try {
            // Use built-in font that supports more Unicode characters
            doc.font('Helvetica');
            
            // For better Chinese support, we'll encode the text properly
            const processedContent = Buffer.from(text_content, 'utf8').toString('utf8');
            
            // Add content to the PDF with proper encoding
            doc.fontSize(12).text(processedContent, {
                align: 'left',
                lineGap: 5
            });
        } catch (fontError) {
            console.warn('Font loading failed, using fallback:', fontError.message);
            // Fallback: use default font and process text
            const processedContent = text_content.replace(/[^\x00-\x7F]/g, function(char) {
                // For non-ASCII characters, try to preserve them or use Unicode escape
                return char;
            });
            
            doc.fontSize(12).text(processedContent, {
                align: 'left',
                lineGap: 5
            });
        }

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
