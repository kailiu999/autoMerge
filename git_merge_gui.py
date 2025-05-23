import tkinter as tk
from tkinter import scrolledtext
import subprocess
import sys
import os
import threading
import queue
import json

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
        self.current_process = None  # 当前运行的进程
        self.worker_thread = None  # 工作线程
        self.message_queue = queue.Queue()  # 消息队列
        self.is_running = False  # 标记是否正在执行任务
        
        # 启动消息处理
        self.process_queue()
        
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
        
        # 取消按钮
        self.cancel_button = tk.Button(
            self.button_frame, 
            text="取消", 
            command=self.cancel_operation,
            bg="#f56c6c",
            fg="white",
            activebackground="#f78989",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            font=("Helvetica", 14, "bold"),
            cursor="no",  # 初始为禁用状态
            state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 下部终端显示区
        self.bottom_frame = tk.Frame(master, bg="#ffffff", bd=0, highlightthickness=0)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # 终端标题栏
        self.terminal_header = tk.Frame(self.bottom_frame, bg="#2d3748", height=30)
        self.terminal_header.pack(fill=tk.X)
        self.terminal_header.pack_propagate(False)
        
        self.terminal_title = tk.Label(
            self.terminal_header, 
            text="输出终端", 
            bg="#2d3748", 
            fg="#ffffff", 
            font=("Helvetica", 12),
            anchor=tk.W
        )
        self.terminal_title.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 重置按钮在终端标题栏
        self.reset_terminal_button = tk.Button(
            self.terminal_header,
            text="清空",
            command=self.reset_merge,
            bg="#4a5568",
            fg="white",
            activebackground="#718096",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=2,
            font=("Helvetica", 10),
            cursor="hand2"
        )
        self.reset_terminal_button.pack(side=tk.RIGHT, padx=10, pady=5)
        
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
        self.terminal.tag_config("info", foreground="cyan")
    
    def process_queue(self):
        """处理消息队列"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                message_type = message.get("type")
                
                if message_type == "output":
                    self.process_output(message.get("text", ""))
                elif message_type == "status":
                    self.handle_status_update(message.get("data"))
                elif message_type == "finished":
                    self.handle_task_finished(message.get("success", False))
                elif message_type == "error":
                    self.append_output(f"执行出错: {message.get('error', '')}\n", "error")
                    self.handle_task_finished(False)
                    
        except queue.Empty:
            pass
        
        # 定期检查队列
        self.master.after(100, self.process_queue)
    
    def run_merge(self):
        """运行合并操作"""
        if self.is_running:
            return
            
        project_path = self.path_entry.get()
        if not project_path:
            self.append_output("请先输入项目路径！\n", "error")
            return
        
        self.reset_state()
        self.current_project_path = project_path
        self.set_running_state(True)
        
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
        
        # 在新线程中执行任务
        self.worker_thread = threading.Thread(
            target=self.execute_git_task,
            args=(project_path,),
            daemon=True
        )
        self.worker_thread.start()
    
    def continue_merge(self):
        """继续合并操作"""
        if not self.conflict_state or not self.current_project_path or self.is_running:
            self.append_output("没有冲突状态需要继续处理！\n", "error")
            return
        
        self.set_running_state(True)
        
        project_path = self.current_project_path
        step_index = self.conflict_state.get("step", 0)
        branch = self.conflict_state.get("branch", "")
        
        self.append_output(f"继续执行，当前步骤索引: {step_index}, 分支: {branch}\n")
        
        # 在新线程中执行任务
        self.worker_thread = threading.Thread(
            target=self.execute_git_task,
            args=(project_path, step_index, branch),
            daemon=True
        )
        self.worker_thread.start()
    
    def cancel_operation(self):
        """取消当前操作"""
        if not self.is_running:
            return
            
        self.append_output("正在取消操作...\n", "warning")
        
        # 终止进程
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                # 给进程一些时间优雅退出
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 如果进程没有优雅退出，强制杀死
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception as e:
                self.append_output(f"取消进程时出错: {str(e)}\n", "error")
        
        self.set_running_state(False)
        self.append_output("操作已取消\n", "warning")
    
    def execute_git_task(self, project_path, step_index=None, branch=None):
        """在后台线程中执行git任务"""
        try:
            # 构建命令
            if step_index is not None and branch is not None:
                # 继续模式
                cmd = [
                    sys.executable, 
                    "git_merge_auto.py", 
                    project_path,
                    "--continue",
                    str(step_index),
                    branch
                ]
            else:
                # 普通模式
                cmd = [sys.executable, "git_merge_auto.py", project_path]
            
            # 启动进程
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # 行缓冲
            )
            
            # 实时读取输出
            while True:
                if self.current_process.poll() is not None:
                    break
                    
                output = self.current_process.stdout.readline()
                if output:
                    # 检查是否是状态信息
                    if output.startswith("STATUS_JSON:"):
                        try:
                            status_json = output.replace("STATUS_JSON:", "").strip()
                            status_data = json.loads(status_json)
                            self.message_queue.put({"type": "status", "data": status_data})
                        except Exception as e:
                            self.message_queue.put({"type": "output", "text": output})
                    else:
                        self.message_queue.put({"type": "output", "text": output})
            
            # 读取剩余输出
            remaining_stdout, stderr = self.current_process.communicate()
            if remaining_stdout:
                for line in remaining_stdout.splitlines():
                    if line.startswith("STATUS_JSON:"):
                        try:
                            status_json = line.replace("STATUS_JSON:", "").strip()
                            status_data = json.loads(status_json)
                            self.message_queue.put({"type": "status", "data": status_data})
                        except Exception as e:
                            self.message_queue.put({"type": "output", "text": line + "\n"})
                    else:
                        self.message_queue.put({"type": "output", "text": line + "\n"})
            
            if stderr:
                self.message_queue.put({"type": "output", "text": stderr})
            
            # 检查退出码
            return_code = self.current_process.returncode
            success = return_code == 0
            
            self.message_queue.put({"type": "finished", "success": success})
            
        except Exception as e:
            self.message_queue.put({"type": "error", "error": str(e)})
    
    def handle_status_update(self, status_data):
        """处理状态更新"""
        if status_data and status_data.get("status") == "conflict":
            self.conflict_state = status_data
            self.append_output("检测到冲突，请手动解决后点击'继续'按钮...\n", "warning")
            self.continue_button.config(state=tk.NORMAL, cursor="hand2")
            self.set_running_state(False)
    
    def handle_task_finished(self, success):
        """处理任务完成"""
        if success:
            self.append_output("操作完成！\n", "success")
            self.reset_state()
        
        self.set_running_state(False)
    
    def set_running_state(self, running):
        """设置运行状态"""
        self.is_running = running
        
        if running:
            # 禁用运行按钮，启用取消按钮
            self.run_button.config(state=tk.DISABLED, cursor="no", text="运行中...")
            self.cancel_button.config(state=tk.NORMAL, cursor="hand2")
            # 如果不是冲突状态，禁用继续按钮
            if not self.conflict_state:
                self.continue_button.config(state=tk.DISABLED, cursor="no")
        else:
            # 启用运行按钮，禁用取消按钮
            self.run_button.config(state=tk.NORMAL, cursor="hand2", text="运行")
            self.cancel_button.config(state=tk.DISABLED, cursor="no")
    
    def reset_state(self):
        """重置程序状态"""
        self.conflict_state = None
        self.continue_button.config(state=tk.DISABLED, cursor="no")
    
    def reset_merge(self):
        """重置当前操作，清空终端，准备重新开始"""
        # 如果正在运行，先取消
        if self.is_running:
            self.cancel_operation()
        
        self.reset_state()
        self.terminal.config(state=tk.NORMAL)
        self.terminal.delete(1.0, tk.END)
        self.terminal.config(state=tk.DISABLED)
        self.append_output("程序已重置，可以开始新的操作。\n", "success")
    
    def append_output(self, text, tag=None):
        """添加输出到终端"""
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
    
    def process_output(self, text):
        """处理输出文本"""
        # 处理带颜色的输出
        if "[ERROR]" in text:
            self.append_output(text, "error")
        elif "[SUCCESS]" in text:
            self.append_output(text, "success")
        elif "[WARNING]" in text:
            self.append_output(text, "warning")
        elif ">>> 正在执行:" in text:
            self.append_output(text, "info")
        else:
            self.append_output(text)

if __name__ == "__main__":
    root = tk.Tk()
    gui = GitMergeGUI(root)
    root.mainloop()