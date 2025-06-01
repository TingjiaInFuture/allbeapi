const express = require('express');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');
const cors = require('cors');

const app = express();
const ajv = new Ajv({ allErrors: true });
addFormats(ajv); // Add support for formats like date-time, email, etc.

app.use(cors());
app.use(express.json());

app.post('/validate', (req, res) => {
    const { schema, data } = req.body;

    if (!schema) {
        return res.status(400).json({ error: 'Schema is required' });
    }
    if (data === undefined) { // data can be null, which is a valid JSON value
        return res.status(400).json({ error: 'Data is required' });
    }

    try {
        const validate = ajv.compile(schema);
        const valid = validate(data);

        if (!valid) {
            res.status(400).json({ valid: false, errors: validate.errors });
        } else {
            res.status(200).json({ valid: true });
        }
    } catch (error) {
        // Catch compilation errors (e.g., invalid schema)
        res.status(400).json({ error: 'Invalid schema or compilation error', details: error.message, ajvErrors: error.errors });
    }
});

const PORT = process.env.PORT || 5004;
app.listen(PORT, () => {
    console.log(`Ajv API server running on port ${PORT}`);
});
