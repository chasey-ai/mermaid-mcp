#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
渲染模块，负责将HTML内容渲染为PNG图像。
使用Playwright实现浏览器自动化和截图功能。
"""

import os
import logging
import asyncio
import base64
from typing import Optional
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

async def render_html_to_png(
    html_content: str,
    width: int = 800,
    height: int = 600,
    save_html: bool = True
) -> bytes:
    """
    将HTML内容渲染为PNG图像。
    
    Args:
        html_content: HTML内容字符串
        width: 截图宽度（像素）
        height: 截图高度（像素）
        save_html: 是否保存HTML文件（用于调试）
        
    Returns:
        PNG图像的二进制内容
    """
    logger.info(f"开始渲染HTML为PNG，尺寸: {width}x{height}")
    
    # 可选：保存HTML用于调试
    if save_html:
        import uuid
        html_path = os.path.join(STATIC_DIR, f"chart_{uuid.uuid4().hex}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"已保存HTML文件: {html_path}")
    
    # 使用Playwright渲染HTML并截图
    async with async_playwright() as p:
        # 启动浏览器
        browser_type = os.getenv("BROWSER_TYPE", "chromium")
        if browser_type == "firefox":
            browser = await p.firefox.launch(headless=True)
        elif browser_type == "webkit":
            browser = await p.webkit.launch(headless=True)
        else:  # 默认使用Chromium
            browser = await p.chromium.launch(headless=True)
        
        # 创建页面
        page = await browser.new_page()
        
        # 设置视口大小
        await page.set_viewport_size({"width": width, "height": height})
        
        try:
            # 设置内容并等待渲染完成
            await page.set_content(html_content, wait_until="networkidle")
            
            # 获取内容大小
            dimensions = await page.evaluate("""() => {
                const body = document.body;
                const html = document.documentElement;
                
                const width = Math.max(
                    body.scrollWidth, body.offsetWidth,
                    html.clientWidth, html.scrollWidth, html.offsetWidth
                );
                
                const height = Math.max(
                    body.scrollHeight, body.offsetHeight,
                    html.clientHeight, html.scrollHeight, html.offsetHeight
                );
                
                return { width, height };
            }""")
            
            # 调整视口以适应内容
            content_width = min(dimensions["width"], width * 2)  # 限制最大宽度
            content_height = min(dimensions["height"], height * 2)  # 限制最大高度
            
            # 如果内容小于最小尺寸，使用最小尺寸
            content_width = max(content_width, width)
            content_height = max(content_height, height)
            
            await page.set_viewport_size({"width": content_width, "height": content_height})
            
            # 截图
            screenshot_bytes = await page.screenshot(
                type="png",
                full_page=True,
                omit_background=True  # 透明背景
            )
            
            logger.info(f"渲染完成，图片尺寸: {content_width}x{content_height}")
            return screenshot_bytes
            
        except Exception as e:
            logger.error(f"渲染HTML时出错: {str(e)}", exc_info=True)
            # 尝试截取错误页面
            try:
                error_screenshot = await page.screenshot(type="png")
                return error_screenshot
            except:
                # 如果无法截图，返回简单错误消息的图像
                return _generate_error_image(str(e))
        finally:
            await browser.close()

def _generate_error_image(error_message: str) -> bytes:
    """生成一个包含错误消息的图像（备用方案）"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 创建一个带有错误消息的图像
        img = Image.new('RGB', (800, 400), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype("Arial", 16)
        except:
            font = ImageFont.load_default()
        
        # 绘制错误消息
        d.text((20, 20), f"渲染错误:\n{error_message}", fill=(255, 0, 0), font=font)
        
        # 保存为二进制数据
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except:
        # 如果上述方法失败，返回一个空白的1x1像素图像
        return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFdQJ+OwRXvQAAAABJRU5ErkJggg==") 