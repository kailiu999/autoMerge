import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os

class GitMergeGUI:
    def __init__(self, master):
        self.master = master
        master.title("Git Merge Tool")
        master.geometry("800x600")
        master.configure(bg="#f0f2f5")
        master.iconbitmap("git_macos_bigsur_icon_190141.ico")
        
        # 当前项目状态
        self.current_project_path = ""
        self.conflict_state = None  # 存储冲突状态信息
        
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
        self.add_quick_tag("neimeng-lifeline-web", "D:\\project\\neimeng-lifeline-web")
        self.add_quick_tag("neimeng-management-web", "D:\\project\\neimeng-management-web")
        
        # 输入框
        self.path_label = tk.Label(self.top_frame, text="项目路径:", font=("Helvetica", 14), fg="#606266", cursor="hand2")
        self.path_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.path_entry = tk.Entry(self.top_frame, width=50, font=("Helvetica", 14), 
                                 bd=0, highlightthickness=1, highlightcolor="#409eff", 
                                 highlightbackground="#dcdfe6", relief=tk.FLAT)
        self.path_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 按钮容器
        self.button_frame = tk.Frame(self.top_frame, bg="#ffffff")
        self.button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 运行按钮
        self.run_button = tk.Button(
            self.button_frame, 
            text="运行", 
            command=self.run_merge,
            bg="#409eff",
            fg="white",
            activebackground="#66b1ff",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            font=("Helvetica", 14, "bold"),
            cursor="hand2"
        )
        self.run_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 继续按钮（初始禁用）
        self.continue_button = tk.Button(
            self.button_frame, 
            text="继续", 
            command=self.continue_merge,
            bg="#67c23a",
            fg="white",
            activebackground="#85ce61",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            font=("Helvetica", 14, "bold"),
            cursor="no",  # 初始为禁用鼠标样式
            state=tk.DISABLED
        )
        self.continue_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 重置按钮
        self.reset_button = tk.Button(
            self.button_frame, 
            text="重置", 
            command=self.reset_merge,
            bg="#f56c6c",
            fg="white",
            activebackground="#f78989",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            font=("Helvetica", 14, "bold"),
            cursor="hand2"
        )
        self.reset_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 下部终端显示区
        self.bottom_frame = tk.Frame(master, bg="#ffffff", bd=0, highlightthickness=0)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.terminal = scrolledtext.ScrolledText(
            self.bottom_frame,
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Consolas", 14)
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)
        
        # 配置颜色标签
        self.terminal.tag_config("error", foreground="red")
        self.terminal.tag_config("success", foreground="green")
        self.terminal.tag_config("warning", foreground="yellow")
    
    def run_merge(self):
        self.reset_state()
        project_path = self.path_entry.get()
        if not project_path:
            self.append_output("请先输入项目路径！\n", "error")
            return
            
        # 记录当前项目路径
        self.current_project_path = project_path
            
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
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_lines.append(output)
                    self.process_output(output)
            
            # 检查错误输出
            return_code = process.poll()
            
            # 如果进程返回了数据结构而不是简单的退出码
            if len(output_lines) > 0 and '"status": "conflict"' in ' '.join(output_lines):
                # 解析冲突状态
                for line in output_lines:
                    if '"status": "conflict"' in line:
                        # 尝试从输出中提取冲突信息
                        import re
                        import json
                        match = re.search(r'({.*})', line)
                        if match:
                            try:
                                conflict_info = json.loads(match.group(1))
                                self.conflict_state = conflict_info
                                self.append_output("检测到冲突，请手动解决后点击'继续'按钮...\n", "warning")
                                self.continue_button.config(state=tk.NORMAL, cursor="hand2")
                                break
                            except:
                                pass
                
            _, stderr = process.communicate()
            if stderr:
                self.append_output(stderr, "error")
                
        except Exception as e:
            self.append_output(f"执行出错: {str(e)}\n", "error")
    
    def continue_merge(self):
        if not self.conflict_state or not self.current_project_path:
            self.append_output("没有冲突状态需要继续处理！\n", "error")
            return
            
        # 切换按钮光标为等待状态
        self.continue_button.config(cursor="watch")
        self.master.update()
        
        project_path = self.current_project_path
        step_index = self.conflict_state.get("step", 0)
        branch = self.conflict_state.get("branch", "")
        
        self.append_output(f"继续执行，当前步骤索引: {step_index}, 分支: {branch}\n")
        
        try:
            # 调用git_merge_auto.py脚本的继续模式
            cmd = [
                sys.executable, 
                "git_merge_auto.py", 
                project_path,
                "--continue",
                str(step_index),
                branch
            ]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 实时读取输出
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_lines.append(output)
                    self.process_output(output)
            
            # 检查是否有新的冲突状态
            for line in output_lines:
                if '"status": "conflict"' in line:
                    import re
                    import json
                    match = re.search(r'({.*})', line)
                    if match:
                        try:
                            conflict_info = json.loads(match.group(1))
                            self.conflict_state = conflict_info
                            self.append_output("仍然存在冲突，请手动解决后再次点击'继续'按钮...\n", "warning")
                            # 恢复继续按钮光标
                            self.continue_button.config(cursor="hand2")
                            return
                        except:
                            pass
            
            # 如果没有新的冲突，重置冲突状态
            self.reset_state()
            self.append_output("操作完成！\n", "success")
                
            # 检查错误输出
            _, stderr = process.communicate()
            if stderr:
                self.append_output(stderr, "error")
                
        except Exception as e:
            self.append_output(f"执行出错: {str(e)}\n", "error")
    
    def reset_state(self):
        """重置程序状态"""
        self.conflict_state = None
        self.continue_button.config(state=tk.DISABLED, cursor="no")
    
    def reset_merge(self):
        """重置当前操作，清空终端，准备重新开始"""
        self.reset_state()
        self.terminal.config(state=tk.NORMAL)
        self.terminal.delete(1.0, tk.END)
        self.terminal.config(state=tk.DISABLED)
        self.append_output("程序已重置，可以开始新的操作。\n", "success")
    
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
            
        # 计算当前行的标签数量
        current_row_tags = len(self.tag_container.winfo_children())
        if current_row_tags >= 3:
            # 创建新的一行容器
            self.tag_container = tk.Frame(self.tag_frame, bg="#ffffff")
            self.tag_container.pack(fill=tk.X, expand=True)
            
        # 从路径中提取最后一个文件夹名称作为标签文本
        tag_name = os.path.basename(path)
        tag = tk.Button(
            self.tag_container,
            text=tag_name,
            command=lambda: [self.path_entry.delete(0, tk.END), self.path_entry.insert(0, path)],
            bg="#ecf5ff",
            fg="#409eff",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            font=("Helvetica", 14),
            cursor="hand2"
        )
        # 使用pack布局放置标签
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