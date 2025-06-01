const express = require('express');
const cors = require('cors');
const prettier = require('prettier');

const app = express();
const port = process.env.PORT || 3001;

// 中间件配置
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 支持的文件类型和对应的解析器
const SUPPORTED_PARSERS = {
  'javascript': 'babel',
  'js': 'babel',
  'jsx': 'babel',
  'typescript': 'typescript',
  'ts': 'typescript',
  'tsx': 'typescript',
  'json': 'json',
  'html': 'html',
  'css': 'css',
  'scss': 'scss',
  'less': 'less',
  'markdown': 'markdown',
  'md': 'markdown',
  'yaml': 'yaml',
  'yml': 'yaml',
  'xml': 'xml',
  'php': 'php',
  'java': 'java',
  'sql': 'sql'
};

// 默认配置
const DEFAULT_OPTIONS = {
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  semi: true,
  singleQuote: false,
  quoteProps: 'as-needed',
  trailingComma: 'es5',
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'always',
  endOfLine: 'lf'
};

/**
 * 主要的代码格式化端点
 * POST /prettier/format
 */
app.post('/prettier/format', async (req, res) => {
  try {
    const { code, parser, options = {}, filepath } = req.body;

    // 验证输入
    if (!code || typeof code !== 'string') {
      return res.status(400).json({
        error: 'Code content is required and must be a string',
        code: 'INVALID_INPUT'
      });
    }

    // 确定解析器
    let selectedParser = parser;
    if (!selectedParser && filepath) {
      const extension = filepath.split('.').pop().toLowerCase();
      selectedParser = SUPPORTED_PARSERS[extension];
    }

    if (!selectedParser) {
      return res.status(400).json({
        error: 'Parser must be specified or filepath must have a supported extension',
        supportedParsers: Object.keys(SUPPORTED_PARSERS),
        code: 'PARSER_REQUIRED'
      });
    }

    // 验证解析器
    if (!Object.values(SUPPORTED_PARSERS).includes(selectedParser)) {
      return res.status(400).json({
        error: `Unsupported parser: ${selectedParser}`,
        supportedParsers: Object.values(SUPPORTED_PARSERS),
        code: 'UNSUPPORTED_PARSER'
      });
    }

    // 合并配置选项
    const prettierOptions = {
      ...DEFAULT_OPTIONS,
      ...options,
      parser: selectedParser
    };

    // 格式化代码
    const formattedCode = await prettier.format(code, prettierOptions);

    res.json({
      success: true,
      formatted: formattedCode,
      parser: selectedParser,
      options: prettierOptions
    });

  } catch (error) {
    console.error('Prettier formatting error:', error);
    
    // 处理语法错误
    if (error.name === 'SyntaxError' || error.message.includes('SyntaxError')) {
      return res.status(400).json({
        error: 'Code contains syntax errors',
        details: error.message,
        code: 'SYNTAX_ERROR'
      });
    }

    res.status(500).json({
      error: 'Failed to format code',
      details: error.message,
      code: 'FORMATTING_ERROR'
    });
  }
});

/**
 * 检查代码格式是否符合Prettier规范
 * POST /prettier/check
 */
app.post('/prettier/check', async (req, res) => {
  try {
    const { code, parser, options = {}, filepath } = req.body;

    if (!code || typeof code !== 'string') {
      return res.status(400).json({
        error: 'Code content is required and must be a string',
        code: 'INVALID_INPUT'
      });
    }

    // 确定解析器
    let selectedParser = parser;
    if (!selectedParser && filepath) {
      const extension = filepath.split('.').pop().toLowerCase();
      selectedParser = SUPPORTED_PARSERS[extension];
    }

    if (!selectedParser) {
      return res.status(400).json({
        error: 'Parser must be specified or filepath must have a supported extension',
        code: 'PARSER_REQUIRED'
      });
    }

    // 合并配置选项
    const prettierOptions = {
      ...DEFAULT_OPTIONS,
      ...options,
      parser: selectedParser
    };

    // 检查格式
    const isFormatted = await prettier.check(code, prettierOptions);

    res.json({
      success: true,
      isFormatted,
      parser: selectedParser,
      message: isFormatted ? 'Code is already formatted' : 'Code needs formatting'
    });

  } catch (error) {
    console.error('Prettier check error:', error);
    res.status(500).json({
      error: 'Failed to check code format',
      details: error.message,
      code: 'CHECK_ERROR'
    });
  }
});

/**
 * 获取支持的解析器列表
 * GET /prettier/parsers
 */
app.get('/prettier/parsers', (req, res) => {
  res.json({
    success: true,
    parsers: SUPPORTED_PARSERS,
    supportedExtensions: Object.keys(SUPPORTED_PARSERS)
  });
});

/**
 * 获取默认配置选项
 * GET /prettier/options
 */
app.get('/prettier/options', (req, res) => {
  res.json({
    success: true,
    defaultOptions: DEFAULT_OPTIONS,
    availableOptions: {
      printWidth: 'number - 每行最大字符数',
      tabWidth: 'number - 制表符宽度',
      useTabs: 'boolean - 使用制表符而不是空格',
      semi: 'boolean - 在语句末尾添加分号',
      singleQuote: 'boolean - 使用单引号而不是双引号',
      quoteProps: 'string - 对象属性引号 (as-needed|consistent|preserve)',
      trailingComma: 'string - 尾随逗号 (none|es5|all)',
      bracketSpacing: 'boolean - 对象字面量括号间距',
      bracketSameLine: 'boolean - 多行HTML元素的>放在最后一行末尾',
      arrowParens: 'string - 箭头函数参数括号 (avoid|always)',
      endOfLine: 'string - 行尾符 (lf|crlf|cr|auto)'
    }
  });
});

/**
 * 批量格式化多个文件
 * POST /prettier/batch
 */
app.post('/prettier/batch', async (req, res) => {
  try {
    const { files, options = {} } = req.body;

    if (!files || !Array.isArray(files)) {
      return res.status(400).json({
        error: 'Files array is required',
        code: 'INVALID_INPUT'
      });
    }

    const results = [];
    const errors = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const { code, parser, filepath, name } = file;

      try {
        // 确定解析器
        let selectedParser = parser;
        if (!selectedParser && filepath) {
          const extension = filepath.split('.').pop().toLowerCase();
          selectedParser = SUPPORTED_PARSERS[extension];
        }

        if (!selectedParser) {
          errors.push({
            index: i,
            name: name || `file_${i}`,
            error: 'Parser could not be determined'
          });
          continue;
        }

        // 合并配置选项
        const prettierOptions = {
          ...DEFAULT_OPTIONS,
          ...options,
          parser: selectedParser
        };

        // 格式化代码
        const formattedCode = await prettier.format(code, prettierOptions);

        results.push({
          index: i,
          name: name || `file_${i}`,
          filepath: filepath || null,
          formatted: formattedCode,
          parser: selectedParser,
          success: true
        });

      } catch (error) {
        errors.push({
          index: i,
          name: name || `file_${i}`,
          error: error.message
        });
      }
    }

    res.json({
      success: true,
      results,
      errors,
      summary: {
        total: files.length,
        success: results.length,
        failed: errors.length
      }
    });

  } catch (error) {
    console.error('Batch formatting error:', error);
    res.status(500).json({
      error: 'Failed to process batch formatting',
      details: error.message,
      code: 'BATCH_ERROR'
    });
  }
});

/**
 * 健康检查端点
 * GET /prettier/health
 */
app.get('/prettier/health', (req, res) => {
  res.json({
    success: true,
    status: 'healthy',
    service: 'Prettier API',
    version: require('./package.json').version,
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

/**
 * API 信息端点
 * GET /prettier/info
 */
app.get('/prettier/info', (req, res) => {
  res.json({
    success: true,
    service: {
      name: 'Prettier API',
      description: 'Code formatting service using Prettier',
      version: require('./package.json').version
    },
    endpoints: {
      'POST /prettier/format': 'Format code using Prettier',
      'POST /prettier/check': 'Check if code is already formatted',
      'POST /prettier/batch': 'Format multiple files in batch',
      'GET /prettier/parsers': 'Get supported parsers and file extensions',
      'GET /prettier/options': 'Get available configuration options',
      'GET /prettier/health': 'Health check endpoint',
      'GET /prettier/info': 'API information'
    },
    supportedLanguages: Object.keys(SUPPORTED_PARSERS),
    examples: {
      format: {
        url: 'POST /prettier/format',
        body: {
          code: 'const x={a:1,b:2};',
          parser: 'babel',
          options: { singleQuote: true, semi: false }
        }
      },
      check: {
        url: 'POST /prettier/check',
        body: {
          code: 'const x = { a: 1, b: 2 };',
          parser: 'babel'
        }
      }
    }
  });
});

// 根路径重定向到信息页面
app.get('/', (req, res) => {
  res.redirect('/prettier/info');
});

// 错误处理中间件
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    details: error.message,
    code: 'INTERNAL_ERROR'
  });
});

// 404 处理
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    availableEndpoints: [
      'POST /prettier/format',
      'POST /prettier/check',
      'POST /prettier/batch',
      'GET /prettier/parsers',
      'GET /prettier/options',
      'GET /prettier/health',
      'GET /prettier/info'
    ],
    code: 'NOT_FOUND'
  });
});

// 启动服务器
app.listen(port, () => {
  console.log(`🎨 Prettier API server is running on http://localhost:${port}`);
  console.log(`📚 API documentation: http://localhost:${port}/prettier/info`);
  console.log(`💚 Health check: http://localhost:${port}/prettier/health`);
});

module.exports = app;
