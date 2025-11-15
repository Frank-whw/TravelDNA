"""
BERT Embedding实现
使用中文BERT模型进行文本向量化
"""
import os
import torch
from typing import List, Union
from langchain_core.embeddings import Embeddings
import logging

logger = logging.getLogger(__name__)


class BERTEmbedding(Embeddings):
    """基于BERT的中文文本嵌入模型"""
    
    def __init__(self, model_name: str = "bert-base-chinese", device: str = None):
        """
        初始化BERT Embedding
        
        Args:
            model_name: BERT模型名称，默认使用bert-base-chinese
            device: 设备类型（'cuda'或'cpu'），None则自动选择
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch.nn.functional as F
            
            logger.info(f"正在加载BERT模型: {model_name} (设备: {self.device})")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            
            self.F = F
            logger.info("✅ BERT模型加载成功")
            
        except ImportError:
            logger.error("❌ 需要安装transformers库: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"❌ BERT模型加载失败: {e}")
            raise
    
    def _mean_pooling(self, model_output, attention_mask):
        """平均池化获取句子向量"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本"""
        with torch.no_grad():
            # 分词和编码
            encoded_input = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            # 移动到设备
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
            
            # 获取模型输出
            model_output = self.model(**encoded_input)
            
            # 平均池化
            sentence_embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
            
            # 归一化
            sentence_embeddings = self.F.normalize(sentence_embeddings, p=2, dim=1)
            
            # 转换为列表
            return sentence_embeddings.cpu().numpy().tolist()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文档
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        try:
            return self._embed_texts(texts)
        except Exception as e:
            logger.error(f"文档嵌入失败: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        嵌入查询文本
        
        Args:
            text: 查询文本
            
        Returns:
            向量
        """
        if not text:
            return [0.0] * 768  # BERT-base的维度
        
        try:
            results = self._embed_texts([text])
            return results[0] if results else [0.0] * 768
        except Exception as e:
            logger.error(f"查询嵌入失败: {e}")
            raise

