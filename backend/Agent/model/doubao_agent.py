"""
豆包Agent接口
"""
import requests
import urllib3
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DouBaoAgent:
    """豆包Agent接口"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 使用正确的豆包API端点
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试连接
        self._test_connection()
    
    def _test_connection(self):
        """测试豆包API连接"""
        try:
            test_payload = {
                "model": "doubao-1-5-pro-32k-250115",
                "messages": [{"role": "user", "content": "你好"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                logger.info("✅ 豆包API连接测试成功")
            else:
                logger.warning(f"⚠️ 豆包API连接测试失败，状态码: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ 豆包API连接测试失败: {e}")
            logger.info("💡 建议检查网络连接或API密钥")
    
    def generate_response(self, messages: List[Dict], system_prompt: str = None) -> str:
        """调用豆包API生成回复"""
        try:
            payload = {
                "model": "doubao-1-5-pro-32k-250115",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            if system_prompt:
                payload["messages"].insert(0, {"role": "system", "content": system_prompt})
            
            # 增加重试机制
            for attempt in range(3):
                try:
                    ssl_configs = [
                        {"verify": True},
                        {"verify": False},
                        {"verify": True, "timeout": 120}
                    ]
                    
                    current_config = ssl_configs[min(attempt, len(ssl_configs)-1)]
                    
                    response = requests.post(
                        self.api_url, 
                        headers=self.headers, 
                        json=payload, 
                        timeout=current_config.get("timeout", 60),
                        verify=current_config["verify"]
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                    
                except requests.exceptions.SSLError as ssl_e:
                    logger.warning(f"SSL错误，尝试第{attempt+1}次: {ssl_e}")
                    if attempt == 2:
                        raise
                    continue
                except requests.exceptions.RequestException as req_e:
                    logger.warning(f"请求错误，尝试第{attempt+1}次: {req_e}")
                    if attempt == 2:
                        raise
                    continue
            
        except Exception as e:
            logger.error(f"豆包API调用失败: {e}")
            return self._generate_fallback_response(messages)
    
    def _generate_fallback_response(self, messages: List[Dict]) -> str:
        """生成备用回复"""
        return """我理解您的需求，正在为您规划个性化旅游攻略。

由于网络连接问题，我暂时无法使用豆包Agent为您生成详细回复。
请稍后再试，或者您可以尝试：
• 检查网络连接
• 重新输入您的需求
• 稍后再次尝试

我会继续收集实时数据来支持您的旅游规划。"""

