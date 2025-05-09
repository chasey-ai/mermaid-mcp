"""
工具函数包，提供各种辅助功能。
"""

from .index import (
    detect_chart_type,
    extract_css_template_name,
    extract_custom_css,
    get_available_templates
)

__all__ = [
    'detect_chart_type',
    'extract_css_template_name',
    'extract_custom_css',
    'get_available_templates'
] 