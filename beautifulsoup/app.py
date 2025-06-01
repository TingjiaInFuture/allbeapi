from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup, Comment
import requests
from urllib.parse import urljoin, urlparse


app = Flask(__name__)
CORS(app)  # 启用CORS支持

@app.route('/beautifulsoup/parse', methods=['POST'])
def parse_html():
    """
    解析HTML内容
    请求体: {
        "html": "HTML字符串",
        "parser": "html.parser" (可选，默认为html.parser)
    }
    """
    try:
        data = request.get_json()
        html_content = data.get('html')
        parser = data.get('parser', 'html.parser')
        
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400
        
        soup = BeautifulSoup(html_content, parser)
        
        return jsonify({
            'title': soup.title.string if soup.title else None,
            'text': soup.get_text().strip(),
            'html': str(soup)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/beautifulsoup/extract', methods=['POST'])
def extract_elements():
    """
    从HTML中提取特定元素
    请求体: {
        "html": "HTML字符串",
        "selector": "CSS选择器或标签名",
        "attribute": "属性名" (可选),
        "parser": "html.parser" (可选)
    }
    """
    try:
        data = request.get_json()
        html_content = data.get('html')
        selector = data.get('selector')
        attribute = data.get('attribute')
        parser = data.get('parser', 'html.parser')
        
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400
        if not selector:
            return jsonify({'error': 'Selector is required'}), 400
        
        soup = BeautifulSoup(html_content, parser)
        
        # 尝试CSS选择器，如果失败则作为标签名处理
        try:
            elements = soup.select(selector)
        except:
            elements = soup.find_all(selector)
        
        result = []
        for element in elements:
            if attribute:
                value = element.get(attribute)
                if value:
                    result.append(value)
            else:
                result.append({
                    'tag': element.name,
                    'text': element.get_text().strip(),
                    'html': str(element),
                    'attributes': dict(element.attrs) if hasattr(element, 'attrs') else {}
                })
        
        return jsonify({'elements': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/beautifulsoup/links', methods=['POST'])
def extract_links():
    """
    提取所有链接
    请求体: {
        "html": "HTML字符串",
        "base_url": "基础URL" (可选，用于转换相对链接),
        "parser": "html.parser" (可选)
    }
    """
    try:
        data = request.get_json()
        html_content = data.get('html')
        base_url = data.get('base_url')
        parser = data.get('parser', 'html.parser')
        
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400
        
        soup = BeautifulSoup(html_content, parser)
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url:
                href = urljoin(base_url, href)
            
            links.append({
                'url': href,
                'text': link.get_text().strip(),
                'title': link.get('title', ''),
                'target': link.get('target', '')
            })
        
        return jsonify({'links': links})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/beautifulsoup/images', methods=['POST'])
def extract_images():
    """
    提取所有图片
    请求体: {
        "html": "HTML字符串",
        "base_url": "基础URL" (可选，用于转换相对链接),
        "parser": "html.parser" (可选)
    }
    """
    try:
        data = request.get_json()
        html_content = data.get('html')
        base_url = data.get('base_url')
        parser = data.get('parser', 'html.parser')
        
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400
        
        soup = BeautifulSoup(html_content, parser)
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if base_url and src:
                src = urljoin(base_url, src)
            
            images.append({
                'src': src,
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
        
        return jsonify({'images': images})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/beautifulsoup/clean', methods=['POST'])
def clean_html():
    """
    清理HTML内容
    请求体: {
        "html": "HTML字符串",
        "remove_tags": ["script", "style"] (可选，要移除的标签),
        "keep_only": ["p", "div", "span"] (可选，只保留的标签),
        "remove_comments": true (可选，是否移除注释),
        "parser": "html.parser" (可选)
    }
    """
    try:
        data = request.get_json()
        html_content = data.get('html')
        remove_tags = data.get('remove_tags', [])
        keep_only = data.get('keep_only', [])
        remove_comments = data.get('remove_comments', False)
        parser = data.get('parser', 'html.parser')
        
        if not html_content:
            return jsonify({'error': 'HTML content is required'}), 400
        
        soup = BeautifulSoup(html_content, parser)
        
        # 移除指定标签
        for tag_name in remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 只保留指定标签
        if keep_only:
            for tag in soup.find_all():
                if tag.name not in keep_only:
                    tag.unwrap()
        
        # 移除注释
        if remove_comments:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
        
        return jsonify({
            'html': str(soup),
            'text': soup.get_text().strip()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/beautifulsoup/fetch', methods=['POST'])
def fetch_and_parse():
    """
    获取网页并解析
    请求体: {
        "url": "网页URL",
        "selector": "CSS选择器" (可选),
        "parser": "html.parser" (可选)
    }
    """
    try:
        data = request.get_json()
        url = data.get('url')
        selector = data.get('selector')
        parser = data.get('parser', 'html.parser')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # 添加User-Agent避免被拒绝
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, parser)
        
        result = {
            'url': url,
            'title': soup.title.string if soup.title else None,
            'text': soup.get_text().strip()
        }
        
        if selector:
            try:
                elements = soup.select(selector)
                result['selected'] = [str(elem) for elem in elements]
            except:
                elements = soup.find_all(selector)
                result['selected'] = [str(elem) for elem in elements]
        
        return jsonify(result)
    
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/beautifulsoup/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'service': 'beautifulsoup-api'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
