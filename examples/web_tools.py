import asyncio
import httpx
from typing import Dict

async def fetch_website_content(url: str) -> Dict[str, str]:
    """
    异步获取网站内容。
    
    Args:
        url: 目标网址
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return {
            "status": str(resp.status_code),
            "content_preview": resp.text[:200]
        }

async def batch_process_tasks(count: int) -> str:
    """模拟耗时的异步任务"""
    print(f"Starting {count} tasks...")
    await asyncio.sleep(1) # 模拟耗时
    return f"Completed {count} tasks successfully."