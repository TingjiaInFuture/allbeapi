const express = require('express');
const { ESLint } = require('eslint');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const os = require('os');

const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' })); // Allow larger code snippets

// Basic ESLint configuration (can be extended)
const eslintConfig = {
    useEslintrc: false, // Don't look for .eslintrc files in the temp directory
    overrideConfig: {
        parserOptions: {
            ecmaVersion: 'latest',
            sourceType: 'module',
            ecmaFeatures: {
                jsx: true, // Enable JSX if needed
            },
        },
        env: {
            es6: true,
            node: true,
            browser: true, // Add browser environment for client-side JS
        },
        extends: ['eslint:recommended'], // Basic recommended rules
        rules: {
            // Add or override rules here if needed
            // e.g., "semi": ["error", "always"],
        },
    },
};

app.post('/eslint/lint', async (req, res) => {
    const { code, language, fix } = req.body;

    if (!code) {
        return res.status(400).json({ error: 'Code snippet is required' });
    }

    const fileExtension = language === 'typescript' ? '.ts' : '.js';
    const eslint = new ESLint({ ...eslintConfig, fix: fix === true });

    // Create a temporary file to lint
    // ESLint works best with files, especially for rules that depend on file context
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'eslint-api-'));
    const tempFilePath = path.join(tempDir, `tempfile${fileExtension}`);

    try {
        fs.writeFileSync(tempFilePath, code);

        const results = await eslint.lintFiles([tempFilePath]);

        let outputCode = code; // Default to original code
        if (fix && results[0] && results[0].output) {
            outputCode = results[0].output;
            // ESLint.outputFixes(results); // This would write fixes to disk if we weren't using a temp file for output
        }
        
        // Clean up the temporary file and directory
        fs.unlinkSync(tempFilePath);
        fs.rmdirSync(tempDir);

        res.status(200).json({ 
            results: results.map(r => ({
                filePath: r.filePath.substring(r.filePath.lastIndexOf(path.sep) + 1), // Show only temp filename
                messages: r.messages,
                errorCount: r.errorCount,
                warningCount: r.warningCount,
                fixableErrorCount: r.fixableErrorCount,
                fixableWarningCount: r.fixableWarningCount,
                source: r.source, // Original source
            })),
            fixedCode: fix ? outputCode : undefined
        });

    } catch (error) {
        console.error('ESLint Error:', error);
        if (fs.existsSync(tempFilePath)) fs.unlinkSync(tempFilePath); // Ensure cleanup on error
        if (fs.existsSync(tempDir)) fs.rmdirSync(tempDir);
        res.status(500).json({ error: 'Error during linting', details: error.message });
    }
});

const PORT = process.env.PORT || 5005;
app.listen(PORT, () => {
    console.log(`ESLint API server running on port ${PORT}`);
});
