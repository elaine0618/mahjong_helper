import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageGrab, ImageTk
import os
import cv2
import numpy as np
import json
from mahjong_probability import calculate_tile_risk, get_discard_advice

class ExcludeRegion(tk.Toplevel):
    """排除区域窗口，用于排除中间转盘"""
    def __init__(self, parent, width=100, height=100, x=200, y=200):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.configure(bg='red')
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)

        self.drag_start_x = None
        self.drag_start_y = None

        self.resizing = False
        self.resize_edge = None
        self.resize_start_x = None
        self.resize_start_y = None
        self.resize_start_w = None
        self.resize_start_h = None
        self.resize_start_abs_x = None
        self.resize_start_abs_y = None


        self.bind('<Enter>', self.on_enter)
        self.bind('<Motion>', self.on_motion)
        self.bind('<Button-1>', self.start_resize)
        self.bind('<B1-Motion>', self.do_resize)
        self.bind('<ButtonRelease-1>', self.stop_resize)

        self.current_cursor = 'arrow'
             
    def on_enter(self, event):
        self.on_motion(event)

    def on_motion(self, event):
        if self.resizing:
            return
        x, y = event.x, event.y
        w = self.winfo_width()
        h = self.winfo_height()
        edge = 8

        on_left = x < edge
        on_right = x > w - edge
        on_top = y < edge
        on_bottom = y > h - edge

        if on_left and on_top:
            cursor = 'top_left_corner'
        elif on_left and on_bottom:
            cursor = 'bottom_left_corner'
        elif on_right and on_top:
            cursor = 'top_right_corner'
        elif on_right and on_bottom:
            cursor = 'bottom_right_corner'
        elif on_left:
            cursor = 'left_side'
        elif on_right:
            cursor = 'right_side'
        elif on_top:
            cursor = 'top_side'
        elif on_bottom:
            cursor = 'bottom_side'
        else:
            cursor = 'arrow'

        if cursor != self.current_cursor:
            try:
                self.configure(cursor=cursor)
                self.current_cursor = cursor
            except:
                self.configure(cursor='arrow')
                self.current_cursor = 'arrow'

    def start_resize(self, event):
        if self.resizing:
            return
        x, y = event.x, event.y
        w = self.winfo_width()
        h = self.winfo_height()
        edge = 8
        
        on_left = x < edge
        on_right = x > w - edge
        on_top = y < edge
        on_bottom = y > h - edge
        
        if not (on_left or on_right or on_top or on_bottom):
            return
            
        self.resizing = True
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_w = self.winfo_width()
        self.resize_start_h = self.winfo_height()
        self.resize_start_abs_x = self.winfo_x()
        self.resize_start_abs_y = self.winfo_y()
        
        if on_left and on_top:
            self.resize_edge = 'nw'
        elif on_left and on_bottom:
            self.resize_edge = 'sw'
        elif on_right and on_top:
            self.resize_edge = 'ne'
        elif on_right and on_bottom:
            self.resize_edge = 'se'
        elif on_left:
            self.resize_edge = 'w'
        elif on_right:
            self.resize_edge = 'e'
        elif on_top:
            self.resize_edge = 'n'
        elif on_bottom:
            self.resize_edge = 's'
            
    def do_resize(self, event):
        if not self.resizing:
            return
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y

        new_w = self.resize_start_w
        new_h = self.resize_start_h
        new_x = self.resize_start_abs_x
        new_y = self.resize_start_abs_y

        edge = self.resize_edge
        if 'w' in edge:
            new_w = max(50, self.resize_start_w - dx)
            new_x = self.resize_start_abs_x + (self.resize_start_w - new_w)
        if 'e' in edge:
            new_w = max(50, self.resize_start_w + dx)
        if 'n' in edge:
            new_h = max(50, self.resize_start_h - dy)
            new_y = self.resize_start_abs_y + (self.resize_start_h - new_h)
        if 's' in edge:
            new_h = max(50, self.resize_start_h + dy)

        self.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")
        self.update_idletasks()

    def stop_resize(self, event):
        self.resizing = False
        self.resize_edge = None
        self.on_motion(event)

    def get_region_bbox(self):
        """获取窗口内边界"""
        x = self.winfo_x()
        y = self.winfo_y()
        width = self.winfo_width()
        height = self.winfo_height()
        return (x, y, x + width, y + height)

class GreenBorderResizableRect(tk.Toplevel):
    """识别区域窗口"""
    def __init__(self, parent, title_text, width, height, x, y):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.configure(bg='black')
        self.attributes('-transparentcolor', 'black')
        self.attributes('-topmost', True)

        self.drag_start_x = None
        self.drag_start_y = None

        self.resizing = False
        self.resize_edge = None
        self.resize_start_x = None
        self.resize_start_y = None
        self.resize_start_w = None
        self.resize_start_h = None
        self.resize_start_abs_x = None
        self.resize_start_abs_y = None

        self.container = tk.Frame(self, bg='black')
        self.container.pack(fill='both', expand=True)

        self.title_bar = tk.Frame(self.container, bg='#333333', height=24, cursor='fleur')
        self.title_bar.pack(fill='x', side='top')
        self.title_bar.pack_propagate(False)

        self.title_label = tk.Label(self.title_bar, text=title_text, bg='#333333', fg='white', font=('Arial', 10, 'bold'))
        self.title_label.pack(side='left', padx=10)

        border_width = 4
        border_color = '#00FF00'
        
        self.left_border = tk.Frame(self.container, bg=border_color, width=border_width)
        self.left_border.place(x=0, y=24, width=border_width, relheight=1, height=-24)
        
        self.right_border = tk.Frame(self.container, bg=border_color, width=border_width)
        self.right_border.place(relx=1.0, x=-border_width, y=24, width=border_width, relheight=1, height=-24)
        
        self.top_border = tk.Frame(self.container, bg=border_color, height=border_width)
        self.top_border.place(x=border_width, y=24, relwidth=1, width=-2*border_width, height=border_width)
        
        self.bottom_border = tk.Frame(self.container, bg=border_color, height=border_width)
        self.bottom_border.place(x=border_width, rely=1.0, y=-border_width, relwidth=1, width=-2*border_width, height=border_width)

        self.label_widgets = []

        self.title_bar.bind('<Button-1>', self.start_drag)
        self.title_bar.bind('<B1-Motion>', self.do_drag)
        self.title_bar.bind('<ButtonRelease-1>', self.stop_drag)

        self.bind('<Enter>', self.on_enter)
        self.bind('<Motion>', self.on_motion)
        self.bind('<Button-1>', self.start_resize)
        self.bind('<B1-Motion>', self.do_resize)
        self.bind('<ButtonRelease-1>', self.stop_resize)

        self.current_cursor = 'arrow'

    def show_table_labels(self, detections, offset_x=0, offset_y=0):
        """
        牌桌区域显示牌名标签
        """
        self.clear_labels()
        
        window_x = self.winfo_x()
        window_y = self.winfo_y()
        
        chinese_names = {
            'm': '万', 's': '条', 'p': '筒',
            '1z': '东', '2z': '南', '3z': '西', '4z': '北',
            '5z': '白', '6z': '发', '7z': '中'
        }
        
        for det in detections:
            tile_key = det['tile_key']
            bbox = det['bbox']
            
            if tile_key.endswith('z'):
                tile_name = chinese_names[tile_key]
            else:
                num = tile_key[0]
                suit = tile_key[1]
                tile_name = f"{num}{chinese_names[suit]}"
            
            # 标签位置（往下20偏移）
            tile_center_x = bbox[0] + (bbox[2] - bbox[0]) // 2
            tile_center_y = bbox[1] + (bbox[3] - bbox[1]) // 2
            x_screen = window_x + tile_center_x + offset_x
            y_screen = window_y + tile_center_y + offset_y + 20
            
            label_window = tk.Toplevel(self)
            label_window.overrideredirect(True)
            label_window.configure(bg='black')
            label_window.attributes('-alpha', 0.7)
            label_window.attributes('-topmost', True)
            
            # 标签样式（背景色，字体颜色大小）
            name_label = tk.Label(label_window, text=tile_name, 
                                 bg='black', fg='#00BFFF',
                                 font=('Arial', 10, 'bold'))
            name_label.pack()
            
            label_window.update_idletasks()
            label_width = label_window.winfo_width()
            label_height = label_window.winfo_height()
            
            label_window.geometry(f"+{x_screen - label_width//2}+{y_screen - label_height}")
            
            self.label_widgets.append(label_window)
            
    def start_drag(self, event):
        if self.resizing:
            return
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.geometry_x = self.winfo_x()
        self.geometry_y = self.winfo_y()

    def do_drag(self, event):
        if self.drag_start_x is None or self.resizing:
            return
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        new_x = self.geometry_x + dx
        new_y = self.geometry_y + dy
        self.geometry(f"+{new_x}+{new_y}")

    def stop_drag(self, event):
        self.drag_start_x = None
        self.drag_start_y = None

    def on_enter(self, event):
        self.on_motion(event)

    def on_motion(self, event):
        if self.resizing:
            return
        x, y = event.x, event.y
        w = self.winfo_width()
        h = self.winfo_height()
        edge = 8

        on_left = x < edge
        on_right = x > w - edge
        on_top = y < edge
        on_bottom = y > h - edge

        if on_left and on_top:
            cursor = 'top_left_corner'
        elif on_left and on_bottom:
            cursor = 'bottom_left_corner'
        elif on_right and on_top:
            cursor = 'top_right_corner'
        elif on_right and on_bottom:
            cursor = 'bottom_right_corner'
        elif on_left:
            cursor = 'left_side'
        elif on_right:
            cursor = 'right_side'
        elif on_top:
            cursor = 'top_side'
        elif on_bottom:
            cursor = 'bottom_side'
        else:
            cursor = 'arrow'

        if cursor != self.current_cursor:
            try:
                self.configure(cursor=cursor)
                self.current_cursor = cursor
            except:
                self.configure(cursor='arrow')
                self.current_cursor = 'arrow'

    def start_resize(self, event):
        if self.resizing:
            return
        x, y = event.x, event.y
        w = self.winfo_width()
        h = self.winfo_height()
        edge = 8
        
        on_left = x < edge
        on_right = x > w - edge
        on_top = y < edge
        on_bottom = y > h - edge
        
        if not (on_left or on_right or on_top or on_bottom):
            return
            
        self.resizing = True
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_w = self.winfo_width()
        self.resize_start_h = self.winfo_height()
        self.resize_start_abs_x = self.winfo_x()
        self.resize_start_abs_y = self.winfo_y()
        
        if on_left and on_top:
            self.resize_edge = 'nw'
        elif on_left and on_bottom:
            self.resize_edge = 'sw'
        elif on_right and on_top:
            self.resize_edge = 'ne'
        elif on_right and on_bottom:
            self.resize_edge = 'se'
        elif on_left:
            self.resize_edge = 'w'
        elif on_right:
            self.resize_edge = 'e'
        elif on_top:
            self.resize_edge = 'n'
        elif on_bottom:
            self.resize_edge = 's'
            
        self.title_bar.unbind('<Button-1>')
        self.title_bar.unbind('<B1-Motion>')

    def do_resize(self, event):
        if not self.resizing:
            return
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y

        new_w = self.resize_start_w
        new_h = self.resize_start_h
        new_x = self.resize_start_abs_x
        new_y = self.resize_start_abs_y

        edge = self.resize_edge
        if 'w' in edge:
            new_w = max(50, self.resize_start_w - dx)
            new_x = self.resize_start_abs_x + (self.resize_start_w - new_w)
        if 'e' in edge:
            new_w = max(50, self.resize_start_w + dx)
        if 'n' in edge:
            new_h = max(50, self.resize_start_h - dy)
            new_y = self.resize_start_abs_y + (self.resize_start_h - new_h)
        if 's' in edge:
            new_h = max(50, self.resize_start_h + dy)

        self.geometry(f"{new_w}x{new_h}+{new_x}+{new_y}")
        self.update_idletasks()

    def stop_resize(self, event):
        self.resizing = False
        self.resize_edge = None
        self.title_bar.bind('<Button-1>', self.start_drag)
        self.title_bar.bind('<B1-Motion>', self.do_drag)
        self.on_motion(event)

    def get_region_bbox(self):
        """获取窗口内边界（不含标题栏和边框）"""
        x = self.winfo_x()
        y = self.winfo_y()
        width = self.winfo_width()
        height = self.winfo_height()
        return (x + 4, y + 24 + 4, x + width - 4, y + height - 4)

    def clear_labels(self):
        """清除所有显示标签"""
        for label in self.label_widgets:
            label.destroy()
        self.label_widgets.clear()

    def show_risk_labels(self, detections, table_tile_counts, player_wind='东', offset_y=0):
        """
        手牌区域显示牌名和危险度
        table_tile_counts: 牌桌上麻将牌数量（手牌不计入）
        player_wind: 自风默认东风
        offset_y: 标签显示默认不偏移
        """
        self.clear_labels()
        
        window_x = self.winfo_x()
        window_y = self.winfo_y()
        
        hand_tiles = [det['tile_key'] for det in detections]
        
        # 调用危险度计算
        advice_results = get_discard_advice(hand_tiles, table_tile_counts, player_wind, '东')
        
        # 创建映射
        risk_map = {result['tile_key']: result for result in advice_results}
        
        chinese_names = {
            'm': '万', 's': '条', 'p': '筒',
            '1z': '东', '2z': '南', '3z': '西', '4z': '北',
            '5z': '白', '6z': '发', '7z': '中'
        }
        
        for det in detections:
            tile_key = det['tile_key']
            bbox = det['bbox']
            
            if tile_key.endswith('z'):
                tile_name = chinese_names[tile_key]
            else:
                num = tile_key[0]
                suit = tile_key[1]
                tile_name = f"{num}{chinese_names[suit]}"
            
            # 获取危险度
            if tile_key in risk_map:
                risk = risk_map[tile_key]['risk']
                color = risk_map[tile_key]['color']
            else:
                # 调用简化危险度计算
                risk = calculate_tile_risk(tile_key, table_tile_counts, player_wind, '东')
                color = "#FFFFFF"
            

            tile_center_x = bbox[0] + (bbox[2] - bbox[0]) // 2
            x_screen = window_x + tile_center_x
            
            y_screen = window_y - offset_y
            
            label_window = tk.Toplevel(self)
            label_window.overrideredirect(True)
            label_window.configure(bg='black')
            label_window.attributes('-transparentcolor', 'black')
            label_window.attributes('-topmost', True)
            
            label_frame = tk.Frame(label_window, bg='black')
            label_frame.pack()
            
            # 牌名标签样式
            name_label = tk.Label(label_frame, text=tile_name, 
                                 bg='black', fg='white',
                                 font=('Arial', 10, 'bold'))
            name_label.pack()
            
            # 危险度标签样式
            risk_label = tk.Label(label_frame, text=f"{risk}%", 
                                bg='black', fg=color,
                                font=('Arial', 14, 'bold'))
            risk_label.pack()
            
            label_window.update_idletasks()
            label_width = label_window.winfo_width()
            label_height = label_window.winfo_height()
            
            label_window.geometry(f"+{x_screen - label_width//2}+{y_screen - label_height}")
            
            self.label_widgets.append(label_window)

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_file="mahjong_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "hand_region": {
                "width": 300,
                "height": 150,
                "x": 150,
                "y": 450
            },
            "table_region": {
                "width": 400,
                "height": 300,
                "x": 100,
                "y": 100
            },
            "exclude_region": {
                "width": 100,
                "height": 100,
                "x": 200,
                "y": 200
            },
            "player_wind": "东"
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    for key in default_config:
                        if key not in loaded_config:
                            loaded_config[key] = default_config[key]
                    return loaded_config
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return default_config
        else:
            return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到 {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_hand_region(self):
        """获取手牌区域配置"""
        return self.config.get("hand_region", {})
    
    def set_hand_region(self, width, height, x, y):
        """设置手牌区域配置"""
        self.config["hand_region"] = {
            "width": width,
            "height": height,
            "x": x,
            "y": y
        }
        self.save_config()
    
    def get_table_region(self):
        """获取牌桌区域配置"""
        return self.config.get("table_region", {})
    
    def set_table_region(self, width, height, x, y):
        """设置牌桌区域配置"""
        self.config["table_region"] = {
            "width": width,
            "height": height,
            "x": x,
            "y": y
        }
        self.save_config()
    
    def get_exclude_region(self):
        """获取排除区域配置"""
        return self.config.get("exclude_region", {})
    
    def set_exclude_region(self, width, height, x, y):
        """设置排除区域配置"""
        self.config["exclude_region"] = {
            "width": width,
            "height": height,
            "x": x,
            "y": y
        }
        self.save_config()
    
    def get_player_wind(self):
        """获取自风参数"""
        return self.config.get("player_wind", "东")
    
    def set_player_wind(self, wind):
        """设置自风参数"""
        self.config["player_wind"] = wind
        self.save_config()
    
# 主程序窗口
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("雀魂麻将助手 - 东风局")
        self.geometry("340x480+1400+150")
        self.configure(bg='#f0f0f0')
        self.resizable(False, False)
        
        self.attributes('-topmost', True)
        
        # 初始化标签
        self.show_table_labels_var = tk.BooleanVar(value=True)
        self.last_table_matches = []
        self.last_hand_matches = []

        # 初始化配置
        self.config_manager = ConfigManager()
        hand_config = self.config_manager.get_hand_region()
        table_config = self.config_manager.get_table_region()
        exclude_config = self.config_manager.get_exclude_region()
        
        # 初始化区域
        self.hand_rect = GreenBorderResizableRect(
            self, "手牌区域", 
            hand_config.get("width", 300), 
            hand_config.get("height", 150), 
            hand_config.get("x", 150), 
            hand_config.get("y", 450)
        )

        self.table_rect = GreenBorderResizableRect(
            self, "牌桌区域", 
            table_config.get("width", 400), 
            table_config.get("height", 300), 
            table_config.get("x", 100), 
            table_config.get("y", 100)
        )
        
        self.exclude_rect = ExcludeRegion(
            self, 
            width=exclude_config.get("width", 100), 
            height=exclude_config.get("height", 100), 
            x=exclude_config.get("x", 200), 
            y=exclude_config.get("y", 200)
        )

        # 加载模板图片
        self.hand_templates = self.load_templates("templates")
        self.table_templates = self.load_templates("paizhuo")

        # 初始化统计数据

        self.hand_result = {f"{i}{s}": 0 for i in range(1, 10) for s in ['m', 's', 'p']}
        self.hand_result.update({f"{i}z": 0 for i in range(1, 8)})
        
        self.table_result = {}
        for tile_key in [f"{i}{s}" for i in range(1, 10) for s in ['m', 's', 'p']] + [f"{i}z" for i in range(1, 8)]:
            if tile_key not in self.table_result:
                self.table_result[tile_key] = 0

        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_templates(self, template_dir):
        """模板加载"""
        templates = {}
        
        if not os.path.exists(template_dir):
            print(f"警告：{template_dir}目录不存在")
            return templates
        
        for filename in os.listdir(template_dir):
            if filename.endswith('.png'):
                parts = filename.split('_')
                if len(parts) >= 2:
                    tile_key = parts[0]
                    filepath = os.path.join(template_dir, filename)
                    try:
                        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
                        if img is not None:
                            templates.setdefault(tile_key, []).append(img)
                    except Exception as e:
                        print(f"加载{template_dir}失败 {filename}: {e}")
        
        print(f"共加载 {len(templates)} 个{template_dir}模板")
        return templates
    
    def create_widgets(self):
        """界面设置"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)

        # ========== 上方按钮区域 ==========
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(0, 10))
        
        self.recognize_btn = ttk.Button(btn_frame, text="识别", command=self.recognize_all, width=10)
        self.recognize_btn.pack(side='left', padx=2)
        
        self.clear_btn = ttk.Button(btn_frame, text="清空统计", command=self.clear_table, width=10)
        self.clear_btn.pack(side='left', padx=2)
        
        ttk.Label(btn_frame, text="自风", font=('Arial', 10)).pack(side='left', padx=(10, 2))
        self.player_wind_var = tk.StringVar(value=self.config_manager.get_player_wind())
        player_wind_combo = ttk.Combobox(btn_frame, textvariable=self.player_wind_var, 
                                         values=["东", "南", "西", "北"], 
                                         state="readonly", width=5)
        player_wind_combo.pack(side='left', padx=5)
        player_wind_combo.bind('<<ComboboxSelected>>', self.on_player_wind_changed)
        # ========== 上方按钮区域2 ==========
        total_frame = ttk.Frame(main_frame)
        total_frame.pack(fill='x', pady=(0, 10))

        self.toggle_labels_btn = ttk.Button(total_frame, text="隐藏标签", command=self.toggle_table_labels, width=10)
        self.toggle_labels_btn.pack(side='left', padx=2)
        
        self.manual_analyze_btn = ttk.Button(total_frame, text="更新分析", command=self.manual_analyze, width=10)
        self.manual_analyze_btn.pack(side='left', padx=2)
        
        self.total_count_label = ttk.Label(total_frame, text="牌桌统计: 0", font=('Arial', 10, 'bold'))
        self.total_count_label.pack(side='left', padx=10)
        
        # ========== 统计数据区域 ==========
        stats_frame = ttk.LabelFrame(main_frame, text="手动录入吃碰杠", padding="1")
        stats_frame.pack(fill='x', pady=0)
        
        # 万条筒字4列布局
        stats_columns = ttk.Frame(stats_frame)
        stats_columns.pack(fill='x')

        man_frame = ttk.LabelFrame(stats_columns, padding="1")
        man_frame.grid(row=0, column=0, padx=1, pady=1, sticky='nsew')
        
        suo_frame = ttk.LabelFrame(stats_columns,  padding="1")
        suo_frame.grid(row=0, column=1, padx=1, pady=1, sticky='nsew')
        
        tong_frame = ttk.LabelFrame(stats_columns, padding="1")
        tong_frame.grid(row=0, column=2, padx=1, pady=1, sticky='nsew')
        
        zi_frame = ttk.LabelFrame(stats_columns,  padding="1")
        zi_frame.grid(row=0, column=3, padx=1, pady=1, sticky='nsew')

        stats_columns.columnconfigure(0, weight=1)
        stats_columns.columnconfigure(1, weight=1)
        stats_columns.columnconfigure(2, weight=1)
        stats_columns.columnconfigure(3, weight=1)

        # 每列的牌名标签
        self.stats_labels = {}

        def create_stat_rows(parent_frame, tile_keys, display_names=None):
            for idx, tile_key in enumerate(tile_keys):
                frame = ttk.Frame(parent_frame)
                frame.pack(fill='x', pady=1)
                
                display_text = display_names[idx] if display_names else f"{tile_key}:"
                name_label = ttk.Label(frame, text=display_text, width=3)
                name_label.pack(side='left')
                
                count_label = ttk.Label(frame, text=str(self.table_result[tile_key]), 
                                       width=1, font=('Arial', 10, 'bold'))
                count_label.pack(side='left')
                self.stats_labels[tile_key] = count_label

        create_stat_rows(man_frame, [f"{i}m" for i in range(1, 10)])
        create_stat_rows(suo_frame, [f"{i}s" for i in range(1, 10)])
        create_stat_rows(tong_frame, [f"{i}p" for i in range(1, 10)])
        zi_names = ["东", "南", "西", "北", "白", "发", "中"]
        create_stat_rows(zi_frame, [f"{i}z" for i in range(1, 8)], zi_names)

        # ========== 手动输入区==========
        # 四行九列布局
        def create_button_row(parent, tile_keys, display_names=None):
            """通用创建按钮行的方法"""
            frame = ttk.Frame(parent)
            frame.pack(fill='x', pady=3)
            
            for idx, tile_key in enumerate(tile_keys):
                btn_frame = ttk.Frame(frame)
                btn_frame.pack(side='left', padx=2)
                
                text = display_names[idx] if display_names else tile_key
                btn = ttk.Button(btn_frame, text=text, width=3,
                               command=lambda k=tile_key: self.add_table_tile(k))
                btn.pack()

        # 创建按钮行
        create_button_row(stats_frame, [f"{i}m" for i in range(1, 10)])
        create_button_row(stats_frame, [f"{i}s" for i in range(1, 10)])
        create_button_row(stats_frame, [f"{i}p" for i in range(1, 10)])

        zi_names = ["东", "南", "西", "北", "白", "发", "中"]
        create_button_row(stats_frame, [f"{i}z" for i in range(1, 8)], zi_names)
        
        self.update_stats_display()
        
    def toggle_table_labels(self):
        """切换牌桌标签的显示/隐藏"""
        current_state = self.show_table_labels_var.get()
        self.show_table_labels_var.set(not current_state)
        
        if self.show_table_labels_var.get():
            self.toggle_labels_btn.config(text="隐藏标签")
            if hasattr(self, 'last_table_matches') and self.last_table_matches:
                self.table_rect.show_table_labels(self.last_table_matches, offset_x=0, offset_y=0)
            print("牌桌标签已显示")
        else:
            self.toggle_labels_btn.config(text="显示标签")
            self.table_rect.clear_labels()
            print("牌桌标签已隐藏")
            
    def manual_analyze(self):
        """更新分析：手动更新牌局数据后使用"""
        try:
            print("\n========== 更新分析 ==========")
            
            # 检查是否有手牌识别结果
            if not hasattr(self, 'last_hand_matches') or not self.last_hand_matches:
                print("请先识别手牌")
                return
            
            # 获取自风参数
            player_wind = self.player_wind_var.get()
            
            # 刷新手牌危险度
            self.hand_rect.show_risk_labels(self.last_hand_matches, self.table_result, player_wind, offset_y=0)
            
            total_hand = sum(self.hand_result.values())
            total_table = sum(self.table_result.values())
            print(f"当前手牌 {total_hand} 张，牌桌 {total_table} 张")
            print(f"当前自风: {player_wind}, 场风: 东")
            print("========== 更新完成 ==========\n")
            
        except Exception as e:
            print(f"更新失败：{str(e)}")
            import traceback
            traceback.print_exc()
            
    def on_player_wind_changed(self, event):
        """自风选择改变时保存配置"""
        self.config_manager.set_player_wind(self.player_wind_var.get())

    def add_table_tile(self, tile_key):
        """手动录入按钮组"""
        self.table_result[tile_key] += 1
        self.update_stats_display()

    def clear_table(self):
        """清空牌桌数据"""
        for tile_key in self.table_result:
            self.table_result[tile_key] = 0
        self.update_stats_display()
        print("牌桌数据已清空")

    def update_stats_display(self):
        """更新牌桌统计结果显示"""
        total_cards = 0
        table_result = self.table_result
        stats_labels = self.stats_labels
        
        for tile_key in stats_labels:
            count = table_result[tile_key]
            stats_labels[tile_key].config(text=str(count))
            total_cards += count
        
        self.total_count_label.config(text=f"牌桌统计: {total_cards}")

    def preprocess_image(self, img, is_template=False):
        """
        图像预处理，处理宝牌问题
        """
        # 转换为灰度图
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            #gray = img.copy()
            gray = img.copy() if is_template else img
        
        # 使用自适应直方图均衡化增强对比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # 使用高斯滤波降噪
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # 自适应阈值二值化，使图案更清晰
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        return binary

    def detect_tiles_multi_scale(self, img_gray, template, tile_key=None, is_table=False):
        """多尺度模板匹配检测麻将牌"""
        h, w = template.shape
        found = []
        
        # 模板预处理
        template_processed = self.preprocess_image(template, is_template=True)
        
        # 识别阈值设置
        if is_table:
            # 识别最小尺寸
            scales = np.linspace(0.85, 1.4, 12)[::-1]
            min_size = 25
            
            # 初筛，阈值越高越严格
            if tile_key:
                if tile_key == '5z':
                    threshold = 0.48
                elif tile_key == '7z':
                    threshold = 0.6
                elif tile_key.endswith('z'):
                    threshold = 0.48
                elif tile_key == '3p':
                    threshold = 0.6
                elif tile_key == '1m':
                    threshold = 0.52
                elif tile_key == '4s':
                    threshold = 0.52
                elif tile_key == '4p':
                    threshold = 0.6
                else:
                    threshold = 0.50
            else:
                threshold = 0.48
        else:
            # 手牌区域：识别准确无需修改
            scales = np.linspace(0.8, 1.5, 10)[::-1]
            threshold = 0.45
            min_size = 15
        
        for scale in scales:
            resized_w = int(w * scale)
            resized_h = int(h * scale)
            
            # 过滤太小的检测
            if resized_w < min_size or resized_h < min_size:
                continue
                
            if resized_w > img_gray.shape[1] or resized_h > img_gray.shape[0]:
                continue
                
            # 缩放模板
            template_resized = cv2.resize(template_processed, (resized_w, resized_h))
            
            # 模板匹配
            result = cv2.matchTemplate(img_gray, template_resized, cv2.TM_CCOEFF_NORMED)
            
            locations = np.where(result >= threshold)
            
            for pt in zip(*locations[::-1]):
                confidence = result[pt[1], pt[0]]
                
                # 牌桌区域：过滤边缘检测
                if is_table:
                    margin = 5
                    if (pt[0] < margin or pt[1] < margin or 
                        pt[0] + resized_w > img_gray.shape[1] - margin or 
                        pt[1] + resized_h > img_gray.shape[0] - margin):
                        continue
                
                found.append({
                    'bbox': (pt[0], pt[1], pt[0] + resized_w, pt[1] + resized_h),
                    'confidence': confidence,
                    'scale': scale
                })
        
        return found

    def non_max_suppression(self, detections, overlap_threshold=0.3):
        """非极大值抑制，合并重叠的检测框"""
        if not detections:
            return []
        
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        final_detections = []
        while detections:
            best = detections.pop(0)
            final_detections.append(best)
            detections = [d for d in detections if self.iou(best['bbox'], d['bbox']) < overlap_threshold]
        
        return final_detections

    def iou(self, box1, box2):
        """计算两个边界框的IoU"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0

    def is_point_in_exclude_region(self, x, y, exclude_bbox):
        """判断点是否在排除区域内"""
        ex_left, ex_top, ex_right, ex_bottom = exclude_bbox
        return (ex_left <= x <= ex_right and ex_top <= y <= ex_bottom)

    def is_bbox_overlap_with_exclude(self, bbox, exclude_bbox):
        """判断检测框是否与排除区域重叠"""
        left, top, right, bottom = bbox
        ex_left, ex_top, ex_right, ex_bottom = exclude_bbox
        
        # 计算重叠区域
        overlap_left = max(left, ex_left)
        overlap_top = max(top, ex_top)
        overlap_right = min(right, ex_right)
        overlap_bottom = min(bottom, ex_bottom)
        
        if overlap_right <= overlap_left or overlap_bottom <= overlap_top:
            return False
        
        # 计算重叠面积和检测框面积
        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
        bbox_area = (right - left) * (bottom - top)
        
        # 如果重叠面积超过检测框面积的30%，认为需要排除
        return overlap_area / bbox_area > 0.3

    def find_tiles_in_region(self, region_img, templates, is_table=False, exclude_bbox=None):
        """
        在区域图像中查找所有麻将牌的位置和类型
        使用指定的模板集
        is_table: 是否为牌桌区域
        exclude_bbox: 排除区域的边界框
        """
        # 将PIL图像转换为OpenCV格式
        img_rgb = np.array(region_img)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        
        # 预处理截取图像
        img_processed = self.preprocess_image(img_bgr, is_template=False)
        
        all_detections = []
        
        #字牌优先，从小到大顺序处理
        tile_types = sorted(templates.keys(), key=lambda k: (
            0 if k.endswith('z') else 1,
            k
        ))
        
        for tile_key in tile_types:
            template_list = templates[tile_key]
            for template in template_list:
                detections = self.detect_tiles_multi_scale(img_processed, template, tile_key, is_table)
                
                for detection in detections:
                    detection['tile_key'] = tile_key
                    all_detections.append(detection)
        
        if not all_detections:
            return []
        
        all_detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        used = [False] * len(all_detections)
        final_detections = []
        
        for i, det1 in enumerate(all_detections):
            if used[i]:
                continue
            
            cluster = [det1]
            used[i] = True
            
            for j, det2 in enumerate(all_detections[i+1:], i+1):
                if not used[j] and self.iou(det1['bbox'], det2['bbox']) > 0.3:
                    cluster.append(det2)
                    used[j] = True
            
            votes = {}
            for det in cluster:
                votes[det['tile_key']] = votes.get(det['tile_key'], 0) + 1
            
            if votes:
                best_tile = max(votes.items(), key=lambda x: x[1])[0]
                avg_confidence = np.mean([d['confidence'] for d in cluster if d['tile_key'] == best_tile])
                
                # 二筛
                if is_table:
                    if best_tile == '5z':
                        min_confidence = 0.40
                    elif best_tile.endswith('z'):
                        min_confidence = 0.45
                    else:
                        min_confidence = 0.48
                    
                    if avg_confidence < min_confidence:
                        continue
                
                bbox = cluster[0]['bbox']
                
                # 检查是否与排除区域重叠
                if exclude_bbox:
                    if (bbox[2] < exclude_bbox[0] or bbox[0] > exclude_bbox[2] or
                        bbox[3] < exclude_bbox[1] or bbox[1] > exclude_bbox[3]):
                        pass
                    elif self.is_bbox_overlap_with_exclude(bbox, exclude_bbox):
                        continue
                
                final_detections.append({
                    'tile_key': best_tile,
                    'bbox': bbox,
                    'confidence': avg_confidence
                })
        
        # 牌桌区域：适度的非极大值抑制
        if is_table:
            final_detections = self.non_max_suppression(final_detections, overlap_threshold=0.25)
        
        return final_detections

    def recognize_all(self):
        """识别流程（牌桌区域 + 手牌区域）"""
        try:
            print("\n========== 开始识别 ==========")
            
            # 获取排除区域坐标
            exclude_bbox = self.exclude_rect.get_region_bbox()

            # mss 快速截取，解决反光问题
            import mss
            with mss.mss() as sct:
                
                # ===== 牌桌区域截取 =====
                print("\n【牌桌区域】截取...")
                table_bbox = self.table_rect.get_region_bbox()
                
                if table_bbox[2] <= table_bbox[0] or table_bbox[3] <= table_bbox[1]:
                    print("牌桌区域无效")
                    table_img = None
                else:
                    # 排除区域坐标转换
                    rel_exclude_bbox = (
                        exclude_bbox[0] - table_bbox[0],
                        exclude_bbox[1] - table_bbox[1],
                        exclude_bbox[2] - table_bbox[0],
                        exclude_bbox[3] - table_bbox[1]
                    )

                    monitor = {
                        "left": table_bbox[0],
                        "top": table_bbox[1],
                        "width": table_bbox[2] - table_bbox[0],
                        "height": table_bbox[3] - table_bbox[1]
                    }
                    # 截取并转换为 PIL Image
                    sct_img = sct.grab(monitor)
                    table_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    print("牌桌区域截取完成")

                # ===== 手牌区域截取 =====
                print("\n【手牌区域】截取...")
                hand_bbox = self.hand_rect.get_region_bbox()
                
                if hand_bbox[2] <= hand_bbox[0] or hand_bbox[3] <= hand_bbox[1]:
                    print("手牌区域无效")
                    return
                
                monitor = {
                    "left": hand_bbox[0],
                    "top": hand_bbox[1],
                    "width": hand_bbox[2] - hand_bbox[0],
                    "height": hand_bbox[3] - hand_bbox[1]
                }
                sct_img = sct.grab(monitor)
                hand_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                print("手牌区域截取完成")
            
            # ===== 处理牌桌区域识别 =====
            if table_img is not None:
                print("\n【牌桌区域识别】处理中...")
                # 开始匹配
                table_matches = self.find_tiles_in_region(table_img, self.table_templates, is_table=True, exclude_bbox=rel_exclude_bbox)
                
                # 保存识别结果，用于标签显示切换
                self.last_table_matches = table_matches
                
                # 更新牌桌统计
                for tile_key in self.table_result:
                    self.table_result[tile_key] = 0
                
                for match in table_matches:
                    if match['tile_key'] in self.table_result:
                        self.table_result[match['tile_key']] += 1
                        #print(f"牌桌识别到: {match['tile_key']}, 置信度: {match['confidence']:.2f}")
                
                self.update_stats_display()
                
                total_table = sum(self.table_result.values())
                print(f"牌桌识别完成，共识别到 {total_table} 张牌")
                
                if self.show_table_labels_var.get():
                    self.table_rect.show_table_labels(table_matches, offset_x=0, offset_y=0)
            
            # ===== 处理手牌区域识别 =====
            print("\n【手牌区域识别】处理中...")
            hand_matches = self.find_tiles_in_region(hand_img, self.hand_templates, is_table=False)
            
            # 保存识别结果，用于快速更新分析
            self.last_hand_matches = hand_matches
            
            # 更新手牌统计
            for tile_key in self.hand_result:
                self.hand_result[tile_key] = 0
            
            hand_result = self.hand_result
            for match in hand_matches:
                key = match['tile_key']
                if key in hand_result:
                    hand_result[key] += 1
                    #print(f"手牌识别到: {match['tile_key']}, 置信度: {match['confidence']:.2f}")

            # 获取自风参数
            player_wind = self.player_wind_var.get()

            # 显示危险度
            self.hand_rect.show_risk_labels(hand_matches, self.table_result, player_wind, offset_y=0)

            total_hand = sum(self.hand_result.values())
            total_table = sum(self.table_result.values())
            print(f"\n手牌识别完成，共识别到 {total_hand} 张手牌\n"
                  f"牌桌当前有 {total_table} 张牌\n"
                  f"当前自风: {player_wind}, 场风: 东\n"
                  "========== 识别完成 ==========\n")

        except Exception as e:
            print(f"识别失败：{str(e)}")
            import traceback
            traceback.print_exc()
            
    def on_closing(self):
        """窗口关闭时保存所有配置"""
        # 保存手牌区域位置和大小
        hand_width = self.hand_rect.winfo_width()
        hand_height = self.hand_rect.winfo_height()
        hand_x = self.hand_rect.winfo_x()
        hand_y = self.hand_rect.winfo_y()
        self.config_manager.set_hand_region(hand_width, hand_height, hand_x, hand_y)
        
        # 保存牌桌区域位置和大小
        table_width = self.table_rect.winfo_width()
        table_height = self.table_rect.winfo_height()
        table_x = self.table_rect.winfo_x()
        table_y = self.table_rect.winfo_y()
        self.config_manager.set_table_region(table_width, table_height, table_x, table_y)
        
        # 保存排除区域位置和大小
        exclude_width = self.exclude_rect.winfo_width()
        exclude_height = self.exclude_rect.winfo_height()
        exclude_x = self.exclude_rect.winfo_x()
        exclude_y = self.exclude_rect.winfo_y()
        self.config_manager.set_exclude_region(exclude_width, exclude_height, exclude_x, exclude_y)
        
        # 保存自风参数
        self.config_manager.set_player_wind(self.player_wind_var.get())

        self.hand_rect.destroy()
        self.table_rect.destroy()
        self.exclude_rect.destroy()
        self.destroy()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()