from flask import Flask, request, jsonify
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/pygments/highlight', methods=['POST'])
def highlight_code():
    data = request.get_json()
    code = data.get('code')
    language = data.get('language')
    options = data.get('options', {})

    if not code:
        return jsonify({'error': 'Code snippet is required'}), 400

    try:
        if language:
            lexer = get_lexer_by_name(language, **options)
        else:
            lexer = guess_lexer(code, **options)
    except ClassNotFound:
        return jsonify({'error': f'Lexer for language "{language}" not found or language could not be guessed.'}), 400
    except Exception as e:
        return jsonify({'error': f'Error initializing lexer: {str(e)}'}), 500

    formatter = HtmlFormatter()
    result = highlight(code, lexer, formatter)
    return jsonify({'highlighted_code': result, 'detected_language': lexer.name})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
