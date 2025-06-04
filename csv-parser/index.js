const express = require('express');
const csv = require('csv-parser');
const streamifier = require('streamifier');

const app = express();
const port = 3007;

app.use(express.json());

// 健康检查端点
app.get('/csv-parser/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        service: 'CSV Parser API',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    });
});

// API信息端点
app.get('/csv-parser/info', (req, res) => {
    res.json({
        name: 'CSV Parser API',
        version: '1.0.0',
        description: 'API for parsing CSV data to JSON format',
        endpoints: {
            'POST /csv-parser/parse': 'Parse CSV data to JSON',
            'POST /csv-parser/csv-to-json': 'Parse CSV data to JSON (legacy endpoint)',
            'GET /csv-parser/health': 'Health check',
            'GET /csv-parser/info': 'API information'
        }
    });
});

// CSV 转 JSON 端点 - 保持向后兼容
app.post('/csv-parser/csv-to-json', (req, res) => {
    handleCsvToJson(req, res);
});

// 新的标准化端点
app.post('/csv-parser/parse', (req, res) => {
    handleCsvToJson(req, res);
});

// 处理CSV转JSON的共用函数
function handleCsvToJson(req, res) {
    const { csv_data, options = {} } = req.body;
    
    if (!csv_data) {
        return res.status(400).json({ 
            error: 'Missing csv_data in request body',
            example: {
                csv_data: "header1,header2\\nvalue1,value2\\nvalue3,value4",
                options: {
                    separator: ",",
                    skipEmptyLines: true,
                    headers: true
                }
            }
        });
    }

    const results = [];
    const csvOptions = {
        separator: options.separator || ',',
        skipEmptyLines: options.skipEmptyLines !== false,
        headers: options.headers !== false,
        ...options
    };

    streamifier.createReadStream(csv_data)
        .pipe(csv(csvOptions))
        .on('data', (data) => {
            results.push(data);
        })
        .on('end', () => {
            res.json({
                success: true,
                data: results,
                count: results.length,
                options_used: csvOptions
            });
        })
        .on('error', (error) => {
            console.error('Error parsing CSV:', error);
            res.status(500).json({ 
                success: false,
                error: 'Error parsing CSV',
                details: error.message,
                code: 'PARSE_ERROR'
            });
        });
}

app.listen(port, () => {
    console.log(`CSV Parser API listening at http://localhost:${port}`);
});
