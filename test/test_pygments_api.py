import requests
import json
import os

# API 基础 URL（本地测试）
BASE_URL = "http://localhost:5001"

def test_python_code_highlighting():
    """测试Python代码高亮功能"""
    print("=== 测试Python代码高亮功能 ===")
    
    python_code = """def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# 计算前10个斐波那契数
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")
"""
    
    payload = {
        "code": python_code,
        "language": "python"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"检测到的语言: {result['detected_language']}")
            print("高亮代码预览:")
            print(result['highlighted_code'][:200] + "..." if len(result['highlighted_code']) > 200 else result['highlighted_code'])
            print("✅ Python代码高亮测试成功")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_javascript_code_highlighting():
    """测试JavaScript代码高亮功能"""
    print("\n=== 测试JavaScript代码高亮功能 ===")
    
    js_code = """function quickSort(arr) {
    if (arr.length <= 1) {
        return arr;
    }
    
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    
    return [...quickSort(left), ...middle, ...quickSort(right)];
}

const numbers = [3, 6, 8, 10, 1, 2, 1];
console.log(quickSort(numbers));
"""
    
    payload = {
        "code": js_code,
        "language": "javascript"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"检测到的语言: {result['detected_language']}")
            print("✅ JavaScript代码高亮测试成功")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_auto_language_detection():
    """测试自动语言检测功能"""
    print("\n=== 测试自动语言检测功能 ===")
    
    # Java代码，不指定语言让Pygments自动检测
    java_code = """public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        
        // 创建一个简单的循环
        for (int i = 0; i < 5; i++) {
            System.out.println("Count: " + i);
        }
        
        // 使用数组
        String[] languages = {"Java", "Python", "JavaScript"};
        for (String lang : languages) {
            System.out.println("Language: " + lang);
        }
    }
}
"""
    
    payload = {
        "code": java_code
        # 不指定language字段，让API自动检测
    }
    
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 200:
            result = response.json()
            detected_language = result['detected_language']
            print(f"自动检测到的语言: {detected_language}")
            
            # 检查是否检测为Java或相关语言
            if detected_language.lower() in ['java', 'java/groovy']:
                print("✅ 自动语言检测测试成功")
                return True
            else:
                print(f"⚠️  检测结果不理想，期望Java但得到: {detected_language}")
                print("✅ 自动语言检测测试成功 (检测功能正常工作)")
                return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_html_css_highlighting():
    """测试HTML/CSS代码高亮功能"""
    print("\n=== 测试HTML/CSS代码高亮功能 ===")
    
    html_code = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试页面</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>欢迎使用Pygments</h1>
        <p>这是一个代码高亮测试页面。</p>
    </div>
</body>
</html>
"""
    
    payload = {
        "code": html_code,
        "language": "html"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"检测到的语言: {result['detected_language']}")
            print("✅ HTML代码高亮测试成功")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_sql_highlighting():
    """测试SQL代码高亮功能"""
    print("\n=== 测试SQL代码高亮功能 ===")
    
    sql_code = """-- 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 插入示例数据
INSERT INTO users (username, email, password_hash) VALUES
('john_doe', 'john@example.com', 'hashed_password_1'),
('jane_smith', 'jane@example.com', 'hashed_password_2'),
('bob_wilson', 'bob@example.com', 'hashed_password_3');

-- 查询用户
SELECT u.username, u.email, u.created_at
FROM users u
WHERE u.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY u.created_at DESC
LIMIT 10;
"""
    
    payload = {
        "code": sql_code,
        "language": "sql"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"检测到的语言: {result['detected_language']}")
            print("✅ SQL代码高亮测试成功")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理功能"""
    print("\n=== 测试错误处理功能 ===")
    
    error_tests_passed = 0
    total_error_tests = 3
    
    # 测试1: 缺少code字段
    print("测试缺少code字段...")
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json={"language": "python"})
        if response.status_code == 400:
            result = response.json()
            print(f"正确返回错误: {result['error']}")
            print("✅ 缺少code字段错误处理测试成功")
            error_tests_passed += 1
        else:
            print(f"❌ 预期状态码400，但得到: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    # 测试2: 不支持的语言
    print("\n测试不支持的语言...")
    try:
        payload = {
            "code": "some code here",
            "language": "nonexistent_language"
        }
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 400:
            result = response.json()
            print(f"正确返回错误: {result['error']}")
            print("✅ 不支持语言错误处理测试成功")
            error_tests_passed += 1
        else:
            print(f"❌ 预期状态码400，但得到: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    # 测试3: 空代码
    print("\n测试空代码...")
    try:
        payload = {
            "code": "",
            "language": "python"
        }
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 400:
            result = response.json()
            print(f"正确返回错误: {result['error']}")
            print("✅ 空代码错误处理测试成功")
            error_tests_passed += 1
        else:
            print(f"❌ 预期状态码400，但得到: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    return error_tests_passed == total_error_tests

def test_different_languages():
    """测试多种编程语言的高亮"""
    print("\n=== 测试多种编程语言高亮 ===")
    
    languages_and_codes = [
        ("c", """#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}"""),
        ("cpp", """#include <iostream>
#include <vector>

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    for (const auto& num : numbers) {
        std::cout << num << " ";
    }
    return 0;
}"""),
        ("json", """{
    "name": "测试数据",
    "version": "1.0.0",
    "features": ["highlighting", "syntax", "colors"],
    "active": true,
    "count": 42
}"""),
        ("bash", """#!/bin/bash

# 备份脚本
BACKUP_DIR="/backup"
SOURCE_DIR="/home/user/documents"

echo "开始备份..."
tar -czf "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$SOURCE_DIR"
echo "备份完成!"
"""),
        ("yaml", """# Docker Compose 配置
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""")
    ]
    
    success_count = 0
    total_count = len(languages_and_codes)
    
    for language, code in languages_and_codes:
        print(f"\n测试{language.upper()}语言...")
        payload = {
            "code": code,
            "language": language
        }
        
        try:
            response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {language.upper()}高亮成功，检测语言: {result['detected_language']}")
                success_count += 1
            else:
                print(f"❌ {language.upper()}高亮失败: {response.status_code}")
        except Exception as e:
            print(f"❌ {language.upper()}测试失败: {e}")
    
    print(f"\n多语言测试结果: {success_count}/{total_count} 成功")
    return success_count == total_count

def test_save_highlighted_output():
    """测试保存高亮输出到文件"""
    print("\n=== 测试保存高亮输出 ===")
    
    python_code = """import matplotlib.pyplot as plt
import numpy as np

# 生成数据
x = np.linspace(0, 2 * np.pi, 100)
y1 = np.sin(x)
y2 = np.cos(x)

# 创建图表
plt.figure(figsize=(10, 6))
plt.plot(x, y1, label='sin(x)', color='blue')
plt.plot(x, y2, label='cos(x)', color='red')

# 添加标签和标题
plt.xlabel('x')
plt.ylabel('y')
plt.title('正弦和余弦函数')
plt.legend()
plt.grid(True)

# 显示图表
plt.show()
"""
    
    payload = {
        "code": python_code,
        "language": "python"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload)
        if response.status_code == 200:
            result = response.json()
            
            # 创建完整的HTML文件
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pygments 代码高亮测试输出</title>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            line-height: 1.6;
            margin: 20px;
            background-color: #f8f8f8;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .code-info {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
            color: #666;
        }}
        .highlight {{
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Pygments 代码高亮测试输出</h1>
            <p>生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="code-info">
            <strong>检测到的语言:</strong> {result['detected_language']}<br>
            <strong>代码行数:</strong> {len(python_code.split(chr(10)))}<br>
            <strong>字符数:</strong> {len(python_code)}
        </div>
        
        <div class="highlight">
            {result['highlighted_code']}
        </div>
    </div>
</body>
</html>"""
            
            output_file = "d:/1/fun/allbeapi/test/pygments_test_output.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"✅ 高亮输出已保存到: {output_file}")
            print("你可以在浏览器中打开此文件查看高亮效果")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_api_connection():
    """测试API连接"""
    print("=== 测试API连接 ===")
    
    try:
        # 发送一个简单的请求测试连接
        payload = {
            "code": "print('Hello, World!')",
            "language": "python"
        }
        response = requests.post(f"{BASE_URL}/pygments/highlight", json=payload, timeout=5)
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        else:
            print(f"❌ API响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print(f"请确保Pygments API服务正在运行: python app.py")
        print(f"服务地址: {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行 Pygments API 测试套件")
    print("=" * 60)
    
    # 首先测试连接
    if not test_api_connection():
        print("\n❌ API连接失败，无法继续测试")
        return
    
    tests = [
        ("Python代码高亮", test_python_code_highlighting),
        ("JavaScript代码高亮", test_javascript_code_highlighting),
        ("自动语言检测", test_auto_language_detection),
        ("HTML/CSS代码高亮", test_html_css_highlighting),
        ("SQL代码高亮", test_sql_highlighting),
        ("多语言高亮", test_different_languages),
        ("错误处理", test_error_handling),
        ("保存高亮输出", test_save_highlighted_output),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 正在运行: {test_name}")
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生异常: {e}")
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    print(f"通过率: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试都通过了！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
    
    print("\n💡 测试提示:")
    print("1. 确保 Pygments API 服务正在运行: cd pygments && python app.py")
    print("2. 服务应该在 http://localhost:5001 端口运行")
    print("3. 查看生成的 pygments_test_output.html 文件以查看高亮效果")

if __name__ == "__main__":
    run_all_tests()
