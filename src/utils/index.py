#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块，提供各种辅助功能。
"""

import os
import logging
import re
from typing import Optional, Dict, Any, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def detect_chart_type(input_text: str) -> Optional[str]:
    """
    尝试从用户输入中检测图表类型。
    
    Args:
        input_text: 用户输入文本
        
    Returns:
        检测到的图表类型，如果无法检测则为None
    """
    # 检查是否是Mermaid代码
    if re.search(r'^\s*graph\s+(TD|TB|BT|RL|LR)', input_text, re.MULTILINE):
        return "flowchart"
    elif re.search(r'^\s*sequenceDiagram', input_text, re.MULTILINE):
        return "sequence"
    elif re.search(r'^\s*classDiagram', input_text, re.MULTILINE):
        return "class"
    elif re.search(r'^\s*stateDiagram', input_text, re.MULTILINE):
        return "state"
    elif re.search(r'^\s*erDiagram', input_text, re.MULTILINE):
        return "er"
    elif re.search(r'^\s*gantt', input_text, re.MULTILINE):
        return "gantt"
    elif re.search(r'^\s*pie', input_text, re.MULTILINE):
        return "pie"
    
    # 检查文本中的关键词
    keywords = {
        "flowchart": ["流程图", "流程", "步骤", "process", "flow", "flowchart"],
        "sequence": ["时序图", "序列图", "顺序图", "sequence", "时间顺序"],
        "class": ["类图", "class diagram", "类关系", "继承", "实现"],
        "state": ["状态图", "状态", "state diagram", "状态转换"],
        "er": ["实体关系图", "entity relationship", "ER图", "数据库"],
        "gantt": ["甘特图", "进度图", "项目计划", "gantt", "timeline"],
        "pie": ["饼图", "比例", "占比", "pie chart", "百分比"],
    }
    
    # 统计各类型关键词出现次数
    scores = {chart_type: 0 for chart_type in keywords}
    for chart_type, words in keywords.items():
        for word in words:
            if word.lower() in input_text.lower():
                scores[chart_type] += 1
    
    # 找出得分最高的类型
    if not scores:
        return None
    
    max_score = max(scores.values())
    if max_score == 0:
        return None
    
    # 返回得分最高的类型
    for chart_type, score in scores.items():
        if score == max_score:
            return chart_type
    
    return None

def extract_css_template_name(input_text: str) -> Optional[str]:
    """
    从用户输入中提取CSS模板名称。
    
    Args:
        input_text: 用户输入文本
        
    Returns:
        CSS模板名称，如果未找到则为None
    """
    # 定义可能的模板名称及其同义词
    template_aliases = {
        "default": ["默认", "default", "standard", "normal"],
        "dark": ["暗色", "dark", "black", "night", "深色"],
        "light": ["亮色", "light", "white", "day", "浅色"],
        "business": ["商务", "business", "professional", "corporate", "企业"],
        "colorful": ["彩色", "colorful", "vibrant", "vivid", "多彩"],
        "minimal": ["简约", "minimal", "simple", "clean", "minimalist"],
    }
    
    # 正则匹配模板名称
    patterns = [
        r'使用["\']?(\w+)["\']?模板',  # 使用"xxx"模板
        r'["\']?(\w+)["\']?[模板样式风格]',  # "xxx"模板/样式/风格
        r'template[:\s]+["\']?(\w+)["\']?',  # template: "xxx"
        r'css[:\s]+["\']?(\w+)["\']?',  # css: "xxx"
        r'style[:\s]+["\']?(\w+)["\']?',  # style: "xxx"
    ]
    
    # 尝试匹配模板名称
    for pattern in patterns:
        match = re.search(pattern, input_text, re.IGNORECASE)
        if match:
            template_name = match.group(1).lower()
            
            # 检查是否匹配标准模板名称或别名
            for name, aliases in template_aliases.items():
                if template_name in aliases:
                    return name
            
            # 如果没有匹配到别名，但匹配到了名称，直接返回
            return template_name
    
    return None

def extract_custom_css(input_text: str) -> Optional[str]:
    """
    从用户输入中提取自定义CSS。
    
    Args:
        input_text: 用户输入文本
        
    Returns:
        自定义CSS字符串，如果未找到则为None
    """
    # 查找CSS代码块
    css_patterns = [
        r'```css\s*([\s\S]*?)\s*```',  # ```css ... ```
        r'<style>\s*([\s\S]*?)\s*</style>',  # <style> ... </style>
    ]
    
    for pattern in css_patterns:
        match = re.search(pattern, input_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    
    return None

def get_available_templates() -> List[str]:
    """
    获取可用的CSS模板列表。
    
    Returns:
        模板名称列表
    """
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    if not os.path.exists(templates_dir):
        return []
    
    templates = [f.split('.')[0] for f in os.listdir(templates_dir) if f.endswith('.css')]
    return templates 