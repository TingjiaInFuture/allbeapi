import requests
import json

# API 的 URL
url = "http://localhost:3000/marked/render"  # 指向本地 Node.js API 服务

# 要发送的 Markdown 数据
markdown_payload = {
    "markdown": "# 测试标题\n\n这是从 Python 脚本发送的 **Markdown** 内容。\n\n* 列表项 1\n* 列表项 2"
}

# 输出 HTML 文件的路径
output_html_file = "d:/1/fun/allbeapi/test/output.html"

print(f"向 {url} 发送 POST 请求...")

try:
    # 发送 POST 请求
    response = requests.post(url, json=markdown_payload)

    # 检查响应状态码
    if response.status_code == 200:
        print("请求成功！")
        html_output = response.text
        
        with open(output_html_file, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"转换后的 HTML 已保存到: {output_html_file}")
        
        print("\n部分 HTML 输出预览:")
        print(html_output[:200] + "..." if len(html_output) > 200 else html_output)
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print("响应内容:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"请求时发生错误: {e}")
    print(f"请确保您的 Node.js API 服务器 (在 d:\\1\\fun\\allbeapi\\marked 目录下运行 node index.js) 正在运行，并且地址 ({url}) 正确。")
