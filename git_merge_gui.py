import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os

class GitMergeGUI:
    def __init__(self, master):
        self.master = master
        master.title("Git Merge Tool")
        master.geometry("600x500")
        master.configure(bg="#f5f5f7")
        
        # 上部面板
        self.top_frame = tk.Frame(master, height=100, bg="#ffffff", bd=0, highlightthickness=0)
        self.top_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # 快捷标签容器
        self.tag_frame = tk.Frame(self.top_frame, bg="#ffffff")
        self.tag_frame.pack(fill=tk.X, pady=(0, 10))
        self.tag_container = tk.Frame(self.tag_frame, bg="#ffffff")
        self.tag_container.pack(fill=tk.X, expand=True)
        
        # 示例快捷标签
        self.existing_paths = []
        self.add_quick_tag("baotou-management-web", "D:\\project\\baotou-management-web")
        self.add_quick_tag("baotou-lifeline-web", "D:\\project\\baotou-lifeline-web")
        
        # 输入框
        self.path_label = tk.Label(self.top_frame, text="项目路径:", font=("Helvetica", 12), fg="#8e8e93")
        self.path_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.path_entry = tk.Entry(self.top_frame, width=50, font=("Helvetica", 12), 
                                 bd=0, highlightthickness=1, highlightcolor="#007aff", 
                                 highlightbackground="#c7c7cc", relief=tk.FLAT)
        self.path_entry.pack(fill=tk.X, pady=(0, 10))
        # 移除回车事件绑定
        
        # 运行按钮
        self.run_button = tk.Button(
            self.top_frame, 
            text="运行", 
            command=self.run_merge,
            bg="#007aff",
            fg="white",
            activebackground="#0062cc",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            font=("Helvetica", 12, "bold")
        )
        self.run_button.pack(fill=tk.X, pady=(10, 0))
        
        # 下部终端显示区
        self.bottom_frame = tk.Frame(master, bg="#ffffff", bd=0, highlightthickness=0)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.terminal = scrolledtext.ScrolledText(
            self.bottom_frame,
            wrap=tk.WORD,
            bg="black",
            fg="white",
            insertbackground="white"
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)
        
        # 配置颜色标签
        self.terminal.tag_config("error", foreground="red")
        self.terminal.tag_config("success", foreground="green")
        self.terminal.tag_config("warning", foreground="yellow")
    
    def run_merge(self):
        project_path = self.path_entry.get()
        if not project_path:
            self.append_output("请先输入项目路径！\n", "error")
            return
            
        # 在执行合并前检查并添加标签
        path = project_path.strip()
        if path:
            # 统一路径格式为反斜杠并标准化大小写
            path = path.replace('/', '\\').lower()
            # 检查路径是否已存在（忽略大小写）
            if not any(existing_path.lower() == path.lower().replace('/', '\\') for existing_path in self.existing_paths):
                name = os.path.basename(path)
                self.add_quick_tag(name, path)
            
        self.append_output(f"正在执行合并操作，项目路径: {project_path}\n")
        
        try:
            # 调用git_merge_auto.py脚本
            cmd = [sys.executable, "git_merge_auto.py", project_path]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 实时读取输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.process_output(output)
            
            # 检查错误输出
            _, stderr = process.communicate()
            if stderr:
                self.append_output(stderr, "error")
                
        except Exception as e:
            self.append_output(f"执行出错: {str(e)}\n", "error")
    
    def append_output(self, text, tag=None):
        self.terminal.config(state=tk.NORMAL)
        if tag:
            self.terminal.insert(tk.END, text, tag)
        else:
            self.terminal.insert(tk.END, text)
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)
    
    def add_quick_tag(self, name, path):
        """添加快捷标签"""
        # 限制最多10个标签
        if len(self.tag_frame.winfo_children()) >= 10:
            self.tag_frame.winfo_children()[0].destroy()
            
        # 从路径中提取最后一个文件夹名称作为标签文本
        tag_name = os.path.basename(path)
        tag = tk.Button(
            self.tag_frame,
            text=tag_name,
            command=lambda: [self.path_entry.delete(0, tk.END), self.path_entry.insert(0, path)],
            bg="#e0e0e0",
            relief=tk.FLAT,
            padx=5,
            pady=2
        )
        # 使用pack布局放置标签
        tag.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 检查是否需要换行
        self.tag_container.update()
        if self.tag_container.winfo_reqwidth() > self.top_frame.winfo_width() - 30:
            # 创建新的一行容器
            self.tag_container = tk.Frame(self.tag_frame, bg="#ffffff")
            self.tag_container.pack(fill=tk.X, expand=True)
            # 将标签移动到新行
            tag.pack_forget()
            tag.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 记录路径
        if path not in self.existing_paths:
            self.existing_paths.append(path)
            
    def check_and_add_tag(self, event):
        """检查并添加新标签"""
        path = self.path_entry.get().strip()
        if path:
            self.append_output(f"原始输入路径: {path}\n")
            # 统一路径格式为反斜杠并标准化大小写
            path = path.replace('/', '\\').lower()
            self.append_output(f"处理后路径: {path}\n")
            self.append_output(f"现有路径列表: {self.existing_paths}\n")
            # 检查路径是否已存在（忽略大小写）
            if not any(existing_path.lower() == path.lower().replace('/', '\\') for existing_path in self.existing_paths):
                name = os.path.basename(path)
                self.append_output(f"添加新标签: {name} - {path}\n")
                self.add_quick_tag(name, path)
                # 更新existing_paths列表
                self.existing_paths.append(path)
            else:
                self.append_output("路径已存在，不添加新标签\n")
    
    def process_output(self, text):
        # 处理带颜色的输出
        if "[ERROR]" in text:
            self.append_output(text, "error")
        elif "[SUCCESS]" in text:
            self.append_output(text, "success")
        elif "[WARNING]" in text:
            self.append_output(text, "warning")
        else:
            self.append_output(text)

if __name__ == "__main__":
    root = tk.Tk()
    gui = GitMergeGUI(root)
    root.mainloop()