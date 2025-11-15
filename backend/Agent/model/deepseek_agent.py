"""
DeepSeek Agent接口
使用OpenAI兼容的API格式
"""
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI SDK未安装，DeepSeek Agent将不可用。请运行: pip install openai")


class DeepSeekAgent:
    """DeepSeek Agent接口，使用OpenAI兼容的API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        """
        初始化DeepSeek Agent
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL，默认 https://api.deepseek.com
            model: 模型名称，默认 deepseek-chat（非思考模式），也可使用 deepseek-reasoner（思考模式）
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI SDK未安装，无法使用DeepSeek Agent。请运行: pip install openai")
        
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
        # 初始化OpenAI客户端（兼容DeepSeek API）
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 测试连接
        self._test_connection()
    
    def _test_connection(self):
        """测试DeepSeek API连接"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "你好"}
                ],
                max_tokens=10,
                stream=False
            )
            
            if response.choices and response.choices[0].message.content:
                logger.info("✅ DeepSeek API连接测试成功")
            else:
                logger.warning("⚠️ DeepSeek API连接测试失败：响应格式异常")
                
        except Exception as e:
            error_str = str(e)
            # 检查是否是余额不足错误（402）
            if "402" in error_str or "Insufficient Balance" in error_str or "Payment Required" in error_str:
                logger.error("❌ DeepSeek API余额不足（402错误），将自动降级到豆包API")
                raise ValueError("DeepSeek API余额不足，请充值或使用豆包API")
            else:
                logger.warning(f"⚠️ DeepSeek API连接测试失败: {e}")
                logger.info("💡 建议检查网络连接或API密钥")
    
    def generate_response(self, messages: List[Dict], system_prompt: str = None, 
                         temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        调用DeepSeek API生成回复
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词（可选）
            temperature: 温度参数，默认0.7
            max_tokens: 最大token数，默认2000
            
        Returns:
            生成的回复文本
        """
        try:
            # 准备消息列表
            chat_messages = messages.copy()
            
            # 如果有系统提示词，添加到消息列表开头
            if system_prompt:
                chat_messages.insert(0, {"role": "system", "content": system_prompt})
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # 提取回复内容
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                logger.warning("DeepSeek API返回空内容")
                return self._generate_fallback_response(messages)
                
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return self._generate_fallback_response(messages)
    
    def _generate_fallback_response(self, messages: List[Dict]) -> str:
        """生成备用回复"""
        return """我理解您的需求，正在为您规划个性化旅游攻略。

由于网络连接问题，我暂时无法使用DeepSeek Agent为您生成详细回复。
请稍后再试，或者您可以尝试：
• 检查网络连接
• 重新输入您的需求
• 稍后再次尝试

我会继续收集实时数据来支持您的旅游规划。"""

