import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import re

class SimpleTemplateTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("麻将牌模板制作")
        self.root.geometry("600x500")
        self.root.attributes('-topmost', True)
        
        # 变量
        self.screenshot = None
        self.photo = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.selection = None
        
        # 创建模板目录
        self.template_dir = "paizhuo"
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 标题
        title = tk.Label(self.root, text="麻将牌模板制作工具", font=("Arial", 14, "bold"))
        title.pack(pady=5)
        
        # 说明
        info = tk.Label(self.root, text="1. 点击【开始框选】 → 2. 在屏幕上框选麻将牌 → 3. 选择牌信息 → 4. 保存",
                       fg="blue")
        info.pack(pady=5)
        
        # 按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        self.select_btn = ttk.Button(btn_frame, text="开始框选", command=self.start_selection, width=12)
        self.select_btn.pack(side="left", padx=5)
        
        self.save_btn = ttk.Button(btn_frame, text="保存模板", command=self.save_template, width=12, state="disabled")
        self.save_btn.pack(side="left", padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="清除", command=self.clear_selection, width=12)
        self.clear_btn.pack(side="left", padx=5)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(self.root, text="预览")
        preview_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # 预览标签
        self.preview_label = tk.Label(preview_frame, bg='lightgray', text="等待截图...", 
                                      font=("Arial", 12), fg="gray")
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 牌信息区域
        info_frame = ttk.LabelFrame(self.root, text="牌信息")
        info_frame.pack(pady=10, padx=10, fill="x")
        
        # 花色选择
        suit_frame = ttk.Frame(info_frame)
        suit_frame.pack(pady=5)
        
        ttk.Label(suit_frame, text="花色：", font=("Arial", 11)).pack(side="left", padx=5)
        
        self.suit_var = tk.StringVar(value="m")
        ttk.Radiobutton(suit_frame, text="万", variable=self.suit_var, value="m", 
                       command=self.update_preview_name).pack(side="left", padx=8)
        ttk.Radiobutton(suit_frame, text="筒", variable=self.suit_var, value="p",
                       command=self.update_preview_name).pack(side="left", padx=8)
        ttk.Radiobutton(suit_frame, text="条", variable=self.suit_var, value="s",
                       command=self.update_preview_name).pack(side="left", padx=8)
        ttk.Radiobutton(suit_frame, text="字", variable=self.suit_var, value="z",
                       command=self.update_preview_name).pack(side="left", padx=8)
        
        # 数字选择
        num_frame = ttk.Frame(info_frame)
        num_frame.pack(pady=5)
        
        ttk.Label(num_frame, text="数字：", font=("Arial", 11)).pack(side="left", padx=5)
        
        # 数字按钮
        self.num_var = tk.StringVar(value="1")
        num_buttons_frame = ttk.Frame(num_frame)
        num_buttons_frame.pack(side="left", padx=5)
        
        for i in range(1, 10):
            btn = ttk.Button(num_buttons_frame, text=str(i), width=3,
                           command=lambda x=i: self.num_var.set(str(x)))
            btn.pack(side="left", padx=1)
        
        # 字牌提示
        self.tip_label = tk.Label(info_frame, 
                                 text="字牌：1东 2南 3西 4北 5白 6发 7中",
                                 fg="gray", font=("Arial", 9))
        self.tip_label.pack(pady=2)
        
        # 当前选择显示
        self.name_label = tk.Label(info_frame, text="当前选择：一万", 
                                   font=("Arial", 12, "bold"), fg="green")
        self.name_label.pack(pady=5)
        
        # 选区信息
        self.selection_label = tk.Label(info_frame, text="选区：未选择",
                                       fg="blue")
        self.selection_label.pack(pady=2)
        
        # 文件名显示
        self.filename_label = tk.Label(info_frame, text="文件名：未保存",
                                      fg="purple", font=("Arial", 10, "bold"))
        self.filename_label.pack(pady=2)
        
        # 状态栏
        self.status_label = tk.Label(self.root, text="就绪", relief="sunken", anchor="w")
        self.status_label.pack(side="bottom", fill="x")
        
    def get_next_number(self, base_name):
        """获取下一个编号"""
        # 查找所有匹配的文件
        pattern = f"^{base_name}_(\\d+)\\.png$"
        max_num = 0
        
        if os.path.exists(self.template_dir):
            for filename in os.listdir(self.template_dir):
                match = re.match(pattern, filename)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)
        
        return max_num + 1
        
    def start_selection(self):
        """开始框选"""
        self.select_btn.config(state="disabled")
        self.status_label.config(text="请在屏幕上框选麻将牌...")
        
        # 隐藏主窗口
        self.root.attributes('-alpha', 0)
        self.root.update()
        
        # 创建全屏选择窗口
        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.configure(bg='black')
        
        # 绑定鼠标事件
        self.selection_window.bind("<ButtonPress-1>", self.on_selection_start)
        self.selection_window.bind("<B1-Motion>", self.on_selection_drag)
        self.selection_window.bind("<ButtonRelease-1>", self.on_selection_end)
        self.selection_window.bind("<Escape>", self.cancel_selection)
        
        # 创建画布
        self.selection_canvas = tk.Canvas(self.selection_window, highlightthickness=0)
        self.selection_canvas.pack(fill="both", expand=True)
        
    def on_selection_start(self, event):
        """开始选择"""
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.rect_id = None
        
    def on_selection_drag(self, event):
        """拖动选择"""
        if self.start_x and self.start_y:
            # 删除旧的矩形
            if self.rect_id:
                self.selection_canvas.delete(self.rect_id)
            
            # 绘制新矩形
            self.rect_id = self.selection_canvas.create_rectangle(
                self.start_x, self.start_y, event.x_root, event.y_root,
                outline='red', width=3
            )
            
    def on_selection_end(self, event):
        """结束选择"""
        if self.start_x and self.start_y:
            x1 = min(self.start_x, event.x_root)
            y1 = min(self.start_y, event.y_root)
            x2 = max(self.start_x, event.x_root)
            y2 = max(self.start_y, event.y_root)
            
            # 保存选区
            self.selection = (x1, y1, x2-x1, y2-y1)
            
            # 关闭选择窗口
            self.selection_window.destroy()
            
            # 截图
            self.take_screenshot()
            
    def cancel_selection(self, event):
        """取消选择"""
        self.selection_window.destroy()
        self.select_btn.config(state="normal")
        self.root.attributes('-alpha', 1)
        self.status_label.config(text="已取消选择")
        
    def take_screenshot(self):
        """截取选中的区域"""
        try:
            self.status_label.config(text="正在截图...")
            
            # 截取全屏
            full_screenshot = pyautogui.screenshot()
            
            # 裁剪选中的区域
            x, y, w, h = self.selection
            self.screenshot = full_screenshot.crop((x, y, x+w, y+h))
            
            # 转换为OpenCV格式用于保存
            self.screenshot_cv = cv2.cvtColor(np.array(self.screenshot), cv2.COLOR_RGB2BGR)
            
            # 显示预览
            self.show_preview()
            
            # 显示主窗口
            self.root.attributes('-alpha', 1)
            
            # 启用保存按钮
            self.save_btn.config(state="normal")
            
            # 更新选区信息
            self.selection_label.config(text=f"选区：{w} x {h} 像素")
            
            # 更新文件名预览
            self.update_preview_name()
            
            self.status_label.config(text="截图完成，确认后保存")
            
        except Exception as e:
            self.root.attributes('-alpha', 1)
            messagebox.showerror("错误", f"截图失败：{str(e)}")
            self.select_btn.config(state="normal")
            
    def show_preview(self):
        """显示预览"""
        if self.screenshot:
            # 调整预览大小
            preview_img = self.screenshot.copy()
            preview_img.thumbnail((550, 300))
            
            # 转换为PhotoImage
            self.preview_photo = ImageTk.PhotoImage(preview_img)
            
            # 更新预览标签
            self.preview_label.config(image=self.preview_photo, text="", bg='white')
            
    def update_preview_name(self):
        """更新预览名称和文件名"""
        suit = self.suit_var.get()
        num = self.num_var.get()
        
        suit_names = {'m': '万', 'p': '筒', 's': '条', 'z': '字'}
        suit_name = suit_names.get(suit, '')
        
        if suit == 'z':
            num_int = int(num)
            z_names = ['东', '南', '西', '北', '白', '发', '中']
            if 1 <= num_int <= 7:
                name = f"{z_names[num_int-1]}{suit_name}"
            else:
                name = f"{num}{suit_name}"
        else:
            name = f"{num}{suit_name}"
            
        self.name_label.config(text=f"当前选择：{name}")
        
        # 更新文件名（显示下一个可用的编号）
        if self.selection:
            base_name = f"{num}{suit}"
            next_num = self.get_next_number(base_name)
            filename = f"{base_name}_{next_num:03d}.png"
            self.filename_label.config(text=f"将保存为：{filename}")
            
    def save_template(self):
        """保存模板"""
        if not self.selection:
            messagebox.showwarning("警告", "请先框选区域")
            return
            
        suit = self.suit_var.get()
        num = self.num_var.get()
        
        # 验证
        if not num.isdigit():
            messagebox.showwarning("警告", "请输入正确的数字")
            return
            
        num_int = int(num)
        if suit == 'z' and (num_int < 1 or num_int > 7):
            messagebox.showwarning("警告", "字牌数字必须在1-7之间")
            return
            
        # 生成带编号的文件名
        base_name = f"{num}{suit}"
        next_num = self.get_next_number(base_name)
        filename = f"{base_name}_{next_num:03d}.png"
        filepath = os.path.join(self.template_dir, filename)
        
        # 保存图片
        cv2.imwrite(filepath, self.screenshot_cv)
        
        # 成功提示
        suit_names = {'m': '万', 'p': '筒', 's': '条', 'z': '字'}
        suit_name = suit_names.get(suit, '')
        
        if suit == 'z':
            z_names = ['东', '南', '西', '北', '白', '发', '中']
            tile_name = f"{z_names[num_int-1]}{suit_name}"
        else:
            tile_name = f"{num}{suit_name}"
            
        messagebox.showinfo("成功", f"模板已保存：{filename}\n牌：{tile_name}\n编号：第{next_num}张")
        
        # 更新文件名预览（显示下一个编号）
        self.update_preview_name()
        
        self.status_label.config(text=f"已保存：{filename}")
        
    def clear_selection(self):
        """清除所有"""
        self.selection = None
        self.screenshot = None
        self.preview_label.config(image='', text="等待截图...", bg='lightgray')
        self.selection_label.config(text="选区：未选择")
        self.filename_label.config(text="文件名：未保存")
        self.save_btn.config(state="disabled")
        self.select_btn.config(state="normal")
        self.status_label.config(text="已清除")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleTemplateTool()
    app.run()