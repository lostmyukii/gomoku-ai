import pandas as pd
import mysql.connector
from mysql.connector import Error
import getpass
import sys
import os
from datetime import datetime

def create_database_and_table(conn, cursor, database_name):
    """创建数据库和表结构"""
    try:
        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        cursor.execute(f"USE {database_name}")
        
        # 创建学生报读课程表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_name VARCHAR(100),
            phone_relation VARCHAR(50),
            phone_number VARCHAR(20),
            class_name VARCHAR(100),
            course_name VARCHAR(100),
            course_type VARCHAR(50),
            purchased_amount INT,
            gifted_amount INT,
            consumed_amount INT,
            returned_amount INT,
            remaining_amount INT,
            over_amount INT,
            consumed_fee DECIMAL(10,2),
            remaining_fee DECIMAL(10,2),
            absent_count INT,
            follow_up_person VARCHAR(50),
            tutor VARCHAR(50),
            gender VARCHAR(10),
            wechat_status VARCHAR(20),
            card_status VARCHAR(20),
            face_status VARCHAR(20),
            grade VARCHAR(50),
            student_id VARCHAR(50),
            school VARCHAR(100),
            import_date DATETIME
        )
        """)
        
        conn.commit()
        print(f"数据库 {database_name} 和表 student_courses 创建成功")
        return True
    except Error as e:
        print(f"创建数据库和表时出错: {e}")
        return False

def process_csv_file(filename):
    """处理CSV文件，清洗数据"""
    try:
        # 读取CSV文件
        df = pd.read_csv(filename, encoding='utf-8', low_memory=False)
        
        # 显示前几行数据
        print("原始数据预览：")
        print(df.head(2))
        
        # 处理列名，去除前后空格
        df.columns = df.columns.str.strip()
        
        # 处理空值
        df = df.fillna('')
        
        # 处理数字列中的非数字字符
        numeric_columns = ['购买数量', '赠送数量', '消耗数量', '退转数量', '剩余数量', '超上数量', 
                           '课消金额', '剩余课消金额', '缺课次数', '年龄']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('课时', '').str.replace('岁', '')
                # 尝试转换为数值，失败则设为0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 选择最重要的列，简化CSV
        selected_columns = [
            '学员姓名', '手机号身份', '手机号', '所在班级', '课程名称', '课程类型',
            '购买数量', '赠送数量', '消耗数量', '退转数量', '剩余数量', '超上数量',
            '课消金额', '剩余课消金额', '缺课次数', '跟进人', '学管师',
            '性别', '微信绑定状态', '绑卡状态', '人脸采集状态',
            '年级', '学号', '学校'
        ]
        
        # 只保留存在的列
        existing_columns = [col for col in selected_columns if col in df.columns]
        df_selected = df[existing_columns]
        
        print("数据清洗完成，共处理 {} 行记录".format(len(df_selected)))
        return df_selected
    
    except Exception as e:
        print(f"处理CSV文件时出错: {e}")
        return None

def import_to_mysql(df, conn, cursor, batch_size=100):
    """将DataFrame数据导入MySQL"""
    try:
        # 获取列映射
        column_mapping = {
            '学员姓名': 'student_name',
            '手机号身份': 'phone_relation',
            '手机号': 'phone_number',
            '所在班级': 'class_name',
            '课程名称': 'course_name',
            '课程类型': 'course_type',
            '购买数量': 'purchased_amount',
            '赠送数量': 'gifted_amount',
            '消耗数量': 'consumed_amount',
            '退转数量': 'returned_amount',
            '剩余数量': 'remaining_amount',
            '超上数量': 'over_amount',
            '课消金额': 'consumed_fee',
            '剩余课消金额': 'remaining_fee',
            '缺课次数': 'absent_count',
            '跟进人': 'follow_up_person',
            '学管师': 'tutor',
            '性别': 'gender',
            '微信绑定状态': 'wechat_status',
            '绑卡状态': 'card_status',
            '人脸采集状态': 'face_status',
            '年级': 'grade',
            '学号': 'student_id',
            '学校': 'school'
        }
        
        # 获取当前时间
        import_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 准备批量插入
        total_rows = len(df)
        insert_count = 0
        error_count = 0
        
        for i in range(0, total_rows, batch_size):
            batch_df = df.iloc[i:min(i+batch_size, total_rows)]
            
            for _, row in batch_df.iterrows():
                try:
                    # 准备列和值
                    columns = []
                    values = []
                    
                    for col in df.columns:
                        if col in column_mapping:
                            columns.append(column_mapping[col])
                            
                            # 根据类型处理值
                            if col in ['购买数量', '赠送数量', '消耗数量', '退转数量', '剩余数量', '超上数量', '缺课次数']:
                                values.append(int(float(row[col])))
                            elif col in ['课消金额', '剩余课消金额']:
                                values.append(float(row[col]))
                            else:
                                values.append(str(row[col]))
                    
                    # 添加导入时间
                    columns.append('import_date')
                    values.append(import_time)
                    
                    # 构建插入SQL语句
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join(columns)
                    sql = f"INSERT INTO student_courses ({columns_str}) VALUES ({placeholders})"
                    
                    # 执行插入
                    cursor.execute(sql, values)
                    insert_count += 1
                    
                except Error as e:
                    error_count += 1
                    print(f"插入数据时出错: {e}")
                    continue
            
            # 每批次提交一次
            conn.commit()
            print(f"已处理 {min(i+batch_size, total_rows)}/{total_rows} 条记录")
        
        print(f"数据导入完成。成功: {insert_count} 条，失败: {error_count} 条")
        return True
    
    except Error as e:
        print(f"导入数据时出错: {e}")
        return False

def main():
    # 获取MySQL连接信息
    host = input("请输入MySQL主机地址 (默认: localhost): ") or "localhost"
    user = input("请输入MySQL用户名 (默认: root): ") or "root"
    password = getpass.getpass("请输入MySQL密码: ")
    database = "student_management"
    
    # CSV文件路径
    csv_file = '学生报读课程20250506141730.csv'
    
    # 检查CSV文件是否存在
    if not os.path.exists(csv_file):
        print(f"错误: 找不到文件 {csv_file}")
        return
    
    try:
        # 连接到MySQL
        print(f"正在连接到MySQL服务器 {host}...")
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if conn.is_connected():
            print("MySQL连接成功")
            cursor = conn.cursor()
            
            # 创建数据库和表
            if create_database_and_table(conn, cursor, database):
                # 处理CSV文件
                df = process_csv_file(csv_file)
                
                if df is not None:
                    # 导入数据到MySQL
                    if import_to_mysql(df, conn, cursor):
                        print(f"成功将数据导入到 {database}.student_courses 表")
            
            # 关闭连接
            cursor.close()
            conn.close()
            print("MySQL连接已关闭")
        
    except Error as e:
        print(f"连接MySQL时出错: {e}")

if __name__ == "__main__":
    main()