import pandas as pd
import matplotlib.pyplot as plt

# 读取CSV文件
df = pd.read_csv('中外合作办学机构数据.csv')

# 打印基本信息
print(f'总记录数: {len(df)}')
print(f'包含地区数: {df["地区"].nunique()}')

# 统计每个地区的机构和项目数量
region_stats = df.groupby(['地区', '类型']).size().unstack().fillna(0)
print('\n各地区机构和项目数量:')
print(region_stats)

# 统计各地区合作办学总数
region_total = df.groupby('地区').size().sort_values(ascending=False)
print('\n合作办学总数排名前5的地区:')
print(region_total.head())

# 保存统计信息到CSV
region_stats.to_csv('中外合作办学机构统计.csv')
print('\n统计信息已保存到 中外合作办学机构统计.csv')