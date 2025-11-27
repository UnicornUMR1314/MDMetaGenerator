import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os


class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "article_generator.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建分类标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,  -- 'tag', 'category', 'author'
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建历史记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subtitle TEXT,
                author TEXT,
                tags TEXT,  -- JSON array
                category TEXT,
                series TEXT,
                language TEXT,
                save_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认数据
        self.insert_default_data(cursor)
        
        conn.commit()
        conn.close()
        
    def insert_default_data(self, cursor):
        """插入默认数据"""
        # 默认标签
        default_tags = ['技术', '教程', '笔记', '思考', '生活', '其他']
        for tag in default_tags:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)
            ''', (tag, 'tag'))
            
        # 默认分类
        default_categories = ['前端', '后端', '全栈', '工具', '随笔']
        for category in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)
            ''', (category, 'category'))
            
        # 默认作者
        default_authors = ['Your Name', 'Admin', 'Guest']
        for author in default_authors:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)
            ''', (author, 'author'))
            
        
            
        # 默认设置
        default_settings = {
            'default_author': 'Your Name',
            'default_path': 'content/posts/',
            'default_language': 'zh-cn',
            'default_draft': 'true',
            'default_toc_enable': 'true',
            'default_toc_auto': 'true',
            'default_lightgallery': 'true',
            'default_share_enable': 'true',
            'default_comment_enable': 'true',
            'default_math_enable': 'false'
        }
        
        for key, value in default_settings.items():
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))
            
    def get_categories_by_type(self, category_type: str) -> List[str]:
        """获取指定类型的分类列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name FROM categories 
            WHERE type = ? 
            ORDER BY usage_count DESC, last_used DESC
        ''', (category_type,))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results
        
    def add_category(self, name: str, category_type: str) -> bool:
        """添加新的分类"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO categories (name, type) VALUES (?, ?)
            ''', (name, category_type))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def delete_category(self, name: str, category_type: str) -> bool:
        """删除分类"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM categories WHERE name = ? AND type = ?
        ''', (name, category_type))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
        
    def update_category_usage(self, name: str, category_type: str):
        """更新分类使用次数和最后使用时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE categories 
            SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE name = ? AND type = ?
        ''', (name, category_type))
        
        conn.commit()
        conn.close()
        
    def get_setting(self, key: str, default_value: str = None) -> str:
        """获取设置值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else default_value
        
    def set_setting(self, key: str, value: str):
        """设置配置值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
        
    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """获取最近的历史记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, subtitle, author, tags, category, series, language, save_path, created_at
            FROM history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'title': row[0],
                'subtitle': row[1],
                'author': row[2],
                'tags': json.loads(row[3]) if row[3] else [],
                'category': row[4],
                'series': row[5],
                'language': row[6],
                'save_path': row[7],
                'created_at': row[8]
            })
            
        conn.close()
        return results
        
    def add_history(self, title: str, subtitle: str, author: str, tags: List[str], 
                   category: str, series: str, language: str, save_path: str):
        """添加历史记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO history (title, subtitle, author, tags, category, series, language, save_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, subtitle, author, json.dumps(tags), category, series, language, save_path))
        
        conn.commit()
        conn.close()
        
    def search_categories(self, query: str, category_type: str) -> List[str]:
        """搜索分类"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name FROM categories 
            WHERE type = ? AND name LIKE ?
            ORDER BY usage_count DESC, last_used DESC
        ''', (category_type, f'%{query}%'))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results
