const express = require('express');
const csv = require('csv-parser');
const streamifier = require('streamifier');

const app = express();
const port = 3007;

app.use(express.json());

app.post('/csv-parser/csv-to-json', (req, res) => {
    const csvData = req.body.csv_data;
    if (!csvData) {
        return res.status(400).json({ error: 'Missing csv_data in request body' });
    }

    const results = [];
    streamifier.createReadStream(csvData)
        .pipe(csv())
        .on('data', (data) => results.push(data))
        .on('end', () => {
            res.json(results);
        })
        .on('error', (error) => {
            console.error('Error parsing CSV:', error);
            res.status(500).json({ error: 'Error parsing CSV' });
        });
});

app.listen(port, () => {
    console.log(`CSV Parser API listening at http://localhost:${port}`);
});
