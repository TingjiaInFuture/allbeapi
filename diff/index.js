const express = require('express');
const Diff = require('diff');
const cors = require('cors');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const app = express();
app.use(cors());
app.use(express.json({ limit: '5mb' }));

// Function to create an HTML representation of the diff
function createHtmlDiff(diffResult) {
    const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
    const document = dom.window.document;
    const pre = document.createElement('pre');
    pre.style.fontFamily = "monospace";
    pre.style.whiteSpace = "pre-wrap";

    diffResult.forEach(part => {
        const span = document.createElement('span');
        span.textContent = part.value;
        if (part.added) {
            span.style.backgroundColor = '#e6ffed';
            span.style.color = '#22863a';
            span.style.fontWeight = 'bold';
        } else if (part.removed) {
            span.style.backgroundColor = '#ffeef0';
            span.style.color = '#b31d28';
            span.style.textDecoration = 'line-through';
        } else {
            span.style.color = '#586069'; // Neutral color for unchanged parts
        }
        pre.appendChild(span);
    });
    return pre.outerHTML;
}

app.post('/compare', (req, res) => {
    const { text1, text2, type, outputFormat } = req.body;

    if (text1 === undefined || text2 === undefined) {
        return res.status(400).json({ error: 'Both text1 and text2 are required' });
    }
    if (!type) {
        return res.status(400).json({ error: 'Comparison type is required (e.g., chars, words, lines, json)' });
    }

    let diffResult;
    try {
        switch (type) {
            case 'chars':
                diffResult = Diff.diffChars(String(text1), String(text2));
                break;
            case 'words':
                diffResult = Diff.diffWords(String(text1), String(text2));
                break;
            case 'wordsWithSpace':
                diffResult = Diff.diffWordsWithSpace(String(text1), String(text2));
                break;
            case 'lines':
                diffResult = Diff.diffLines(String(text1), String(text2));
                break;
            case 'trimmedLines':
                 diffResult = Diff.diffTrimmedLines(String(text1), String(text2));
                break;
            case 'sentences':
                diffResult = Diff.diffSentences(String(text1), String(text2));
                break;
            case 'css':
                diffResult = Diff.diffCss(String(text1), String(text2));
                break;
            case 'json':
                // For JSON, we compare the objects. The diff will show changes in the stringified version.
                // For a more structured JSON diff, a specialized JSON diff library would be better.
                diffResult = Diff.diffJson(typeof text1 === 'string' ? JSON.parse(text1) : text1, 
                                         typeof text2 === 'string' ? JSON.parse(text2) : text2);
                break;
            default:
                return res.status(400).json({ error: 'Invalid comparison type' });
        }
    } catch (e) {
        if (type === 'json' && e instanceof SyntaxError) {
            return res.status(400).json({ error: 'Invalid JSON input for json diff type', details: e.message });
        }
        return res.status(500).json({ error: 'Error performing diff', details: e.message });
    }

    if (outputFormat === 'html') {
        const htmlDiff = createHtmlDiff(diffResult);
        res.status(200).json({ diff: htmlDiff, format: 'html' });
    } else if (outputFormat === 'patch') {
        // Create a patch (unified diff format)
        // Note: createPatch/createTwoFilesPatch needs file headers, old/new file content, and options.
        // For simplicity, we'll use a basic patch representation here.
        // For a full patch, you might need more context or specific diff functions.
        const patch = Diff.createPatch('file', String(text1), String(text2)); // Basic patch
        res.status(200).json({ diff: patch, format: 'patch' });
    } else {
        // Default to JSON array of changes
        res.status(200).json({ diff: diffResult, format: 'json_array' });
    }
});

const PORT = process.env.PORT || 5006;
app.listen(PORT, () => {
    console.log(`Diff API server running on port ${PORT}`);
});
