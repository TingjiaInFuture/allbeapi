import pandas as pd
import numpy as np
from typing import Dict, Any

def generate_sales_report(days: int = 7) -> pd.DataFrame:
    """
    生成销售数据报表。
    
    AllBeAPI 会自动检测到这是 DataFrame：
    - 如果数据量小，直接转为 JSON。
    - 如果数据量大，返回 Markdown 预览和 Object ID。
    """
    dates = pd.date_range(start='2024-01-01', periods=days)
    df = pd.DataFrame({
        'Date': dates,
        'Revenue': np.random.randint(1000, 5000, size=days),
        'Cost': np.random.randint(500, 2000, size=days)
    })
    return df

def analyze_dataframe(df_id: str) -> Dict[str, Any]:
    """
    接收一个 DataFrame 的 ID 并进行分析。
    
    Args:
        df_id: 上一步生成的 DataFrame 的 object_id
    """
    # 注意：在实际代码中，AllBeAPI 目前主要处理“返回”对象。
    # 如果你想把 object_id 传回来，目前需要在自定义代码中维护一个简单的查找表，
    # 或者直接使用 `call-object-method` 调用 DataFrame 自带的方法（如 describe）。
    pass