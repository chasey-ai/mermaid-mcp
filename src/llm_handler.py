#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM处理模块，负责调用LLM理解用户输入并生成HTML图表。
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
import anthropic
import openai
import jinja2
from dotenv import load_dotenv

# 导入工具函数
from src.utils import detect_chart_type, extract_css_template_name, extract_custom_css

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 初始化模板引擎
template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(os.path.dirname(__file__), "templates"))
template_env = jinja2.Environment(loader=template_loader)

# 初始化API客户端
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

async def process_user_input(
    input_text: str,
    chart_type: Optional[str] = None,
    css_template: Optional[str] = None,
    custom_css: Optional[str] = None
) -> str:
    """
    处理用户输入，调用LLM生成HTML图表。
    
    Args:
        input_text: 用户输入的文本（流程图描述、Mermaid代码等）
        chart_type: 指定图表类型（可选）
        css_template: 要使用的CSS模板名称（可选）
        custom_css: 用户提供的自定义CSS（可选）
        
    Returns:
        生成的HTML内容
    """
    logger.info(f"处理用户输入，图表类型: {chart_type}, CSS模板: {css_template}")
    
    # 如果未指定图表类型，尝试从输入中检测
    if not chart_type:
        detected_type = detect_chart_type(input_text)
        if detected_type:
            chart_type = detected_type
            logger.info(f"检测到图表类型: {chart_type}")
    
    # 如果未指定CSS模板，尝试从输入中检测
    if not css_template:
        detected_template = extract_css_template_name(input_text)
        if detected_template:
            css_template = detected_template
            logger.info(f"检测到CSS模板: {css_template}")
    
    # 如果未指定自定义CSS，尝试从输入中检测
    if not custom_css:
        detected_css = extract_custom_css(input_text)
        if detected_css:
            custom_css = detected_css
            logger.info(f"检测到自定义CSS")
    
    # 根据环境变量选择使用的LLM
    llm_provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    
    # 准备LLM的提示
    prompt = _create_prompt(input_text, chart_type)
    
    # 获取HTML内容
    if llm_provider == "anthropic":
        html_content = await _call_anthropic(prompt)
    else:  # 默认使用OpenAI
        html_content = await _call_openai(prompt)
    
    # 提取HTML代码
    html_code = _extract_html(html_content)
    
    # 应用CSS样式
    final_html = _apply_styling(html_code, css_template, custom_css)
    
    return final_html

def _create_prompt(input_text: str, chart_type: Optional[str] = None) -> str:
    """创建LLM提示"""
    chart_type_str = f"类型为 {chart_type} 的" if chart_type else ""
    
    prompt = f"""
    作为一个专业的图表生成专家，请根据以下用户输入，生成一个精美的HTML图表（无需使用Mermaid库）。

    用户输入:
    ```
    {input_text}
    ```

    要求:
    1. 请直接生成HTML和CSS代码，不需要使用任何外部库（如Mermaid.js）
    2. 请生成一个{chart_type_str}图表，确保图表美观、专业且易于理解
    3. 你的代码将被直接用于生成PNG图像，因此请确保自包含且完整
    4. 使用内联CSS样式或内部样式表，不要引用外部样式表
    5. 确保元素有适当的边距和内边距，使图表看起来整洁和专业
    6. 使用清晰可辨的字体和颜色方案
    7. 请在合适的地方添加箭头、连接线或其他视觉元素来表示关系和流程
    8. 如果输入包含Mermaid代码，请尝试参考其结构和内容，但始终输出HTML/CSS代码
    9. 为节点和连接线添加适当的CSS类（如.node、.edge、.start、.end等），以便样式定制
    10. 将主要内容包装在一个带有类名"chart-container"的div中

    只返回完整的HTML代码，不需要任何解释。确保代码放在<html>和</html>标签内。
    """
    
    return prompt

async def _call_anthropic(prompt: str) -> str:
    """调用Anthropic API"""
    try:
        message = await anthropic_client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"调用Anthropic API时出错: {str(e)}", exc_info=True)
        raise

async def _call_openai(prompt: str) -> str:
    """调用OpenAI API"""
    try:
        response = await openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": "你是一个专业的图表生成专家，能够生成精美的HTML图表。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"调用OpenAI API时出错: {str(e)}", exc_info=True)
        raise

def _extract_html(content: str) -> str:
    """从LLM响应中提取HTML代码"""
    # 基本清理
    content = content.strip()
    
    # 如果包含在代码块中
    if content.startswith("```html") or content.startswith("```"):
        lines = content.split("\n")
        # 移除第一行和最后一行的代码标记
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    
    # 确保包含在HTML标签中
    if not content.strip().startswith("<html"):
        content = f"<html>\n<body>\n{content}\n</body>\n</html>"
    
    return content

def _apply_styling(html_code: str, css_template: Optional[str] = None, custom_css: Optional[str] = None) -> str:
    """应用CSS样式到HTML"""
    # 如果没有指定CSS模板，使用默认模板
    template_name = css_template if css_template else "default"
    
    # 尝试加载模板
    try:
        css_content = ""
        if template_name != "none":
            template_path = os.path.join(os.path.dirname(__file__), "templates", f"{template_name}.css")
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    css_content = f.read()
            else:
                logger.warning(f"未找到模板 {template_name}.css，使用内联样式")
        
        # 添加自定义CSS（如果有）
        if custom_css:
            css_content += f"\n\n/* 自定义CSS */\n{custom_css}"
        
        # 如果有CSS内容，将其嵌入到HTML中
        if css_content:
            # 检查HTML中是否已经有<head>标签
            if "<head>" in html_code:
                html_code = html_code.replace("<head>", f"<head>\n<style>\n{css_content}\n</style>")
            else:
                # 如果没有<head>标签，在<html>标签后添加
                html_code = html_code.replace("<html>", f"<html>\n<head>\n<style>\n{css_content}\n</style>\n</head>")
    except Exception as e:
        logger.error(f"应用CSS样式时出错: {str(e)}", exc_info=True)
    
    return html_code 