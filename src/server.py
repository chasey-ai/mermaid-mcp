#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mermaid-MCP: 基于MCP协议的流程图生成服务器
该服务器接收用户输入并使用LLM生成HTML图表，然后将其转换为PNG图像。
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# MCP相关
import mcp.server.stdio
import mcp.types as mcp_types
from mcp.server.lowlevel import NotificationOptions, Server

# 导入项目模块
from src.llm_handler import process_user_input
from src.renderer import render_html_to_png
from src.utils import get_available_templates

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 定义MCP工具参数
class GenerateChartParams(BaseModel):
    input_text: str
    chart_type: Optional[str] = None
    css_template: Optional[str] = None
    custom_css: Optional[str] = None
    width: Optional[int] = Field(default=800)
    height: Optional[int] = Field(default=600)

# 定义MCP服务器类
class MermaidMCPServer:
    def __init__(self):
        # 创建FastAPI应用
        self.app = FastAPI(title="Mermaid-MCP API")
        
        # 创建MCP服务器
        self.mcp_server = Server("mermaid-mcp-server")
        
        # 注册工具
        @self.mcp_server.list_tools()
        async def list_tools() -> List[mcp_types.Tool]:
            return [
                mcp_types.Tool(
                    name="generate_chart",
                    description="将文本描述或Mermaid代码生成为PNG图表",
                    arguments=[
                        mcp_types.ToolArgument(name="input_text", description="用户输入的文本或Mermaid代码", required=True),
                        mcp_types.ToolArgument(name="chart_type", description="图表类型，例如flowchart, sequence等", required=False),
                        mcp_types.ToolArgument(name="css_template", description="CSS模板名称", required=False),
                        mcp_types.ToolArgument(name="custom_css", description="自定义CSS", required=False),
                        mcp_types.ToolArgument(name="width", description="图表宽度", required=False),
                        mcp_types.ToolArgument(name="height", description="图表高度", required=False),
                    ],
                ),
                mcp_types.Tool(
                    name="list_css_templates",
                    description="获取可用的CSS模板列表",
                    arguments=[],
                ),
            ]
        
        @self.mcp_server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"调用工具: {name}, 参数: {arguments}")
            
            if name == "generate_chart":
                try:
                    # 参数处理
                    params = GenerateChartParams(
                        input_text=arguments.get("input_text", ""),
                        chart_type=arguments.get("chart_type"),
                        css_template=arguments.get("css_template"),
                        custom_css=arguments.get("custom_css"),
                        width=int(arguments.get("width", 800)),
                        height=int(arguments.get("height", 600))
                    )
                    
                    # 使用LLM处理用户输入，生成HTML
                    html_content = await process_user_input(
                        params.input_text,
                        chart_type=params.chart_type,
                        css_template=params.css_template,
                        custom_css=params.custom_css
                    )
                    
                    # 将HTML渲染为PNG
                    png_data = await render_html_to_png(
                        html_content,
                        width=params.width,
                        height=params.height
                    )
                    
                    # 返回资源
                    return {
                        "content": png_data,
                        "mime_type": "image/png",
                        "filename": "生成的图表.png",
                        "description": "基于用户输入生成的图表"
                    }
                except Exception as e:
                    logger.error(f"生成图表时出错: {str(e)}", exc_info=True)
                    # 返回错误信息
                    error_html = f"<html><body><h1>生成图表时出错</h1><p>{str(e)}</p></body></html>"
                    error_png = await render_html_to_png(error_html, width=400, height=300)
                    return {
                        "content": error_png,
                        "mime_type": "image/png",
                        "filename": "错误.png",
                        "description": f"生成过程中出现错误: {str(e)}"
                    }
            
            elif name == "list_css_templates":
                templates = get_available_templates()
                
                html_content = """
                <html><body>
                <h1>可用的CSS模板</h1>
                <ul>
                """
                
                for template in templates:
                    html_content += f"<li>{template}</li>"
                
                html_content += """
                </ul>
                </body></html>
                """
                
                png_data = await render_html_to_png(html_content, width=400, height=400)
                return {
                    "content": png_data,
                    "mime_type": "image/png",
                    "filename": "可用CSS模板.png",
                    "description": "列出所有可用的CSS模板"
                }
            
            else:
                raise ValueError(f"未知工具: {name}")
    
    async def start(self, host="localhost", port=5000):
        """启动MCP服务器"""
        import uvicorn
        
        # 将静态文件目录挂载到API
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # 创建MCP API终结点
        @self.app.post("/mcp")
        async def handle_mcp_request(request: Dict[str, Any]):
            try:
                # 处理MCP请求
                response = await self.mcp_server.handle_json_rpc(request)
                return response
            except Exception as e:
                logger.error(f"处理MCP请求时出错: {str(e)}", exc_info=True)
                return {"error": str(e)}
        
        logger.info(f"启动Mermaid-MCP服务器，监听 {host}:{port}")
        
        # 启动FastAPI
        config = uvicorn.Config(self.app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()
        

# 主函数
async def main():
    """程序入口点"""
    server = MermaidMCPServer()
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器发生异常: {str(e)}", exc_info=True) 