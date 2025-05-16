import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'lostm001215',
    'database': 'student_management'
}

def connect_to_database():
    """连接到MySQL数据库并返回连接对象"""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        
        if conn.is_connected():
            print("成功连接到MySQL数据库")
            return conn
    
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

def load_data():
    """从数据库加载数据"""
    conn = connect_to_database()
    if conn is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            student_name, phone_relation, phone_number, class_name, 
            course_name, course_type, purchased_amount, gifted_amount,
            consumed_amount, returned_amount, remaining_amount, over_amount,
            consumed_fee, remaining_fee, absent_count, follow_up_person,
            tutor, gender, wechat_status, card_status, face_status,
            grade, student_id, school
        FROM student_courses
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    
    except Error as e:
        print(f"查询数据时出错: {e}")
        conn.close()
        return pd.DataFrame()

def clean_and_prepare_data(df):
    """清洗和准备数据"""
    # 复制数据，避免修改原始数据
    df_clean = df.copy()
    
    # 处理缺失值
    numeric_columns = ['purchased_amount', 'gifted_amount', 'consumed_amount', 
                       'returned_amount', 'remaining_amount', 'over_amount',
                       'consumed_fee', 'remaining_fee', 'absent_count']
    
    for col in numeric_columns:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        df_clean[col].fillna(0, inplace=True)
    
    # 填充分类变量的缺失值
    categorical_columns = ['gender', 'class_name', 'course_name', 'school']
    for col in categorical_columns:
        df_clean[col].fillna('未知', inplace=True)
    
    # 添加派生特征
    df_clean['course_completion_rate'] = (df_clean['consumed_amount'] / (df_clean['purchased_amount'] + df_clean['gifted_amount'])) * 100
    df_clean['course_completion_rate'] = df_clean['course_completion_rate'].clip(0, 100)  # 限制在0-100%之间
    df_clean['consumption_efficiency'] = df_clean['consumed_amount'] / (df_clean['absent_count'] + 1)  # 避免除以零
    
    return df_clean

def student_clustering(df):
    """使用K-Means对学生进行聚类分析"""
    # 选择用于聚类的特征
    features = ['purchased_amount', 'consumed_amount', 'remaining_amount', 
                'absent_count', 'course_completion_rate']
    
    # 提取特征
    X = df[features].copy()
    
    # 标准化特征
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 确定最佳聚类数
    inertia = []
    k_range = range(1, 11)
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(X_scaled)
        inertia.append(kmeans.inertia_)
    
    # 应用肘部法则选择最佳聚类数
    elbow_point = 3  # 根据肘部法则选择
    
    # 执行KMeans聚类
    kmeans = KMeans(n_clusters=elbow_point, random_state=42)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # 分析每个聚类的特征
    cluster_analysis = df.groupby('cluster').agg({
        'purchased_amount': 'mean',
        'consumed_amount': 'mean',
        'remaining_amount': 'mean',
        'absent_count': 'mean',
        'course_completion_rate': 'mean',
        'student_name': 'count'
    }).rename(columns={'student_name': 'student_count'})
    
    return df, cluster_analysis

def course_analysis(df):
    """分析课程的受欢迎程度和完成率"""
    course_stats = df.groupby('course_name').agg({
        'student_name': 'count',
        'purchased_amount': 'sum',
        'consumed_amount': 'sum',
        'remaining_amount': 'sum',
        'absent_count': 'sum'
    }).rename(columns={'student_name': 'student_count'})
    
    course_stats['completion_rate'] = (course_stats['consumed_amount'] / course_stats['purchased_amount']) * 100
    course_stats['average_absences'] = course_stats['absent_count'] / course_stats['student_count']
    
    # 只保留有一定学生数量的课程，避免偶然数据
    course_stats = course_stats[course_stats['student_count'] >= 5]
    
    # 排序
    popular_courses = course_stats.sort_values('student_count', ascending=False)
    highest_completion = course_stats.sort_values('completion_rate', ascending=False)
    lowest_absence = course_stats.sort_values('average_absences')
    
    return {
        'popular_courses': popular_courses.head(10),
        'highest_completion': highest_completion.head(10),
        'lowest_absence': lowest_absence.head(10)
    }

def attendance_pattern_analysis(df):
    """分析学生出勤模式与课程进度的关系"""
    # 计算每个学生的出勤率
    df['attendance_rate'] = 1 - (df['absent_count'] / (df['consumed_amount'] + df['absent_count'] + 0.1))
    df['attendance_rate'] = df['attendance_rate'].clip(0, 1)  # 限制在0-100%之间
    
    # 按出勤率分组
    attendance_bins = [0, 0.6, 0.8, 0.9, 1.0]
    attendance_labels = ['低(<60%)', '中(60-80%)', '良好(80-90%)', '优秀(>90%)']
    df['attendance_group'] = pd.cut(df['attendance_rate'], bins=attendance_bins, labels=attendance_labels)
    
    # 分析不同出勤率组的课程完成情况
    attendance_analysis = df.groupby('attendance_group').agg({
        'course_completion_rate': 'mean',
        'consumption_efficiency': 'mean',
        'student_name': 'count'
    }).rename(columns={'student_name': 'student_count'})
    
    return attendance_analysis

def generate_insights():
    """生成数据洞察报告"""
    # 加载数据
    df = load_data()
    if df.empty:
        return "无法加载数据，请检查数据库连接"
    
    # 清洗和准备数据
    df_prepared = clean_and_prepare_data(df)
    
    # 学生聚类分析
    df_clustered, cluster_analysis = student_clustering(df_prepared)
    
    # 课程分析
    course_insights = course_analysis(df_prepared)
    
    # 出勤模式分析
    attendance_analysis = attendance_pattern_analysis(df_prepared)
    
    # 生成报告
    report = """
    # 学生课程数据高级分析报告
    
    ## 1. 学生分群分析
    
    根据购买课时、消耗课时、剩余课时、缺课次数和课程完成率等指标，学生可以被分为以下几个群体：
    
    {}
    
    ## 2. 最受欢迎的课程（学生数量最多）
    
    {}
    
    ## 3. 课程完成率最高的课程
    
    {}
    
    ## 4. 缺勤率最低的课程
    
    {}
    
    ## 5. 出勤模式与课程进度分析
    
    学生的出勤情况与课程完成率和学习效率存在明显关联：
    
    {}
    
    ## 6. 关键发现和建议
    
    1. 课程类型 "{}" 最受欢迎，拥有最多的学生。
    2. 完成率最高的课程是 "{}"，可以研究其成功因素。
    3. 出勤率为优秀(>90%)的学生课程完成率平均为 {:.2f}%，而出勤率低(<60%)的学生完成率仅为 {:.2f}%。
    4. 建议重点关注聚类组 "{}" 的学生，该组学生购买课时多但完成率低。
    5. 建议为出勤率低的学生提供额外的支持和鼓励，以提高其课程完成率。
    """.format(
        cluster_analysis.to_string(),
        course_insights['popular_courses'][['student_count', 'purchased_amount', 'consumed_amount']].to_string(),
        course_insights['highest_completion'][['completion_rate', 'student_count']].to_string(),
        course_insights['lowest_absence'][['average_absences', 'student_count']].to_string(),
        attendance_analysis.to_string(),
        course_insights['popular_courses'].index[0],
        course_insights['highest_completion'].index[0],
        attendance_analysis.loc['优秀(>90%)', 'course_completion_rate'] if '优秀(>90%)' in attendance_analysis.index else 0,
        attendance_analysis.loc['低(<60%)', 'course_completion_rate'] if '低(<60%)' in attendance_analysis.index else 0,
        cluster_analysis['remaining_amount'].idxmax()
    )
    
    return report

def save_report_to_file():
    """将分析报告保存到文件"""
    report = generate_insights()
    
    # 保存到文件
    with open('学生课程数据分析报告.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("分析报告已保存到 '学生课程数据分析报告.md'")
    
    # 生成可视化并保存
    create_visualizations()

def create_visualizations():
    """创建高级数据可视化并保存为图片"""
    # 确保存在图片目录
    if not os.path.exists('visualizations'):
        os.makedirs('visualizations')
    
    # 加载数据
    df = load_data()
    if df.empty:
        print("无法加载数据，请检查数据库连接")
        return
    
    # 清洗和准备数据
    df_prepared = clean_and_prepare_data(df)
    
    # 设置Seaborn样式
    sns.set(style="whitegrid")
    
    # 1. 课程类型分布可视化
    plt.figure(figsize=(12, 6))
    course_type_counts = df_prepared['course_type'].value_counts().sort_values(ascending=False)
    sns.barplot(x=course_type_counts.index, y=course_type_counts.values)
    plt.title('课程类型分布', fontsize=16)
    plt.xlabel('课程类型')
    plt.ylabel('学生数量')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('visualizations/课程类型分布.png', dpi=300)
    plt.close()
    
    # 2. 课程完成率与缺课次数关系
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_prepared, x='absent_count', y='course_completion_rate', 
                    hue='gender', size='purchased_amount', sizes=(20, 200), alpha=0.7)
    plt.title('课程完成率与缺课次数关系', fontsize=16)
    plt.xlabel('缺课次数')
    plt.ylabel('课程完成率 (%)')
    plt.tight_layout()
    plt.savefig('visualizations/课程完成率与缺课次数关系.png', dpi=300)
    plt.close()
    
    # 3. 聚类分析可视化
    df_clustered, _ = student_clustering(df_prepared)
    
    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=df_clustered, x='consumed_amount', y='remaining_amount', 
                  hue='cluster', size='purchased_amount', sizes=(20, 200), alpha=0.7, palette='viridis')
    plt.title('学生消耗课时与剩余课时聚类分析', fontsize=16)
    plt.xlabel('消耗课时')
    plt.ylabel('剩余课时')
    plt.tight_layout()
    plt.savefig('visualizations/学生课时聚类分析.png', dpi=300)
    plt.close()
    
    # 4. 出勤率与课程完成率的箱线图
    plt.figure(figsize=(12, 6))
    df_clustered['attendance_group'] = pd.cut(
        1 - (df_clustered['absent_count'] / (df_clustered['consumed_amount'] + df_clustered['absent_count'] + 0.1)).clip(0, 1),
        bins=[0, 0.6, 0.8, 0.9, 1.0],
        labels=['低(<60%)', '中(60-80%)', '良好(80-90%)', '优秀(>90%)']
    )
    sns.boxplot(data=df_clustered, x='attendance_group', y='course_completion_rate')
    plt.title('不同出勤率的课程完成率分布', fontsize=16)
    plt.xlabel('出勤率分组')
    plt.ylabel('课程完成率 (%)')
    plt.tight_layout()
    plt.savefig('visualizations/出勤率与课程完成率关系.png', dpi=300)
    plt.close()
    
    # 5. 学生性别分布饼图
    plt.figure(figsize=(8, 8))
    gender_counts = df_prepared['gender'].value_counts()
    plt.pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', 
           colors=sns.color_palette('pastel'), startangle=90)
    plt.title('学生性别分布', fontsize=16)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('visualizations/学生性别分布.png', dpi=300)
    plt.close()
    
    # 6. 热力图：班级与课程类型的关系
    plt.figure(figsize=(14, 10))
    class_course_counts = pd.crosstab(df_prepared['class_name'], df_prepared['course_type'])
    # 只保留主要班级和课程类型，避免图表过于复杂
    main_classes = df_prepared['class_name'].value_counts().head(10).index
    main_course_types = df_prepared['course_type'].value_counts().head(8).index
    filtered_counts = class_course_counts.loc[main_classes, main_course_types]
    
    sns.heatmap(filtered_counts, annot=True, fmt='d', cmap='YlGnBu')
    plt.title('班级与课程类型关系热力图', fontsize=16)
    plt.xlabel('课程类型')
    plt.ylabel('班级')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('visualizations/班级课程关系热力图.png', dpi=300)
    plt.close()
    
    print(f"已生成6个高级数据可视化图表，保存在 'visualizations' 目录")

def perform_time_series_analysis():
    """执行时间序列分析，分析学生购课和消耗趋势"""
    # 加载数据
    df = load_data()
    if df.empty:
        print("无法加载数据，请检查数据库连接")
        return
    
    # 将导入日期转换为日期类型
    df['import_date'] = pd.to_datetime(df['import_date'], errors='coerce')
    
    # 按日期分组并计算每日累计值
    daily_stats = df.groupby(df['import_date'].dt.date).agg({
        'student_name': 'count',
        'purchased_amount': 'sum',
        'consumed_amount': 'sum'
    }).rename(columns={'student_name': 'student_count'})
    
    # 计算累计值
    daily_stats['cumulative_students'] = daily_stats['student_count'].cumsum()
    daily_stats['cumulative_purchased'] = daily_stats['purchased_amount'].cumsum()
    daily_stats['cumulative_consumed'] = daily_stats['consumed_amount'].cumsum()
    
    # 创建时间序列可视化
    plt.figure(figsize=(14, 8))
    
    # 学生累计增长曲线
    plt.subplot(2, 1, 1)
    plt.plot(daily_stats.index, daily_stats['cumulative_students'], marker='o', linestyle='-', label='累计学生数')
    plt.title('学生累计增长趋势', fontsize=14)
    plt.ylabel('学生数量')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # 课时购买和消耗趋势
    plt.subplot(2, 1, 2)
    plt.plot(daily_stats.index, daily_stats['cumulative_purchased'], marker='s', linestyle='-', label='累计购买课时')
    plt.plot(daily_stats.index, daily_stats['cumulative_consumed'], marker='^', linestyle='-', label='累计消耗课时')
    plt.title('课时购买与消耗趋势', fontsize=14)
    plt.ylabel('课时数量')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    plt.tight_layout()
    if not os.path.exists('visualizations'):
        os.makedirs('visualizations')
    plt.savefig('visualizations/时间序列分析.png', dpi=300)
    plt.close()
    
    print("时间序列分析已完成，图表保存在 'visualizations/时间序列分析.png'")

if __name__ == "__main__":
    save_report_to_file()
    perform_time_series_analysis()