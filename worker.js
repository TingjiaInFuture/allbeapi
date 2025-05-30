addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const targetBaseUrl = 'https://marked-api-cewxmsxevb.cn-hangzhou.fcapp.run'

  if (url.pathname === '/marked/render' && request.method === 'POST') { // 检查请求方法是否为 POST
    const targetUrl = new URL(targetBaseUrl + '/render')

    // 复制请求头，移除 Host 和 CF-* headers
    const headers = new Headers(request.headers)
    headers.delete('Host')
    // Cloudflare 可能会添加一些自己的 headers，通常最好移除它们以避免目标服务器混淆
    for (let key of headers.keys()) {
      if (key.toLowerCase().startsWith('cf-')) {
        headers.delete(key)
      }
    }
    
    // 如果有需要，可以添加特定的 header 到目标请求
    // headers.set('X-My-Custom-Header', 'some-value');

    const newRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      redirect: 'follow' // 或者 'manual' 或 'error'，根据需要
    })

    try {
      const response = await fetch(newRequest)
      return response
    } catch (e) {
      return new Response('Error fetching from upstream: ' + e.message, { status: 500 })
    }
  }

  return new Response('Not found or invalid method', { status: 404 }) // 更新默认响应
}
