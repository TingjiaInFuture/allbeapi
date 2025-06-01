addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const markedBaseUrl = 'https://marked-fycslzjgmg.cn-hongkong.fcapp.run'
  const beautifulsoupBaseUrl = 'https://beautifulsoup-njzzhjkxto.cn-beijing.fcapp.run'

  // 处理 Marked API 请求
  if (url.pathname === '/marked/render' && request.method === 'POST') {
    const targetUrl = new URL(markedBaseUrl + '/render')
    
    const headers = new Headers(request.headers)
    headers.delete('Host')
    for (let key of headers.keys()) {
      if (key.toLowerCase().startsWith('cf-')) {
        headers.delete(key)
      }
    }

    const newRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      redirect: 'follow'
    })

    try {
      const response = await fetch(newRequest)
      return response
    } catch (e) {
      return new Response('Error fetching from upstream: ' + e.message, { status: 500 })
    }
  }

  // 处理 Beautiful Soup API 请求
  if (url.pathname.startsWith('/beautifulsoup/') && request.method === 'POST') {
    const endpoint = url.pathname.replace('/beautifulsoup', '')
    const targetUrl = new URL(beautifulsoupBaseUrl + endpoint)
    
    const headers = new Headers(request.headers)
    headers.delete('Host')
    for (let key of headers.keys()) {
      if (key.toLowerCase().startsWith('cf-')) {
        headers.delete(key)
      }
    }

    const newRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: headers,
      body: request.body,
      redirect: 'follow'
    })

    try {
      const response = await fetch(newRequest)
      return response
    } catch (e) {
      return new Response('Error fetching from Beautiful Soup API: ' + e.message, { status: 500 })
    }
  }

  return new Response('Not found or invalid method', { status: 404 })
}
