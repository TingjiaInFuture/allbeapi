from flask import Flask, request, jsonify
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

def improved_language_detection(code, hint_language=None):
    """改进的语言检测功能"""
    # 如果提供了语言提示，优先使用
    if hint_language:
        try:
            return get_lexer_by_name(hint_language)
        except ClassNotFound:
            pass
    
    # 使用一些简单的启发式规则来改善检测
    code_lower = code.lower().strip()
    
    # Java检测
    if 'public class' in code and 'public static void main' in code:
        try:
            return get_lexer_by_name('java')
        except ClassNotFound:
            pass
    
    # C++检测
    if '#include <iostream>' in code or 'std::' in code:
        try:
            return get_lexer_by_name('cpp')
        except ClassNotFound:
            pass
    
    # C检测
    if '#include <stdio.h>' in code and 'printf' in code:
        try:
            return get_lexer_by_name('c')
        except ClassNotFound:
            pass
    
    # Python检测
    if re.search(r'def\s+\w+\s*\(', code) or 'import ' in code or 'from ' in code:
        try:
            return get_lexer_by_name('python')
        except ClassNotFound:
            pass
    
    # JavaScript检测
    if 'function ' in code or 'const ' in code or 'let ' in code or 'var ' in code:
        try:
            return get_lexer_by_name('javascript')
        except ClassNotFound:
            pass
    
    # SQL检测
    if any(keyword in code_lower for keyword in ['select ', 'create table', 'insert into', 'update ', 'delete from']):
        try:
            return get_lexer_by_name('sql')
        except ClassNotFound:
            pass
    
    # 最后尝试Pygments的自动检测
    try:
        return guess_lexer(code)
    except ClassNotFound:
        # 如果都失败了，返回文本lexer
        return get_lexer_by_name('text')

@app.route('/pygments/highlight', methods=['POST'])
def highlight_code():
    data = request.get_json()
    code = data.get('code')
    language = data.get('language')
    options = data.get('options', {})

    if not code or code.strip() == "":
        return jsonify({'error': 'Code snippet is required'}), 400

    try:
        if language:
            # 用户指定了语言
            lexer = get_lexer_by_name(language, **options)
        else:
            # 使用改进的自动检测
            lexer = improved_language_detection(code)
    except ClassNotFound:
        return jsonify({'error': f'Lexer for language "{language}" not found or language could not be guessed.'}), 400
    except Exception as e:
        return jsonify({'error': f'Error initializing lexer: {str(e)}'}), 500

    try:
        formatter = HtmlFormatter(style='default', linenos=False, cssclass='highlight')
        result = highlight(code, lexer, formatter)
        return jsonify({
            'highlighted_code': result, 
            'detected_language': lexer.name,
            'lexer_aliases': lexer.aliases,
            'code_length': len(code),
            'lines_count': len(code.split('\n'))
        })
    except Exception as e:
        return jsonify({'error': f'Error highlighting code: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
