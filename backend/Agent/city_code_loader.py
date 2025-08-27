"""
城市代码加载器 - 处理高德地图城市代码Excel文件
"""
import pandas as pd
import os
import logging
from typing import Dict, Optional, List
from config import Config

logger = logging.getLogger(__name__)

class CityCodeLoader:
    """城市代码加载器"""
    
    def __init__(self):
        self.city_code_data = {}
        self.loaded = False
        self.excel_file_path = Config.AMAP_CITY_CODE_FILE
        
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(self.excel_file_path):
            # 从当前文件位置计算相对路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.excel_file_path = os.path.join(current_dir, self.excel_file_path)
        
    def load_city_codes(self) -> bool:
        """加载城市代码数据"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.excel_file_path):
                logger.error(f"城市代码文件不存在: {self.excel_file_path}")
                return False
            
            # 读取Excel文件
            df = pd.read_excel(self.excel_file_path)
            logger.info(f"成功读取Excel文件，共 {len(df)} 行数据")
            
            # 处理数据，建立城市名到代码的映射
            for index, row in df.iterrows():
                # 根据Excel文件的实际列名进行调整
                # 常见的列名可能是：city, citycode, adcode, name等
                city_name = None
                city_code = None
                ad_code = None
                
                # 尝试不同的列名组合
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'city' in col_lower or '城市' in col_lower or 'name' in col_lower or '名称' in col_lower:
                        if pd.notna(row[col]):
                            city_name = str(row[col]).strip()
                    elif 'citycode' in col_lower or '城市代码' in col_lower:
                        if pd.notna(row[col]):
                            city_code = str(row[col]).strip()
                    elif 'adcode' in col_lower or '区域代码' in col_lower:
                        if pd.notna(row[col]):
                            ad_code = str(row[col]).strip()
                
                # 存储城市信息
                if city_name:
                    self.city_code_data[city_name] = {
                        'citycode': city_code,
                        'adcode': ad_code,
                        'name': city_name
                    }
                    
                    # 添加一些常见的别名
                    if '上海' in city_name:
                        self.city_code_data['上海市'] = self.city_code_data[city_name]
                        self.city_code_data['上海'] = self.city_code_data[city_name]
            
            # 手动添加上海的城市代码（如果没有在Excel中找到）
            if '上海' not in self.city_code_data:
                self.city_code_data['上海'] = {
                    'citycode': '021',
                    'adcode': '310000',
                    'name': '上海市'
                }
                self.city_code_data['上海市'] = self.city_code_data['上海']
            
            self.loaded = True
            logger.info(f"城市代码加载完成，共加载 {len(self.city_code_data)} 个城市")
            return True
            
        except Exception as e:
            logger.error(f"加载城市代码失败: {e}")
            return False
    
    def get_city_code(self, city_name: str) -> Optional[str]:
        """根据城市名获取城市代码"""
        if not self.loaded:
            if not self.load_city_codes():
                return None
        
        # 清理城市名
        city_name = city_name.strip()
        
        # 直接匹配
        if city_name in self.city_code_data:
            # 优先返回adcode，如果没有则返回citycode
            city_info = self.city_code_data[city_name]
            return city_info.get('adcode') or city_info.get('citycode')
        
        # 模糊匹配
        for stored_city, info in self.city_code_data.items():
            if city_name in stored_city or stored_city in city_name:
                return info.get('adcode') or info.get('citycode')
        
        # 如果找不到，返回上海的代码作为默认值
        logger.warning(f"未找到城市 {city_name} 的代码，使用上海代码")
        return self.city_code_data.get('上海', {}).get('adcode', '310000')
    
    def get_city_info(self, city_name: str) -> Optional[Dict]:
        """获取城市完整信息"""
        if not self.loaded:
            if not self.load_city_codes():
                return None
        
        city_name = city_name.strip()
        
        # 直接匹配
        if city_name in self.city_code_data:
            return self.city_code_data[city_name]
        
        # 模糊匹配
        for stored_city, info in self.city_code_data.items():
            if city_name in stored_city or stored_city in city_name:
                return info
        
        return None
    
    def search_cities(self, keyword: str) -> List[Dict]:
        """搜索包含关键词的城市"""
        if not self.loaded:
            if not self.load_city_codes():
                return []
        
        keyword = keyword.strip().lower()
        results = []
        
        for city_name, info in self.city_code_data.items():
            if keyword in city_name.lower():
                results.append(info)
        
        return results
    
    def get_supported_cities(self) -> List[str]:
        """获取支持的城市列表"""
        if not self.loaded:
            if not self.load_city_codes():
                return []
        
        return list(self.city_code_data.keys())
    
    def get_statistics(self) -> Dict:
        """获取加载统计信息"""
        return {
            'loaded': self.loaded,
            'total_cities': len(self.city_code_data),
            'file_path': self.excel_file_path,
            'sample_cities': list(self.city_code_data.keys())[:10] if self.city_code_data else []
        }

# 全局实例
_city_loader = None

def get_city_loader() -> CityCodeLoader:
    """获取城市代码加载器实例"""
    global _city_loader
    if _city_loader is None:
        _city_loader = CityCodeLoader()
    return _city_loader

def get_city_code(city_name: str) -> Optional[str]:
    """便捷函数：获取城市代码"""
    loader = get_city_loader()
    return loader.get_city_code(city_name)

def get_city_info(city_name: str) -> Optional[Dict]:
    """便捷函数：获取城市信息"""
    loader = get_city_loader()
    return loader.get_city_info(city_name)

# 测试函数
def test_city_loader():
    """测试城市代码加载器"""
    print("=== 城市代码加载器测试 ===")
    
    loader = CityCodeLoader()
    
    # 测试加载
    if loader.load_city_codes():
        print("✅ 城市代码加载成功")
        
        # 测试统计信息
        stats = loader.get_statistics()
        print(f"📊 统计信息: {stats}")
        
        # 测试城市代码查询
        test_cities = ['上海', '上海市', '北京', '不存在的城市']
        for city in test_cities:
            code = loader.get_city_code(city)
            info = loader.get_city_info(city)
            print(f"🏙️ {city} -> 代码: {code}, 信息: {info}")
        
        # 测试搜索
        search_results = loader.search_cities('上海')
        print(f"🔍 搜索'上海': {search_results}")
        
    else:
        print("❌ 城市代码加载失败")

if __name__ == "__main__":
    test_city_loader()
