import requests
import json

# API 基础 URL（本地测试）
BASE_URL = "http://localhost:5000"

def test_parse_html():
    """测试HTML解析功能"""
    print("=== 测试HTML解析功能 ===")
    
    html_content = """
    <html>
        <head><title>测试页面</title></head>
        <body>
            <h1>标题</h1>
            <p>这是一个段落</p>
            <div class="content">
                <a href="https://example.com">链接</a>
                <img src="image.jpg" alt="图片">
            </div>
        </body>
    </html>
    """
    
    payload = {"html": html_content}
    
    try:
        response = requests.post(f"{BASE_URL}/parse", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"标题: {result['title']}")
            print(f"文本内容: {result['text'][:100]}...")
            print("✅ HTML解析测试成功")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_extract_elements():
    """测试元素提取功能"""
    print("\n=== 测试元素提取功能 ===")
    
    html_content = """
    <div>
        <h1>主标题</h1>
        <h2>副标题1</h2>
        <h2>副标题2</h2>
        <p class="intro">介绍段落</p>
        <p>普通段落</p>
    </div>
    """
    
    # 测试提取所有h2标签
    payload = {"html": html_content, "selector": "h2"}
    
    try:
        response = requests.post(f"{BASE_URL}/extract", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"找到 {len(result['elements'])} 个h2元素:")
            for elem in result['elements']:
                print(f"  - {elem['text']}")
            print("✅ 元素提取测试成功")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_extract_links():
    """测试链接提取功能"""
    print("\n=== 测试链接提取功能 ===")
    
    html_content = """
    <div>
        <a href="https://github.com">GitHub</a>
        <a href="/relative-link" title="相对链接">本站链接</a>
        <a href="mailto:test@example.com">邮箱</a>
    </div>
    """
    
    payload = {
        "html": html_content,
        "base_url": "https://example.com"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/links", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"找到 {len(result['links'])} 个链接:")
            for link in result['links']:
                print(f"  - {link['text']}: {link['url']}")
            print("✅ 链接提取测试成功")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_clean_html():
    """测试HTML清理功能"""
    print("\n=== 测试HTML清理功能 ===")
    
    html_content = """
    <html>
        <head>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <p>保留的内容</p>
            <div>保留的div</div>
            <!-- 这是注释 -->
        </body>
    </html>
    """
    
    payload = {
        "html": html_content,
        "remove_tags": ["script", "style"],
        "remove_comments": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/clean", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("清理后的HTML:")
            print(result['html'])
            print("✅ HTML清理测试成功")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            result = response.json()
            print(f"服务状态: {result['status']}")
            print("✅ 健康检查测试成功")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("Beautiful Soup API 测试")
    print("=" * 50)
    print("请确保API服务器正在运行 (python app.py)")
    print()
    
    # 先测试健康检查
    test_health_check()
    
    # 运行所有测试
    test_parse_html()
    test_extract_elements()
    test_extract_links()
    test_clean_html()
    
    print("\n" + "=" * 50)
    print("测试完成！")
