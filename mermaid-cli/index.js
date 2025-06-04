const express = require('express');
const { exec } = require('child_process');
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

const puppeteerConfigPath = path.join(__dirname, 'puppeteer-config.json');

app.post('/mermaid-cli/generate-diagram', async (req, res) => {
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
    const inputFilename = `input-${uuidv4()}.mmd`;
    const inputPath = path.join(outputDir, inputFilename);

    try {
        // Write definition to temporary file
        fs.writeFileSync(inputPath, definition);
        
        // Use mermaid CLI to generate the diagram, now with puppeteer config
        const command = `npx mmdc -i "${inputPath}" -o "${outputPath}" -p "${puppeteerConfigPath}"`;
        
        await new Promise((resolve, reject) => {
            exec(command, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error generating diagram. Command: ${command}`);
                    console.error(`Stderr: ${stderr}`);
                    console.error(`Stdout: ${stdout}`);
                    console.error('Error object:', error); // Log the full error object on the server

                    // Attach more details to the error object for the client response
                    error.stderr = stderr;
                    error.stdout = stdout;
                    error.executedCommand = command;
                    reject(error);
                } else {
                    resolve();
                }
            });
        });

        // Clean up input file
        fs.unlinkSync(inputPath);
        
        res.json({ message: 'Diagram generated successfully', filePath: `/mermaid-cli/output/${filename}` });
    } catch (error) {
        console.error('Error generating diagram:', error);
        // Clean up input file if it exists
        if (fs.existsSync(inputPath)) {
            fs.unlinkSync(inputPath);
        }
        // Send more detailed error information
        res.status(500).json({
            error: 'Error generating diagram',
            details: error.message, // Original error message from exec
            stderr: error.stderr,
            stdout: error.stdout,
            command: error.executedCommand,
            exitCode: error.code
        });
    }
});

// Serve static files from the output directory
app.use('/mermaid-cli/output', express.static(outputDir));

app.listen(port, () => {
    console.log(`Mermaid CLI API listening at http://localhost:${port}`);
});
