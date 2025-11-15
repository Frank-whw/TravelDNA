"""
Agent模型模块
包含核心的Agent实现和推理逻辑
"""
from .doubao_agent import DouBaoAgent
try:
    from .deepseek_agent import DeepSeekAgent
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DeepSeekAgent = None
    DEEPSEEK_AVAILABLE = False
from .models import TravelPreference, ThoughtProcess, UserContext, WeatherCondition, TrafficCondition, CrowdLevel

__all__ = ['DouBaoAgent', 'DeepSeekAgent', 'TravelPreference', 'ThoughtProcess', 'UserContext',
           'WeatherCondition', 'TrafficCondition', 'CrowdLevel']

