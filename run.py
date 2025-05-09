#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mermaid-MCP 启动脚本
用于启动MCP服务器并监听连接。
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# 导入服务器模块
from src.server import MermaidMCPServer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

async def main():
    """程序入口点"""
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "5000"))
    
    # 创建并启动服务器
    server = MermaidMCPServer()
    
    # 输出启动信息
    logger.info(f"启动 Mermaid-MCP 服务器...")
    logger.info(f"监听地址: {host}:{port}")
    logger.info(f"LLM提供商: {os.getenv('LLM_PROVIDER', 'anthropic')}")
    logger.info(f"浏览器类型: {os.getenv('BROWSER_TYPE', 'chromium')}")
    
    try:
        # 启动服务器
        await server.start(host=host, port=port)
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器发生异常: {str(e)}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已关闭。")
    except Exception as e:
        logger.error(f"运行时出错: {str(e)}", exc_info=True) 