import requests
import json

# API 基础 URL（本地测试）
BASE_URL = "http://localhost:3001"

def test_format_javascript():
    """测试JavaScript代码格式化"""
    print("=== 测试JavaScript代码格式化 ===")
    
    messy_js_code = """
const x={a:1,b:2,c:function(){console.log("hello");}};
if(x.a==1){console.log('yes');}else{console.log('no');}
    """
    
    payload = {
        "code": messy_js_code,
        "parser": "babel",
        "options": {
            "singleQuote": True,
            "semi": False,
            "printWidth": 80
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/prettier/format", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ 格式化成功!")
            print("原始代码:")
            print(messy_js_code)
            print("\n格式化后:")
            print(data['formatted'])
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def test_format_html():
    """测试HTML代码格式化"""
    print("\n=== 测试HTML代码格式化 ===")
    
    messy_html = """<div><p>Hello</p><span>World</span></div>"""
    
    payload = {
        "code": messy_html,
        "parser": "html",
        "options": {
            "printWidth": 80,
            "tabWidth": 2
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/prettier/format", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ HTML格式化成功!")
            print("原始代码:")
            print(messy_html)
            print("\n格式化后:")
            print(data['formatted'])
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def test_format_json():
    """测试JSON格式化"""
    print("\n=== 测试JSON格式化 ===")
    
    messy_json = """{"name":"test","data":{"items":[1,2,3],"active":true}}"""
    
    payload = {
        "code": messy_json,
        "parser": "json",
        "options": {
            "printWidth": 40
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/prettier/format", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ JSON格式化成功!")
            print("原始代码:")
            print(messy_json)
            print("\n格式化后:")
            print(data['formatted'])
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def test_check_format():
    """测试代码格式检查"""
    print("\n=== 测试代码格式检查 ===")
    
    # 测试已格式化的代码
    formatted_code = """const x = {
  a: 1,
  b: 2,
  c: function () {
    console.log("hello");
  },
};
"""
    
    # 测试未格式化的代码
    unformatted_code = "const x={a:1,b:2};"
    
    for code, description in [(formatted_code, "已格式化"), (unformatted_code, "未格式化")]:
        payload = {
            "code": code,
            "parser": "babel"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/prettier/check", json=payload)
            if response.status_code == 200:
                data = response.json()
                status = "✅" if data['isFormatted'] else "❌"
                print(f"{status} {description}代码检查: {data['message']}")
            else:
                print(f"❌ 请求失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 连接错误: {e}")

def test_batch_format():
    """测试批量格式化"""
    print("\n=== 测试批量格式化 ===")
    
    files = [
        {
            "name": "script.js",
            "code": "const x={a:1,b:2};",
            "parser": "babel"
        },
        {
            "name": "style.css",
            "code": "body{margin:0;padding:0;}",
            "parser": "css"
        },
        {
            "name": "data.json",
            "code": '{"key":"value","items":[1,2,3]}',
            "parser": "json"
        }
    ]
    
    payload = {
        "files": files,
        "options": {
            "singleQuote": True,
            "semi": False
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/prettier/batch", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ 批量格式化成功!")
            print(f"处理结果: 成功 {data['summary']['success']}, 失败 {data['summary']['failed']}")
            
            for result in data['results']:
                print(f"\n📄 {result['name']} ({result['parser']}):")
                print(result['formatted'][:100] + "..." if len(result['formatted']) > 100 else result['formatted'])
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def test_get_parsers():
    """测试获取支持的解析器"""
    print("\n=== 测试获取支持的解析器 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/prettier/parsers")
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功获取解析器列表:")
            for ext, parser in data['parsers'].items():
                print(f"  {ext} -> {parser}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/prettier/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ 服务健康状态:")
            print(f"  状态: {data['status']}")
            print(f"  版本: {data['version']}")
            print(f"  运行时间: {data['uptime']:.2f}秒")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接错误: {e}")

def test_api_info():
    """测试API信息"""
    print("\n=== 测试API信息 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/prettier/info")
        if response.status_code == 200:
            data = response.json()
            print("✅ API信息:")
            print(f"  服务名: {data['service']['name']}")
            print(f"  描述: {data['service']['description']}")
            print(f"  支持的语言: {', '.join(data['supportedLanguages'])}")
            print("  可用端点:")
            for endpoint, desc in data['endpoints'].items():
                print(f"    {endpoint}: {desc}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接错误: {e}")

if __name__ == "__main__":
    print("🎨 开始测试 Prettier API 服务")
    print("=" * 50)
    
    # 运行所有测试
    test_health_check()
    test_api_info()
    test_get_parsers()
    test_format_javascript()
    test_format_html()
    test_format_json()
    test_check_format()
    test_batch_format()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成!")
    print("\n💡 提示:")
    print("1. 确保 Prettier API 服务正在运行 (cd Prettier && npm start)")
    print("2. 如果测试失败，请检查服务是否在 http://localhost:3001 运行")
