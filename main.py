#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章Markdown创建生成器 - 优化版
通过GUI界面选择文章meta信息，自动生成Hugo格式的Markdown文件
支持记忆功能和自定义分类标签管理，采用可折叠UI设计
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml
import os
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Optional
from database import DatabaseManager

# 现代化UI配置
MODERN_STYLE = {
    'bg_color': '#f8f9fa',           # 浅灰背景
    'primary_color': '#4a90e2',    # 主色调 - 蓝色
    'secondary_color': '#6c757d',  # 次要色 - 灰色
    'success_color': '#28a745',      # 成功色 - 绿色
    'danger_color': '#dc3545',     # 危险色 - 红色
    'warning_color': '#ffc107',      # 警告色 - 黄色
    'text_color': '#343a40',         # 文本色 - 深灰
    'border_color': '#dee2e6',      # 边框色 - 浅灰
    'hover_color': '#e9ecef',        # 悬停色 - 更浅灰
    'font_family': 'Segoe UI',       # 字体
    'font_size_normal': 10,
    'font_size_large': 12,
    'font_size_small': 9,
    'border_radius': 8,              # 圆角
    'padding': 12,                   # 内边距
    'margin': 8                      # 外边距
}


class CollapsibleFrame(ttk.Frame):
    """现代化可折叠框架组件"""
    
    def __init__(self, parent, title="", expanded=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.expanded = expanded
        self.title = title
        
        # 配置框架样式
        self.configure(style='Modern.TFrame')
        
        # 创建标题栏 - 现代化样式
        self.header = ttk.Frame(self, style='Header.TFrame')
        self.header.pack(fill=tk.X, padx=0, pady=0)
        
        # 折叠/展开按钮 - 使用更美观的按钮
        self.toggle_button = ttk.Button(
            self.header, 
            text="▼" if expanded else "▶", 
            width=4,
            command=self.toggle,
            style='Collapse.TButton'
        )
        self.toggle_button.pack(side=tk.LEFT, padx=(6, 4), pady=4)
        
        # 标题标签 - 使用现代字体和颜色
        self.title_label = ttk.Label(
            self.header, 
            text=title, 
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_large'], 'bold'),
            foreground=MODERN_STYLE['primary_color'],
            style='Header.TLabel'
        )
        self.title_label.pack(side=tk.LEFT, pady=4)
        
        # 内容框架 - 添加边框和内边距
        self.content = ttk.Frame(self, style='Content.TFrame')
        if expanded:
            self.content.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        
    def toggle(self):
        """切换折叠状态"""
        self.expanded = not self.expanded
        if self.expanded:
            self.content.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
            self.toggle_button.config(text="▼")
        else:
            self.content.pack_forget()
            self.toggle_button.config(text="▶")


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self.after_id = None
    def show(self):
        if self.tip:
            return
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        def _create():
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            try:
                self.tip.attributes('-alpha', 0.98)
            except:
                pass
            self.tip.wm_geometry(f"+{x}+{y}")
            frame = ttk.Frame(self.tip, style='Tooltip.TFrame', padding=8)
            frame.pack(fill=tk.BOTH, expand=True)
            label = ttk.Label(frame, text=self.text, style='Tooltip.TLabel', wraplength=240)
            label.pack()
            self.tip.after(2500, self.hide)
        self.after_id = self.widget.after(200, _create)
    def hide(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        if self.tip:
            try:
                self.tip.destroy()
            except:
                pass
            self.tip = None

class ArticleMetaGenerator:
    """MD文章meta信息生成器主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MD文章meta信息生成器")
        self.root.geometry("590x680")  # 调整窗口大小，更紧凑
        self.root.configure(bg=MODERN_STYLE['bg_color'])
        
        # 配置现代化样式
        self.setup_modern_styles()
        
        # 初始化数据库
        self.db = DatabaseManager()
        
        # 从数据库加载配置
        self.load_config_from_db()
        
        # 当前选择的值
        self.current_values = {}
        
        self.setup_ui()
        self.load_recent_values()
        
    def setup_modern_styles(self):
        """配置现代化样式"""
        style = ttk.Style()
        
        # 配置主题颜色
        style.theme_use('clam')  # 使用clam主题作为基础
        
        # 框架样式
        style.configure('Modern.TFrame', 
                       background=MODERN_STYLE['bg_color'])
        
        style.configure('Header.TFrame', 
                       background='#ffffff',
                       relief='raised',
                       borderwidth=1)
        
        style.configure('Content.TFrame', 
                       background=MODERN_STYLE['bg_color'],
                       relief='flat',
                       borderwidth=0)
        
        # 按钮样式
        style.configure('Modern.TButton',
                       font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal']),
                       background=MODERN_STYLE['primary_color'],
                       foreground='white',
                       borderwidth=0,
                       focusthickness=3,
                       focuscolor='none',
                       padding=8)
        
        style.map('Modern.TButton',
                 background=[('active', '#357abd'), ('disabled', '#cccccc')],
                 foreground=[('disabled', '#666666')])
        
        # 折叠按钮样式
        style.configure('Collapse.TButton',
                       font=(MODERN_STYLE['font_family'], 9, 'bold'),
                       background='#f8f9fa',
                       foreground=MODERN_STYLE['primary_color'],
                       borderwidth=1,
                       padding=4,
                       width=4)
        
        style.map('Collapse.TButton',
                 background=[('active', '#e9ecef')])
        
        # 输入框样式
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       background='white',
                       foreground=MODERN_STYLE['text_color'],
                       borderwidth=1,
                       relief='solid',
                       padding=6)
        
        style.map('Modern.TEntry',
                 fieldbackground=[('focus', '#ffffff')],
                 bordercolor=[('focus', MODERN_STYLE['primary_color'])])
        
        # 标签样式
        style.configure('Modern.TLabel',
                       background=MODERN_STYLE['bg_color'],
                       foreground=MODERN_STYLE['text_color'],
                       font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal']))
        
        style.configure('Header.TLabel',
                       background='#ffffff',
                       foreground=MODERN_STYLE['primary_color'])
        
        # 复选框样式
        style.configure('Modern.TCheckbutton',
                       background=MODERN_STYLE['bg_color'],
                       foreground=MODERN_STYLE['text_color'],
                       font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal']))
        
        # 组合框样式
        style.configure('Modern.TCombobox',
                       fieldbackground='white',
                       background='white',
                       foreground=MODERN_STYLE['text_color'],
                       borderwidth=1,
                       padding=6)
        
        # 笔记本样式（标签页）
        style.configure('Modern.TNotebook',
                       background=MODERN_STYLE['bg_color'],
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab',
                       background='#e9ecef',
                       foreground=MODERN_STYLE['text_color'],
                       font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal']),
                       padding=[10, 6],
                       borderwidth=0)
        
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', 'white'), ('active', '#f8f9fa')],
                 foreground=[('selected', MODERN_STYLE['primary_color'])])
        
        # LabelFrame样式
        style.configure('Modern.TLabelframe',
                       background=MODERN_STYLE['bg_color'],
                       borderwidth=1,
                       relief='solid')
        
        style.configure('Modern.TLabelframe.Label',
                       background=MODERN_STYLE['bg_color'],
                       foreground=MODERN_STYLE['primary_color'],
                       font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_large'], 'bold'),
                       padding=6)

        style.configure('Hint.TLabel',
                       background=MODERN_STYLE['bg_color'],
                       foreground=MODERN_STYLE['secondary_color'],
                       font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_small']))

        style.configure('Tooltip.TFrame',
                        background='#ffffff',
                        borderwidth=1,
                        relief='solid')
        style.configure('Tooltip.TLabel',
                        background='#ffffff',
                        foreground=MODERN_STYLE['secondary_color'],
                        font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_small']))
        
    def load_config_from_db(self):
        """从数据库加载配置"""
        self.config = {
            'default_author': self.db.get_setting('default_author', 'Your Name'),
            'default_path': self.db.get_setting('default_path', 'content/posts/'),
            'default_language': self.db.get_setting('default_language', 'zh-cn'),
            'default_draft': self.db.get_setting('default_draft', 'true') == 'true',
            'default_toc_enable': self.db.get_setting('default_toc_enable', 'true') == 'true',
            'default_toc_auto': self.db.get_setting('default_toc_auto', 'true') == 'true',
            'default_lightgallery': self.db.get_setting('default_lightgallery', 'true') == 'true',
            'default_share_enable': self.db.get_setting('default_share_enable', 'true') == 'true',
            'default_comment_enable': self.db.get_setting('default_comment_enable', 'true') == 'true',
            'default_math_enable': self.db.get_setting('default_math_enable', 'false') == 'true'
        }
        
    def setup_ui(self):
        """设置现代化用户界面"""
        # 创建主框架 - 使用适中的内边距
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=12, pady=12)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建顶部工具栏 - 使用卡片式设计
        self.create_modern_toolbar(main_frame)
        
        # 创建Notebook用于标签页 - 使用现代化样式
        self.notebook = ttk.Notebook(main_frame, style='Modern.TNotebook')
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(12, 0))
        
        # 创建主界面标签页
        self.main_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(self.main_frame, text="📝 文章生成")
        
        # 配置主框架 - 添加滚动条支持
        self.setup_scrollable_frame(self.main_frame)
        
        # 创建配置管理标签页
        self.config_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(self.config_frame, text="⚙️ 配置管理")
        self.create_config_section(self.config_frame)
        
        # 创建历史记录标签页
        self.history_frame = ttk.Frame(self.notebook, style='Modern.TFrame')
        self.notebook.add(self.history_frame, text="📋 历史记录")
        self.create_history_section(self.history_frame)
        
    def setup_scrollable_frame(self, parent):
        """设置可滚动框架"""
        # 创建画布和滚动条
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 网格布局
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置权重
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # 在可滚动框架中创建内容
        self.create_main_content(scrollable_frame)
        
    # 保持原有的方法名但调用新的现代化方法
    def create_basic_info_section(self, parent):
        """兼容原有调用的方法"""
        self.create_modern_basic_info_section(parent)
        
    def create_classification_section(self, parent):
        """兼容原有调用的方法"""
        self.create_modern_classification_section(parent)
        
    def create_display_settings_section(self, parent):
        """兼容原有调用的方法"""
        self.create_modern_display_settings_section(parent)
        
    def create_advanced_section(self, parent):
        """兼容原有调用的方法"""
        self.create_modern_advanced_section(parent)
        
    def create_content_section(self, parent):
        """兼容原有调用的方法"""
        self.create_modern_content_section(parent)
        
    def create_toolbar(self, parent):
        """兼容原有调用的方法"""
        self.create_modern_toolbar(parent)
        
    def create_modern_toolbar(self, parent):
        """创建现代化顶部工具栏 - 更紧凑设计"""
        # 创建工具栏框架 - 卡片式设计
        toolbar_frame = ttk.Frame(parent, style='Modern.TFrame')
        toolbar_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 左侧操作按钮组
        button_frame = ttk.Frame(toolbar_frame, style='Modern.TFrame')
        button_frame.pack(side=tk.LEFT, padx=(0, 12))
        
        # 主要操作按钮 - 使用更紧凑的尺寸
        ttk.Button(
            button_frame, 
            text="🆕 新建", 
            command=self.clear_form,
            style='Modern.TButton'
        ).pack(side=tk.LEFT, padx=(0, 6))
        
        ttk.Button(
            button_frame, 
            text="👁️ 预览", 
            command=self.preview_article,
            style='Modern.TButton'
        ).pack(side=tk.LEFT, padx=(0, 6))
        
        ttk.Button(
            button_frame, 
            text="✨ 生成", 
            command=self.generate_article,
            style='Modern.TButton'
        ).pack(side=tk.LEFT, padx=(0, 6))
        
        # 右侧路径选择组
        path_frame = ttk.Frame(toolbar_frame, style='Modern.TFrame')
        path_frame.pack(side=tk.RIGHT, padx=(12, 0))
        
        ttk.Label(
            path_frame, 
            text="📁 路径:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        ).pack(side=tk.LEFT, padx=(0, 6))
        
        self.save_path_var = tk.StringVar(value=self.config['default_path'])
        entry_container = ttk.Frame(path_frame, style='Modern.TFrame')
        entry_container.pack(side=tk.LEFT, padx=(0, 6))

        path_entry = ttk.Entry(
            entry_container, 
            textvariable=self.save_path_var, 
            width=15,
            style='Modern.TEntry'
        )
        path_entry.pack(anchor=tk.W)

        tooltip = ToolTip(path_entry, "相对路径或绝对路径")
        path_entry.bind('<Enter>', lambda e: tooltip.show())
        path_entry.bind('<Leave>', lambda e: tooltip.hide())
        path_entry.bind('<FocusIn>', lambda e: tooltip.show())
        path_entry.bind('<FocusOut>', lambda e: tooltip.hide())
        
        ttk.Button(
            path_frame, 
            text="📂", 
            command=self.browse_path,
            style='Modern.TButton'
        ).pack(side=tk.LEFT)
        
    def create_main_content(self, parent):
        """创建现代化主内容区域"""
        # 基本信息（始终显示）- 使用卡片式设计
        basic_frame = ttk.LabelFrame(
            parent, 
            text="📋 基本信息", 
            padding="12",
            style='Modern.TLabelframe'
        )
        basic_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        basic_frame.columnconfigure(1, weight=1)
        
        self.create_modern_basic_info_section(basic_frame)
        
        # 使用可折叠框架组织复杂选项
        
        # 分类标签（可折叠）
        self.classification_frame = CollapsibleFrame(
            parent, 
            title="🏷️ 分类标签", 
            expanded=True
        )
        self.classification_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        self.create_modern_classification_section(self.classification_frame.content)
        
        # 展示设置（可折叠）
        self.display_frame = CollapsibleFrame(
            parent, 
            title="🎨 展示设置", 
            expanded=False
        )
        self.display_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        self.create_modern_display_settings_section(self.display_frame.content)
        
        # 高级选项（可折叠）
        self.advanced_frame = CollapsibleFrame(
            parent, 
            title="⚙️ 高级选项", 
            expanded=False
        )
        self.advanced_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        self.create_modern_advanced_section(self.advanced_frame.content)
        
        # 内容区域（可折叠）
        self.content_frame = CollapsibleFrame(
            parent, 
            title="📝 内容摘要", 
            expanded=True
        )
        self.content_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(1, weight=1)
        parent.rowconfigure(4, weight=1)
        self.create_modern_content_section(self.content_frame.content)
        
    def create_modern_basic_info_section(self, parent):
        """创建现代化基本信息区域 - 更紧凑设计"""
        row = 0
        
        # 标题 - 使用更紧凑的间距
        title_label = ttk.Label(
            parent, 
            text="📝 标题:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        title_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=5)
        
        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(
            parent, 
            textvariable=self.title_var, 
            width=45,  # 减小宽度
            style='Modern.TEntry',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        title_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        title_entry.bind('<KeyRelease>', self.on_title_change)
        row += 1
        
        # 子标题
        subtitle_label = ttk.Label(
            parent, 
            text="✏️ 子标题:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        subtitle_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=5)
        
        self.subtitle_var = tk.StringVar()
        subtitle_entry = ttk.Entry(
            parent, 
            textvariable=self.subtitle_var, 
            width=45,  # 减小宽度
            style='Modern.TEntry',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        subtitle_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 作者（带管理按钮）
        author_frame = ttk.Frame(parent, style='Modern.TFrame')
        author_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.author_var = tk.StringVar(value=self.config['default_author'])
        self.author_combo = ttk.Combobox(
            author_frame, 
            textvariable=self.author_var, 
            values=self.db.get_categories_by_type('author'), 
            width=35,  # 减小宽度
            style='Modern.TCombobox',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        self.author_combo.pack(side=tk.LEFT, padx=(0, 6))
        
        manage_author_btn = ttk.Button(
            author_frame, 
            text="👤 管理", 
            command=lambda: self.manage_categories('author'),
            style='Modern.TButton'
        )
        manage_author_btn.pack(side=tk.LEFT)
        
        author_label = ttk.Label(
            parent, 
            text="👤 作者:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        author_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=5)
        row += 1
        
        # 日期和状态
        date_frame = ttk.Frame(parent, style='Modern.TFrame')
        date_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.date_var = tk.StringVar(value=datetime.now().astimezone().isoformat(timespec='seconds'))
        date_entry = ttk.Entry(
            date_frame, 
            textvariable=self.date_var, 
            width=25,  # 减小宽度
            style='Modern.TEntry',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        date_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        self.draft_var = tk.BooleanVar(value=self.config['default_draft'])
        draft_check = ttk.Checkbutton(
            date_frame, 
            text="📝 草稿", 
            variable=self.draft_var,
            style='Modern.TCheckbutton'
        )
        draft_check.pack(side=tk.LEFT)
        
        date_label = ttk.Label(
            parent, 
            text="📅 日期:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        date_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=5)
        row += 1
        
        # 语言选择
        lang_frame = ttk.Frame(parent, style='Modern.TFrame')
        lang_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.zh_var = tk.BooleanVar(value=True)
        self.en_var = tk.BooleanVar(value=False)
        
        zh_check = ttk.Checkbutton(
            lang_frame, 
            text="🇨🇳 中文", 
            variable=self.zh_var,
            style='Modern.TCheckbutton'
        )
        zh_check.pack(side=tk.LEFT, padx=(0, 20))
        
        en_check = ttk.Checkbutton(
            lang_frame, 
            text="🇺🇸 英文", 
            variable=self.en_var,
            style='Modern.TCheckbutton'
        )
        en_check.pack(side=tk.LEFT)
        
        lang_label = ttk.Label(
            parent, 
            text="🌐 语言:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        lang_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=5)
        
    def create_modern_classification_section(self, parent):
        """创建现代化分类标签区域 - 更紧凑设计"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # 标签管理
        tag_label = ttk.Label(
            parent, 
            text="🏷️ 标签:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        tag_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=4)
        
        tags_frame = ttk.Frame(parent, style='Modern.TFrame')
        tags_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        
        self.tags_var = tk.StringVar()
        self.tags_combo = ttk.Combobox(
            tags_frame, 
            textvariable=self.tags_var, 
            values=self.db.get_categories_by_type('tag'), 
            width=35,  # 减小宽度
            style='Modern.TCombobox',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        self.tags_combo.pack(side=tk.LEFT, padx=(0, 6))
        
        manage_tags_btn = ttk.Button(
            tags_frame, 
            text="🏷️ 管理", 
            command=lambda: self.manage_categories('tag'),
            style='Modern.TButton'
        )
        manage_tags_btn.pack(side=tk.LEFT)
        row += 1
        
        # 分类管理
        category_label = ttk.Label(
            parent, 
            text="📂 分类:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        category_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=4)
        
        category_frame = ttk.Frame(parent, style='Modern.TFrame')
        category_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            category_frame, 
            textvariable=self.category_var, 
            values=self.db.get_categories_by_type('category'), 
            width=40,
            style='Modern.TCombobox',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        self.category_combo.pack(side=tk.LEFT, padx=(0, 8))
        
        manage_category_btn = ttk.Button(
            category_frame, 
            text="📂 管理", 
            command=lambda: self.manage_categories('category'),
            style='Modern.TButton'
        )
        manage_category_btn.pack(side=tk.LEFT)
        row += 1
        
        # 系列管理
        series_label = ttk.Label(
            parent, 
            text="📚 系列:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        series_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=4)
        
        series_frame = ttk.Frame(parent, style='Modern.TFrame')
        series_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        
        self.series_var = tk.StringVar()
        self.series_combo = ttk.Combobox(
            series_frame, 
            textvariable=self.series_var, 
            values=self.db.get_categories_by_type('series'), 
            width=40,
            style='Modern.TCombobox',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        self.series_combo.pack(side=tk.LEFT, padx=(0, 8))
        
        manage_series_btn = ttk.Button(
            series_frame, 
            text="📚 管理", 
            command=lambda: self.manage_categories('series'),
            style='Modern.TButton'
        )
        manage_series_btn.pack(side=tk.LEFT)
        row += 1
        
        # 系列权重
        weight_label = ttk.Label(
            parent, 
            text="⚖️ 系列权重:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        weight_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=4)
        
        self.series_weight_var = tk.StringVar(value="")
        weight_entry = ttk.Entry(
            parent, 
            textvariable=self.series_weight_var, 
            width=18,
            style='Modern.TEntry',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        weight_entry.grid(row=row, column=1, sticky=tk.W, pady=4)
        
    def create_modern_display_settings_section(self, parent):
        """创建现代化展示设置区域"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # 目录设置 - 使用现代化的框架
        toc_frame = ttk.LabelFrame(
            parent, 
            text="📑 目录设置", 
            padding="8",
            style='Modern.TLabelframe'
        )
        toc_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), padx=(0, 12), pady=6)
        
        self.toc_enable_var = tk.BooleanVar(value=self.config['default_toc_enable'])
        self.toc_auto_var = tk.BooleanVar(value=self.config['default_toc_auto'])
        
        toc_enable_check = ttk.Checkbutton(
            toc_frame, 
            text="✅ 启用目录", 
            variable=self.toc_enable_var,
            style='Modern.TCheckbutton'
        )
        toc_enable_check.pack(anchor=tk.W, pady=4)
        
        toc_auto_check = ttk.Checkbutton(
            toc_frame, 
            text="🤖 自动目录", 
            variable=self.toc_auto_var,
            style='Modern.TCheckbutton'
        )
        toc_auto_check.pack(anchor=tk.W, pady=4)
        
        # 功能开关 - 使用现代化的框架
        func_frame = ttk.LabelFrame(
            parent, 
            text="🔧 功能开关", 
            padding="8",
            style='Modern.TLabelframe'
        )
        func_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 12), pady=6)
        
        self.lightgallery_var = tk.BooleanVar(value=self.config['default_lightgallery'])
        self.share_var = tk.BooleanVar(value=self.config['default_share_enable'])
        self.comment_var = tk.BooleanVar(value=self.config['default_comment_enable'])
        self.math_var = tk.BooleanVar(value=self.config['default_math_enable'])
        
        lightgallery_check = ttk.Checkbutton(
            func_frame, 
            text="🖼️ 图片画廊", 
            variable=self.lightgallery_var,
            style='Modern.TCheckbutton'
        )
        lightgallery_check.pack(anchor=tk.W, pady=4)
        
        share_check = ttk.Checkbutton(
            func_frame, 
            text="📤 分享功能", 
            variable=self.share_var,
            style='Modern.TCheckbutton'
        )
        share_check.pack(anchor=tk.W, pady=4)
        
        comment_check = ttk.Checkbutton(
            func_frame, 
            text="💬 评论功能", 
            variable=self.comment_var,
            style='Modern.TCheckbutton'
        )
        comment_check.pack(anchor=tk.W, pady=4)
        
        math_check = ttk.Checkbutton(
            func_frame, 
            text="🔢 数学公式", 
            variable=self.math_var,
            style='Modern.TCheckbutton'
        )
        math_check.pack(anchor=tk.W, pady=4)
        
        # 特色图片 - 使用现代化的框架
        img_frame = ttk.LabelFrame(
            parent, 
            text="🖼️ 特色图片", 
            padding="8",
            style='Modern.TLabelframe'
        )
        img_frame.grid(row=row, column=2, sticky=(tk.W, tk.E), pady=6)
        
        featured_img_label = ttk.Label(
            img_frame, 
            text="特色图:", 
            style='Modern.TLabel'
        )
        featured_img_label.pack(anchor=tk.W)
        
        self.featured_image_var = tk.StringVar()
        featured_img_entry = ttk.Entry(
            img_frame, 
            textvariable=self.featured_image_var, 
            width=25,
            style='Modern.TEntry'
        )
        featured_img_entry.pack(anchor=tk.W, pady=(0, 8))
        
        preview_img_label = ttk.Label(
            img_frame, 
            text="预览图:", 
            style='Modern.TLabel'
        )
        preview_img_label.pack(anchor=tk.W)
        
        self.featured_image_preview_var = tk.StringVar()
        preview_img_entry = ttk.Entry(
            img_frame, 
            textvariable=self.featured_image_preview_var, 
            width=25,
            style='Modern.TEntry'
        )
        preview_img_entry.pack(anchor=tk.W)
        
    def create_modern_advanced_section(self, parent):
        """创建现代化高级选项区域"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # 许可证
        license_label = ttk.Label(
            parent, 
            text="📄 许可证:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        license_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=4)
        
        self.license_var = tk.StringVar()
        license_combo = ttk.Combobox(
            parent, 
            textvariable=self.license_var, 
            values=['CC BY-SA 4.0', 'MIT', 'Apache 2.0', ''], 
            width=25,
            style='Modern.TCombobox',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'])
        )
        license_combo.grid(row=row, column=1, sticky=tk.W, pady=4)
        row += 1
        
        # 自定义字段
        custom_label = ttk.Label(
            parent, 
            text="🔧 自定义字段:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        custom_label.grid(row=row, column=0, sticky=tk.W, padx=(0, 12), pady=4)
        
        self.custom_fields_text = tk.Text(
            parent, 
            height=3, 
            width=45,
            bg='white',
            fg=MODERN_STYLE['text_color'],
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal']),
            relief='solid',
            borderwidth=1,
            highlightbackground=MODERN_STYLE['border_color'],
            highlightcolor=MODERN_STYLE['primary_color'],
            highlightthickness=1
        )
        self.custom_fields_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        
        # 添加占位符文本
        placeholder_text = "# 自定义YAML字段\n# 例如:\n# keywords: [\"AI\", \"机器学习\"]\n# aliases: [\"alternative-title\"]"
        self.custom_fields_text.insert('1.0', placeholder_text)
        self.custom_fields_text.config(fg='gray')
        
        def on_focus_in(event):
            if self.custom_fields_text.get('1.0', tk.END).strip() == placeholder_text.strip():
                self.custom_fields_text.delete('1.0', tk.END)
                self.custom_fields_text.config(fg=MODERN_STYLE['text_color'])
                
        def on_focus_out(event):
            if not self.custom_fields_text.get('1.0', tk.END).strip():
                self.custom_fields_text.insert('1.0', placeholder_text)
                self.custom_fields_text.config(fg='gray')
                
        self.custom_fields_text.bind('<FocusIn>', on_focus_in)
        self.custom_fields_text.bind('<FocusOut>', on_focus_out)
        
    def create_modern_content_section(self, parent):
        """创建现代化内容区域"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # 摘要标签
        desc_label = ttk.Label(
            parent, 
            text="📝 摘要:", 
            style='Modern.TLabel',
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal'], 'bold')
        )
        desc_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 6))
        
        # 摘要文本框 - 现代化样式
        self.description_text = tk.Text(
            parent, 
            height=5, 
            width=65,
            bg='white',
            fg=MODERN_STYLE['text_color'],
            font=(MODERN_STYLE['font_family'], MODERN_STYLE['font_size_normal']),
            relief='solid',
            borderwidth=1,
            highlightbackground=MODERN_STYLE['border_color'],
            highlightcolor=MODERN_STYLE['primary_color'],
            highlightthickness=1
        )
        self.description_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        
        # 添加滚动条 - 现代化样式
        desc_scrollbar = ttk.Scrollbar(
            parent, 
            orient=tk.VERTICAL, 
            command=self.description_text.yview,
            style='Modern.Vertical.TScrollbar'
        )
        desc_scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        
    def create_display_settings_section(self, parent):
        """创建展示设置区域"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # 目录设置
        toc_frame = ttk.LabelFrame(parent, text="目录设置", padding="5")
        toc_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        self.toc_enable_var = tk.BooleanVar(value=self.config['default_toc_enable'])
        self.toc_auto_var = tk.BooleanVar(value=self.config['default_toc_auto'])
        
        ttk.Checkbutton(toc_frame, text="启用目录", variable=self.toc_enable_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(toc_frame, text="自动目录", variable=self.toc_auto_var).pack(anchor=tk.W, pady=2)
        
        # 功能开关
        func_frame = ttk.LabelFrame(parent, text="功能开关", padding="5")
        func_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        self.lightgallery_var = tk.BooleanVar(value=self.config['default_lightgallery'])
        self.share_var = tk.BooleanVar(value=self.config['default_share_enable'])
        self.comment_var = tk.BooleanVar(value=self.config['default_comment_enable'])
        self.math_var = tk.BooleanVar(value=self.config['default_math_enable'])
        
        ttk.Checkbutton(func_frame, text="图片画廊", variable=self.lightgallery_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(func_frame, text="分享功能", variable=self.share_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(func_frame, text="评论功能", variable=self.comment_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(func_frame, text="数学公式", variable=self.math_var).pack(anchor=tk.W, pady=2)
        
        # 特色图片
        img_frame = ttk.LabelFrame(parent, text="特色图片", padding="5")
        img_frame.grid(row=row, column=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(img_frame, text="特色图:").pack(anchor=tk.W)
        self.featured_image_var = tk.StringVar()
        ttk.Entry(img_frame, textvariable=self.featured_image_var, width=25).pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(img_frame, text="预览图:").pack(anchor=tk.W)
        self.featured_image_preview_var = tk.StringVar()
        ttk.Entry(img_frame, textvariable=self.featured_image_preview_var, width=25).pack(anchor=tk.W)
        
    def create_advanced_section(self, parent):
        """创建高级选项区域"""
        parent.columnconfigure(1, weight=1)
        row = 0
        
        # 许可证
        ttk.Label(parent, text="许可证:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10))
        self.license_var = tk.StringVar()
        license_combo = ttk.Combobox(parent, textvariable=self.license_var, 
                                   values=['CC BY-SA 4.0', 'MIT', 'Apache 2.0', ''], width=30)
        license_combo.grid(row=row, column=1, sticky=tk.W, pady=2)
        row += 1
        
        # 自定义字段
        ttk.Label(parent, text="自定义字段:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10))
        self.custom_fields_text = tk.Text(parent, height=4, width=50)
        self.custom_fields_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 添加占位符文本
        self.custom_fields_text.insert('1.0', "# 自定义YAML字段\n# 例如:\n# keywords: [\"AI\", \"机器学习\"]\n# aliases: [\"alternative-title\"]")
        self.custom_fields_text.config(fg='gray')
        
        def on_focus_in(event):
            if self.custom_fields_text.get('1.0', tk.END).strip() == "# 自定义YAML字段\n# 例如:\n# keywords: [\"AI\", \"机器学习\"]\n# aliases: [\"alternative-title\"]":
                self.custom_fields_text.delete('1.0', tk.END)
                self.custom_fields_text.config(fg='black')
                
        def on_focus_out(event):
            if not self.custom_fields_text.get('1.0', tk.END).strip():
                self.custom_fields_text.insert('1.0', "# 自定义YAML字段\n# 例如:\n# keywords: [\"AI\", \"机器学习\"]\n# aliases: [\"alternative-title\"]")
                self.custom_fields_text.config(fg='gray')
                
        self.custom_fields_text.bind('<FocusIn>', on_focus_in)
        self.custom_fields_text.bind('<FocusOut>', on_focus_out)
        
    def create_content_section(self, parent):
        """创建内容区域"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # 摘要
        ttk.Label(parent, text="摘要:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.description_text = tk.Text(parent, height=6, width=70)
        self.description_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 添加滚动条
        desc_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.description_text.yview)
        desc_scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.description_text.configure(yscrollcommand=desc_scrollbar.set)
        
    def create_config_section(self, parent):
        """创建配置管理区域"""
        parent.columnconfigure(1, weight=1)
        
        # 基本配置（可折叠）
        basic_config_frame = CollapsibleFrame(parent, title="基本配置 ▼", expanded=True)
        basic_config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.create_basic_config_section(basic_config_frame.content)
        
        # 功能开关配置（可折叠）
        switch_config_frame = CollapsibleFrame(parent, title="功能开关配置 ▼", expanded=False)
        switch_config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.create_switch_config_section(switch_config_frame.content)
        
        # 保存按钮
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, sticky=tk.W, pady=(20, 0))
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="重置为默认值", command=self.reset_config).pack(side=tk.LEFT, padx=(10, 0))
        
    def create_basic_config_section(self, parent):
        """创建基本配置区域"""
        row = 0
        
        # 默认作者
        ttk.Label(parent, text="默认作者:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.default_author_var = tk.StringVar(value=self.config['default_author'])
        ttk.Entry(parent, textvariable=self.default_author_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # 默认路径
        ttk.Label(parent, text="默认路径:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.default_path_var = tk.StringVar(value=self.config['default_path'])
        ttk.Entry(parent, textvariable=self.default_path_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # 默认语言
        ttk.Label(parent, text="默认语言:").grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        self.default_language_var = tk.StringVar(value=self.config['default_language'])
        ttk.Combobox(parent, textvariable=self.default_language_var, 
                    values=['zh-cn', 'en'], width=10).grid(row=row, column=1, sticky=tk.W, pady=5)
        
    def create_switch_config_section(self, parent):
        """创建开关配置区域"""
        # 默认开关设置
        self.default_draft_config_var = tk.BooleanVar(value=self.config['default_draft'])
        self.default_toc_enable_config_var = tk.BooleanVar(value=self.config['default_toc_enable'])
        self.default_toc_auto_config_var = tk.BooleanVar(value=self.config['default_toc_auto'])
        self.default_lightgallery_config_var = tk.BooleanVar(value=self.config['default_lightgallery'])
        self.default_share_config_var = tk.BooleanVar(value=self.config['default_share_enable'])
        self.default_comment_config_var = tk.BooleanVar(value=self.config['default_comment_enable'])
        self.default_math_config_var = tk.BooleanVar(value=self.config['default_math_enable'])
        
        # 分两列排列
        col1_frame = ttk.Frame(parent)
        col1_frame.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        col2_frame = ttk.Frame(parent)
        col2_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Checkbutton(col1_frame, text="默认草稿", variable=self.default_draft_config_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(col1_frame, text="默认启用目录", variable=self.default_toc_enable_config_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(col1_frame, text="默认自动目录", variable=self.default_toc_auto_config_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(col1_frame, text="默认图片画廊", variable=self.default_lightgallery_config_var).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(col2_frame, text="默认分享功能", variable=self.default_share_config_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(col2_frame, text="默认评论功能", variable=self.default_comment_config_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(col2_frame, text="默认数学公式", variable=self.default_math_config_var).pack(anchor=tk.W, pady=2)
        
    def create_history_section(self, parent):
        """创建历史记录区域"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # 历史记录列表
        list_frame = ttk.Frame(parent)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.history_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.SINGLE, height=15)
        self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.history_listbox.yview)
        
        # 按钮框架
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, sticky=tk.W)
        
        ttk.Button(button_frame, text="加载选中记录", command=self.load_selected_history).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_history).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="清空历史", command=self.clear_history).pack(side=tk.LEFT)
        
        # 加载历史记录
        self.refresh_history()
        
    def load_recent_values(self):
        """加载最近使用的值"""
        recent_history = self.db.get_recent_history(1)
        if recent_history:
            latest = recent_history[0]
            # 这里可以自动填充一些字段，或者提供快速选择的选项
            pass
            
    def refresh_history(self):
        """刷新历史记录列表"""
        self.history_listbox.delete(0, tk.END)
        history = self.db.get_recent_history(20)
        
        for record in history:
            display_text = f"{record['title']} - {record['author']} - {record['created_at'][:10]}"
            self.history_listbox.insert(tk.END, display_text)
            
        # 保存完整的记录数据
        self.history_data = history
        
    def load_selected_history(self):
        """加载选中的历史记录"""
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.history_data):
                record = self.history_data[index]
                # 填充表单
                self.title_var.set(record.get('title', ''))
                self.subtitle_var.set(record.get('subtitle', ''))
                self.author_var.set(record.get('author', ''))
                self.category_var.set(record.get('category', ''))
                self.series_var.set(record.get('series', ''))
                
                # 切换到主界面
                self.notebook.select(0)
                
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？"):
            # 这里可以添加清空数据库的逻辑
            self.refresh_history()
            
    def on_title_change(self, event):
        """标题改变时的处理"""
        title = self.title_var.get()
        if title:
            # 自动生成slug并显示（可选）
            slug = self.generate_slug(title)
            # 可以在界面某个地方显示生成的slug
            
    def browse_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory(title="选择保存路径")
        if path:
            self.save_path_var.set(path)
            
    def generate_slug(self, title: str) -> str:
        """根据标题生成slug"""
        if not title:
            return "untitled"
            
        # 简单的拼音转换（实际项目中可以使用pypinyin库）
        slug = title.lower()
        
        # 移除特殊字符，替换空格为连字符
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        
        return slug.strip('-')
        
    def parse_custom_fields(self) -> Dict:
        """解析自定义字段"""
        content = self.custom_fields_text.get('1.0', tk.END).strip()
        if not content or content.startswith('#'):
            return {}
            
        try:
            # 尝试解析YAML格式的自定义字段
            custom_data = yaml.safe_load(content)
            return custom_data if isinstance(custom_data, dict) else {}
        except:
            return {}
            
    def generate_front_matter(self, lang: str = 'zh-cn') -> str:
        """生成Front Matter"""
        # 更新分类使用次数
        if self.author_var.get():
            self.db.update_category_usage(self.author_var.get(), 'author')
        if self.tags_var.get():
            self.db.update_category_usage(self.tags_var.get(), 'tag')
        if self.category_var.get():
            self.db.update_category_usage(self.category_var.get(), 'category')
        if self.series_var.get():
            self.db.update_category_usage(self.series_var.get(), 'series')
            
        front_matter = {
            'title': self.title_var.get(),
            'subtitle': self.subtitle_var.get(),
            'date': self.date_var.get(),
            'lastmod': self.date_var.get(),
            'draft': self.draft_var.get(),
            'authors': [self.author_var.get()] if self.author_var.get() else [],
            'description': self.description_text.get('1.0', tk.END).strip(),
            'tags': [self.tags_var.get()] if self.tags_var.get() else [],
            'categories': [self.category_var.get()] if self.category_var.get() else [],
            'series': [self.series_var.get()] if self.series_var.get() else [],
            'hiddenFromHomePage': False,
            'hiddenFromSearch': False,
            'toc': {
                'enable': self.toc_enable_var.get(),
                'auto': self.toc_auto_var.get()
            },
            'lightgallery': self.lightgallery_var.get(),
            'share': {
                'enable': self.share_var.get()
            },
            'comment': {
                'enable': self.comment_var.get()
            },
            'math': {
                'enable': self.math_var.get()
            },
            'license': (self.license_var.get() if hasattr(self, 'license_var') and self.license_var.get() else ""),
            'featuredImage': (self.featured_image_var.get() if self.featured_image_var.get() else ""),
            'featuredImagePreview': (self.featured_image_preview_var.get() if self.featured_image_preview_var.get() else "")
        }
        
        # 添加自定义字段
        custom_fields = self.parse_custom_fields()
        front_matter.update(custom_fields)
        
        # 移除空值（保留空数组/空字符串以符合模板示例）
        front_matter = {k: v for k, v in front_matter.items() if v is not None}
        
        # 生成YAML格式的Front Matter
        yaml_content = yaml.dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return f"---\n{yaml_content}---\n"
        
    def preview_article(self):
        """预览文章"""
        if not self.title_var.get():
            messagebox.showwarning("警告", "请输入标题")
            return
            
        preview_window = tk.Toplevel(self.root)
        preview_window.title("预览")
        preview_window.geometry("700x600")
        
        # 创建带滚动条的预览窗口
        preview_frame = ttk.Frame(preview_window, padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        preview_text = tk.Text(preview_frame, wrap=tk.WORD)
        preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(preview_text, orient=tk.VERTICAL, command=preview_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        preview_text.configure(yscrollcommand=scrollbar.set)
        
        # 生成预览内容
        front_matter = self.generate_front_matter()
        
        # 根据语言生成不同的内容
        if self.zh_var.get() and not self.en_var.get():
            content = f"{front_matter}<!--more-->\n\n## 摘要\n{self.description_text.get('1.0', tk.END).strip()}\n\n## 正文\n\n在这里添加正文内容...\n"
        elif self.en_var.get() and not self.zh_var.get():
            content = f"{front_matter}<!--more-->\n\n## Summary\n{self.description_text.get('1.0', tk.END).strip()}\n\n## Content\n\nAdd your content here...\n"
        else:
            content = f"{front_matter}<!--more-->\n\n## 摘要 / Summary\n{self.description_text.get('1.0', tk.END).strip()}\n\n## 正文 / Content\n\n在这里添加正文内容... / Add your content here...\n"
        
        preview_text.insert('1.0', content)
        preview_text.configure(state='disabled')
        
    def generate_article(self):
        """生成文章"""
        if not self.title_var.get():
            messagebox.showerror("错误", "标题不能为空")
            return
            
        # 生成slug
        slug = self.generate_slug(self.title_var.get())
        
        # 保存路径
        save_path = Path(self.save_path_var.get())
        
        try:
            # 确保目录存在
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 添加到历史记录
            languages = []
            if self.zh_var.get():
                languages.append('zh-cn')
            if self.en_var.get():
                languages.append('en')
                
            self.db.add_history(
                title=self.title_var.get(),
                subtitle=self.subtitle_var.get(),
                author=self.author_var.get(),
                tags=[self.tags_var.get()] if self.tags_var.get() else [],
                category=self.category_var.get(),
                series=self.series_var.get(),
                language=','.join(languages),
                save_path=str(save_path)
            )
            
            # 生成中文版本
            if self.zh_var.get():
                zh_content = self.generate_front_matter('zh-cn')
                zh_content += "<!--more-->\n\n## 摘要\n" + self.description_text.get('1.0', tk.END).strip() + "\n\n## 正文\n\n在这里添加正文内容...\n"
                
                zh_file = save_path / f"{slug}.zh-cn.md"
                with open(zh_file, 'w', encoding='utf-8') as f:
                    f.write(zh_content)
                    
            # 生成英文版本
            if self.en_var.get():
                en_content = self.generate_front_matter('en')
                en_content += "<!--more-->\n\n## Summary\n" + self.description_text.get('1.0', tk.END).strip() + "\n\n## Content\n\nAdd your content here...\n"
                
                en_file = save_path / f"{slug}.en.md"
                with open(en_file, 'w', encoding='utf-8') as f:
                    f.write(en_content)
                    
            # 刷新历史记录
            self.refresh_history()
            
            messagebox.showinfo("成功", f"文章生成成功！\nSlug: {slug}\n路径: {save_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成文章失败: {str(e)}")
            
    def save_config(self):
        """保存配置"""
        try:
            # 保存到数据库
            self.db.set_setting('default_author', self.default_author_var.get())
            self.db.set_setting('default_path', self.default_path_var.get())
            self.db.set_setting('default_language', self.default_language_var.get())
            self.db.set_setting('default_draft', str(self.default_draft_config_var.get()).lower())
            self.db.set_setting('default_toc_enable', str(self.default_toc_enable_config_var.get()).lower())
            self.db.set_setting('default_toc_auto', str(self.default_toc_auto_config_var.get()).lower())
            self.db.set_setting('default_lightgallery', str(self.default_lightgallery_config_var.get()).lower())
            self.db.set_setting('default_share_enable', str(self.default_share_config_var.get()).lower())
            self.db.set_setting('default_comment_enable', str(self.default_comment_config_var.get()).lower())
            self.db.set_setting('default_math_enable', str(self.default_math_config_var.get()).lower())
            
            # 重新加载配置
            self.load_config_from_db()
            
            messagebox.showinfo("成功", "配置保存成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
            
    def reset_config(self):
        """重置为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有配置为默认值吗？"):
            self.default_author_var.set('Your Name')
            self.default_path_var.set('content/posts/')
            self.default_language_var.set('zh-cn')
            self.default_draft_config_var.set(True)
            self.default_toc_enable_config_var.set(True)
            self.default_toc_auto_config_var.set(True)
            self.default_lightgallery_config_var.set(True)
            self.default_share_config_var.set(True)
            self.default_comment_config_var.set(True)
            self.default_math_config_var.set(False)
            
    def clear_form(self):
        """清空表单"""
        self.title_var.set("")
        self.subtitle_var.set("")
        self.author_var.set(self.config['default_author'])
        self.draft_var.set(self.config['default_draft'])
        self.date_var.set(datetime.now().astimezone().isoformat(timespec='seconds'))
        self.tags_var.set("")
        self.category_var.set("")
        self.series_var.set("")
        self.series_weight_var.set("")
        self.description_text.delete('1.0', tk.END)
        self.featured_image_var.set("")
        self.featured_image_preview_var.set("")
        if hasattr(self, 'license_var'):
            self.license_var.set("")
        if hasattr(self, 'custom_fields_text'):
            self.custom_fields_text.delete('1.0', tk.END)
            self.custom_fields_text.insert('1.0', "# 自定义YAML字段\n# 例如:\n# keywords: [\"AI\", \"机器学习\"]\n# aliases: [\"alternative-title\"]")
            self.custom_fields_text.config(fg='gray')
        
    def run(self):
        """运行应用"""
        self.root.mainloop()

    def manage_categories(self, category_type: str):
        win = tk.Toplevel(self.root)
        win.title(f"管理 {category_type}")
        win.geometry("420x360")

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        values = self.db.get_categories_by_type(category_type)
        listbox = tk.Listbox(frame, height=12)
        listbox.pack(fill=tk.BOTH, expand=True)
        for v in values:
            listbox.insert(tk.END, v)

        entry = ttk.Entry(frame)
        entry.pack(fill=tk.X, pady=6)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X)

        def refresh():
            listbox.delete(0, tk.END)
            new_vals = self.db.get_categories_by_type(category_type)
            for v in new_vals:
                listbox.insert(tk.END, v)
            if category_type == 'author' and hasattr(self, 'author_combo'):
                self.author_combo.configure(values=new_vals)
            elif category_type == 'tag' and hasattr(self, 'tags_combo'):
                self.tags_combo.configure(values=new_vals)
            elif category_type == 'category' and hasattr(self, 'category_combo'):
                self.category_combo.configure(values=new_vals)
            elif category_type == 'series' and hasattr(self, 'series_combo'):
                self.series_combo.configure(values=new_vals)

        def on_add():
            name = entry.get().strip()
            if not name:
                return
            self.db.add_category(name, category_type)
            entry.delete(0, tk.END)
            refresh()

        def on_delete():
            sel = listbox.curselection()
            if not sel:
                return
            name = listbox.get(sel[0])
            self.db.delete_category(name, category_type)
            refresh()

        ttk.Button(btns, text="添加", command=on_add).pack(side=tk.LEFT)
        ttk.Button(btns, text="删除", command=on_delete).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="关闭", command=win.destroy).pack(side=tk.RIGHT)


if __name__ == "__main__":
    app = ArticleMetaGenerator()
    app.run()