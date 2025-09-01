import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import subprocess
import sys
import os
import threading
import queue
import json
import importlib.util
import io
from contextlib import redirect_stdout, redirect_stderr

class GitMergeGUI:
    def __init__(self, master):
        self.master = master
        master.title("Git Merge Tool")
        master.geometry("800x600")
        master.configure(bg="#f0f2f5")
        
        # 获取图标路径
        self.icon_path = self.get_icon_path()
        
        # 初始设置窗口属性和图标
        master.resizable(True, True)  # 允许调整大小
        
        # 设置窗口图标 - 确保任务栏正确显示
        self.set_window_icon()
        
        # 设置窗口属性确保在任务栏显示
        if os.name == 'nt':
            try:
                master.wm_attributes('-toolwindow', False)
            except Exception as e:
                print(f"设置窗口属性失败: {e}")
        
        # 配置文件路径
        self.config_file = "quick_tags_config.json"
        
        # 当前项目状态
        self.current_project_path = ""
        self.conflict_state = None  # 存储冲突状态信息
        self.current_process = None  # 当前运行的进程
        self.worker_thread = None  # 工作线程
        self.message_queue = queue.Queue()  # 消息队列
        self.is_running = False  # 标记是否正在执行任务
        
        # 启动消息处理
        self.process_queue()
        
        # 绑定窗口关闭事件（点击X按钮时直接关闭程序）
        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # 上部面板
        self.top_frame = tk.Frame(master, height=100, bg="#ffffff", bd=0, highlightthickness=0)
        self.top_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # 快捷标签容器
        self.tag_frame = tk.Frame(self.top_frame, bg="#ffffff")
        self.tag_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.tag_container = tk.Frame(self.tag_frame, bg="#ffffff")
        self.tag_container.pack(fill=tk.X, expand=True)
        
        # 初始化快捷标签
        self.existing_paths = []
        self.load_quick_tags()  # 加载保存的标签
        
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
        
        # 设置按钮
        self.settings_btn = tk.Button(
            self.button_frame,
            text="⚙ 设置",
            command=self.open_settings,
            bg="#67c23a",
            fg="white",
            activebackground="#85ce61",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            font=("Helvetica", 14, "bold"),
            cursor="hand2"
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
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
        self.run_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
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
    

    
    def get_icon_path(self):
        """获取图标文件路径"""
        try:
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller打包后的临时目录
                icon_path = os.path.join(getattr(sys, '_MEIPASS'), "git_macos_bigsur_icon_190141.ico")
            else:
                # 开发环境
                icon_path = os.path.abspath("git_macos_bigsur_icon_190141.ico")
            
            if os.path.exists(icon_path):
                return icon_path
            else:
                return None
        except Exception as e:
            print(f"获取图标路径失败: {e}")
            return None
    
    def set_window_icon(self):
        """设置窗口图标 - 优化任务栏显示"""
        if self.icon_path and os.path.exists(self.icon_path):
            try:
                # 确保窗口已经创建
                self.master.update_idletasks()
                
                # 设置窗口图标
                self.master.iconbitmap(self.icon_path)
                
                # Windows 特殊处理：确保任务栏图标正确显示
                if os.name == 'nt':
                    # 使用多种方法设置图标以提高兼容性
                    try:
                        # 方法1: 使用wm_iconbitmap
                        self.master.wm_iconbitmap(self.icon_path)
                    except Exception:
                        pass
                    
                    # 方法2: 延迟再次设置以确保任务栏更新
                    self.master.after(50, lambda: self.master.iconbitmap(self.icon_path))
                    
                    # 方法3: 设置窗口属性确保图标正确显示在任务栏
                    try:
                        self.master.wm_attributes('-toolwindow', False)
                    except Exception:
                        pass
                    
            except Exception as e:
                print(f"设置窗口图标失败: {e}")
                # 备用方案
                try:
                    # 尝试使用wm_iconbitmap
                    self.master.wm_iconbitmap(self.icon_path)
                except Exception as e2:
                    print(f"wm_iconbitmap也失败: {e2}")
        else:
            pass  # 图标文件不存在，跳过图标设置


    def on_window_close(self):
        """处理窗口关闭事件（点击系统关闭按钮）"""
        # 直接关闭程序
        self.close_window()
    

    
    def close_window(self):
        """关闭窗口"""
        try:
            # 关闭窗口
            self.master.quit()
            self.master.destroy()
            
        except Exception as e:
            print(f"关闭窗口失败: {e}")
            # 强制退出
            try:
                os._exit(0)
            except:
                pass
    

    
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
        if path and path not in self.existing_paths:
            # 标准化路径格式
            path = path.replace('/', '\\').lower()
            # 检查路径是否已存在（忽略大小写）
            if not any(existing_path.lower() == path for existing_path in self.existing_paths):
                name = os.path.basename(path)
                self.add_quick_tag(name, project_path)  # 使用原始路径
        
        self.append_output(f"正在执行合并操作，项目路径: {project_path}\n")
        
        # 在新线程中执行任务
        self.worker_thread = threading.Thread(
            target=self.execute_git_task,
            args=(project_path,),
            daemon=True
        )
        self.worker_thread.start()
    

    
    def execute_git_task(self, project_path):
        """在后台线程中执行git任务"""
        try:
            # 在打包环境中直接导入并执行git_merge_auto模块，避免启动新进程
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller打包后，直接导入模块
                import importlib.util
                script_path = os.path.join(getattr(sys, '_MEIPASS'), "git_merge_auto.py")
                spec = importlib.util.spec_from_file_location("git_merge_auto", script_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"无法加载模块: {script_path}")
                git_merge_auto = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(git_merge_auto)
                
                # 重定向输出到消息队列
                import io
                import contextlib
                from contextlib import redirect_stdout, redirect_stderr
                
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()
                
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # 模拟命令行参数
                    original_argv = sys.argv.copy()
                    sys.argv = ['git_merge_auto.py', project_path]
                    
                    try:
                        result = git_merge_auto.execute_git_workflow(project_path)
                        success = bool(result) and result is not False
                    except Exception as e:
                        self.message_queue.put({"type": "error", "error": str(e)})
                        return
                    finally:
                        sys.argv = original_argv
                
                # 发送捕获的输出
                stdout_content = stdout_capture.getvalue()
                stderr_content = stderr_capture.getvalue()
                
                if stdout_content:
                    for line in stdout_content.splitlines():
                        if line.startswith("STATUS_JSON:"):
                            try:
                                status_json = line.replace("STATUS_JSON:", "").strip()
                                status_data = json.loads(status_json)
                                self.message_queue.put({"type": "status", "data": status_data})
                            except Exception as e:
                                self.message_queue.put({"type": "output", "text": line + "\n"})
                        else:
                            self.message_queue.put({"type": "output", "text": line + "\n"})
                
                if stderr_content:
                    self.message_queue.put({"type": "output", "text": stderr_content})
                
                self.message_queue.put({"type": "finished", "success": success})
                
            else:
                # 开发环境，使用子进程
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
                        
                    if self.current_process.stdout is not None:
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
            self.append_output("检测到冲突，请手动解决冲突后重新运行...\n", "warning")
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
            # 禁用运行按钮
            self.run_button.config(state=tk.DISABLED, cursor="no", text="运行中...")
        else:
            # 启用运行按钮
            self.run_button.config(state=tk.NORMAL, cursor="hand2", text="运行")
    
    def reset_state(self):
        """重置程序状态"""
        self.conflict_state = None
    
    def reset_merge(self):
        """重置当前操作，清空终端，准备重新开始"""
        # 如果正在运行，终止进程
        if self.is_running and self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                try:
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception as e:
                self.append_output(f"终止进程时出错: {str(e)}\n", "error")
        
        self.set_running_state(False)
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
    
    def load_quick_tags(self):
        """加载保存的快捷标签"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    tags = config.get('quick_tags', [])
                    for tag in tags:
                        if 'name' in tag and 'path' in tag:
                            self.add_quick_tag(tag['name'], tag['path'], save_config=False)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 如果加载失败，添加一个默认标签
            self.add_quick_tag("urban-lifeline-web", "C:\\Users\\Mrliu\\Desktop\\project\\Urban-lifeline")
    
    def save_quick_tags(self):
        """保存快捷标签到配置文件"""
        try:
            tags = []
            for path in self.existing_paths:
                name = os.path.basename(path)
                tags.append({'name': name, 'path': path})
            
            config = {'quick_tags': tags}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def add_quick_tag(self, name, path, save_config=True):
        """添加快捷标签"""
        # 检查是否已经存在
        if path in self.existing_paths:
            return
        
        # 标准化路径格式
        path = path.replace('/', '\\').strip()
        
        # 限制最多10个标签
        if len(self.existing_paths) >= 10:
            return
        
        # 记录路径
        if path not in self.existing_paths:
            self.existing_paths.append(path)
        
        # 创建标签组件
        self.create_tag_widget(name, path)
        
        # 保存配置
        if save_config:
            self.save_quick_tags()
    
    def create_tag_widget(self, name, path):
        """创建标签组件"""
        # 计算当前行的标签数量
        current_row_tags = len([w for w in self.tag_container.winfo_children() if isinstance(w, tk.Frame)])
        if current_row_tags >= 3:
            # 创建新的一行容器
            self.tag_container = tk.Frame(self.tag_frame, bg="#ffffff")
            self.tag_container.pack(fill=tk.X, expand=True)
        
        # 创建标签容器
        tag_frame = tk.Frame(self.tag_container, bg="#ecf5ff", relief=tk.FLAT, bd=1)
        tag_frame.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 标签按钮
        tag_button = tk.Button(
            tag_frame,
            text=name,
            command=lambda: [self.path_entry.delete(0, tk.END), self.path_entry.insert(0, path)],
            bg="#ecf5ff",
            fg="#409eff",
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=4,
            font=("Helvetica", 10),
            cursor="hand2"
        )
        tag_button.pack()
    
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
    
    def open_settings(self):
        """打开设置对话框"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("设置")
        settings_window.geometry("700x650")
        settings_window.configure(bg="#ffffff")
        settings_window.resizable(True, True)
        settings_window.minsize(650, 600)
        
        # 设置窗口为模态
        settings_window.transient(self.master)
        settings_window.grab_set()
        
        # 居中显示
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (650 // 2)
        settings_window.geometry(f"700x650+{x}+{y}")
        
        # 创建选项卡
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 快捷标签设置选项卡
        tag_frame = ttk.Frame(notebook)
        notebook.add(tag_frame, text="快捷标签设置")
        
        self.create_tag_settings_tab(tag_frame)
    
    def create_tag_settings_tab(self, parent):
        """创建快捷标签设置选项卡内容"""
        # 主容器
        main_frame = tk.Frame(parent, bg="#ffffff")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 上半部分：已有标签列表
        list_frame = tk.LabelFrame(main_frame, text="已有标签列表", bg="#ffffff", fg="#303133", font=("Helvetica", 12, "bold"))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 表格头
        header_frame = tk.Frame(list_frame, bg="#f5f7fa")
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(header_frame, text="名称", bg="#f5f7fa", fg="#606266", font=("Helvetica", 10, "bold"), width=15).pack(side=tk.LEFT)
        tk.Label(header_frame, text="路径", bg="#f5f7fa", fg="#606266", font=("Helvetica", 10, "bold"), width=35).pack(side=tk.LEFT)
        tk.Label(header_frame, text="操作", bg="#f5f7fa", fg="#606266", font=("Helvetica", 10, "bold"), width=10).pack(side=tk.LEFT)
        
        # 滚动列表容器
        list_container = tk.Frame(list_frame, bg="#ffffff")
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # 创建滚动条和列表
        canvas = tk.Canvas(list_container, bg="#ffffff", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 用于存储当前编辑的标签索引
        self.editing_tag_index = None
        
        # 显示已有标签
        self.refresh_tag_list(scrollable_frame)
        
        # 下半部分：新增/编辑标签表单
        form_frame = tk.LabelFrame(main_frame, text="标签表单", bg="#ffffff", fg="#303133", font=("Helvetica", 12, "bold"))
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 表单内容
        form_content = tk.Frame(form_frame, bg="#ffffff")
        form_content.pack(fill=tk.X, padx=15, pady=15)
        
        # 名称输入
        name_frame = tk.Frame(form_content, bg="#ffffff")
        name_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Label(name_frame, text="名称:", bg="#ffffff", fg="#606266", width=8, anchor="w", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self.tag_name_entry = tk.Entry(name_frame, font=("Helvetica", 11), bd=1, relief=tk.SOLID)
        self.tag_name_entry.pack(fill=tk.X, expand=True, padx=(10, 0))
        
        # 路径输入
        path_frame = tk.Frame(form_content, bg="#ffffff")
        path_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(path_frame, text="路径:", bg="#ffffff", fg="#606266", width=8, anchor="w", font=("Helvetica", 10)).pack(side=tk.LEFT)
        self.tag_path_entry = tk.Entry(path_frame, font=("Helvetica", 11), bd=1, relief=tk.SOLID)
        self.tag_path_entry.pack(fill=tk.X, expand=True, padx=(10, 0))
        
        # 按钮组
        button_frame = tk.Frame(form_content, bg="#ffffff")
        button_frame.pack(fill=tk.X)
        
        # 提交按钮
        self.submit_button = tk.Button(
            button_frame,
            text="提交",
            command=lambda: self.submit_tag_form(scrollable_frame),
            bg="#409eff",
            fg="white",
            activebackground="#66b1ff",
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=10,
            font=("Helvetica", 11),
            cursor="hand2"
        )
        self.submit_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # 取消按钮
        cancel_button = tk.Button(
            button_frame,
            text="取消",
            command=self.clear_tag_form,
            bg="#909399",
            fg="white",
            activebackground="#a6a9ad",
            relief=tk.FLAT,
            bd=0,
            padx=25,
            pady=10,
            font=("Helvetica", 11),
            cursor="hand2"
        )
        cancel_button.pack(side=tk.LEFT)
        
        # 存储引用以便在其他方法中使用
        self.tag_list_frame = scrollable_frame
    
    def refresh_tag_list(self, list_frame):
        """刷新标签列表显示"""
        # 清空现有内容
        for widget in list_frame.winfo_children():
            widget.destroy()
        
        # 显示每个标签
        for i, path in enumerate(self.existing_paths):
            name = os.path.basename(path)
            
            # 创建行容器
            row_frame = tk.Frame(list_frame, bg="#ffffff" if i % 2 == 0 else "#fafafa")
            row_frame.pack(fill=tk.X, pady=1)
            
            # 名称
            name_label = tk.Label(row_frame, text=name, bg=row_frame['bg'], fg="#303133", font=("Helvetica", 10), width=15, anchor="w")
            name_label.pack(side=tk.LEFT, padx=5, pady=5)
            
            # 路径（截取显示）
            display_path = path if len(path) <= 40 else "..." + path[-37:]
            path_label = tk.Label(row_frame, text=display_path, bg=row_frame['bg'], fg="#606266", font=("Helvetica", 9), width=35, anchor="w")
            path_label.pack(side=tk.LEFT, padx=5, pady=5)
            
            # 操作按钮
            action_frame = tk.Frame(row_frame, bg=row_frame['bg'])
            action_frame.pack(side=tk.LEFT, padx=5)
            
            # 编辑按钮
            edit_button = tk.Button(
                action_frame,
                text="编辑",
                command=lambda idx=i: self.edit_tag(idx),
                bg="#67c23a",
                fg="white",
                activebackground="#85ce61",
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=2,
                font=("Helvetica", 8),
                cursor="hand2"
            )
            edit_button.pack(side=tk.LEFT, padx=(0, 5))
            
            # 删除按钮
            delete_button = tk.Button(
                action_frame,
                text="删除",
                command=lambda idx=i: self.delete_tag_from_settings(idx),
                bg="#f56c6c",
                fg="white",
                activebackground="#f78989",
                relief=tk.FLAT,
                bd=0,
                padx=8,
                pady=2,
                font=("Helvetica", 8),
                cursor="hand2"
            )
            delete_button.pack(side=tk.LEFT)
    
    def edit_tag(self, index):
        """编辑指定索引的标签"""
        if 0 <= index < len(self.existing_paths):
            path = self.existing_paths[index]
            name = os.path.basename(path)
            
            # 填充表单
            self.tag_name_entry.delete(0, tk.END)
            self.tag_name_entry.insert(0, name)
            self.tag_path_entry.delete(0, tk.END)
            self.tag_path_entry.insert(0, path)
            
            # 记录编辑的标签索引
            self.editing_tag_index = index
            
            # 更改按钮文本
            self.submit_button.config(text="更新")
    
    def delete_tag_from_settings(self, index):
        """从设置中删除指定索引的标签"""
        if 0 <= index < len(self.existing_paths):
            path = self.existing_paths[index]
            result = messagebox.askyesno("确认", f"确定要删除标签 '{os.path.basename(path)}' 吗？")
            if result:
                # 从列表中删除
                self.existing_paths.pop(index)
                
                # 保存配置
                self.save_quick_tags()
                
                # 刷新界面显示
                self.refresh_tags_display()
                
                # 刷新设置中的列表
                self.refresh_tag_list(self.tag_list_frame)
                
                # 清空表单
                self.clear_tag_form()
                
                messagebox.showinfo("成功", "标签已删除！")
    
    def submit_tag_form(self, list_frame):
        """提交标签表单"""
        name = self.tag_name_entry.get().strip()
        path = self.tag_path_entry.get().strip()
        
        if not name:
            messagebox.showerror("错误", "请输入标签名称！")
            return
        
        if not path:
            messagebox.showerror("错误", "请输入项目路径！")
            return
        
        # 验证路径是否存在
        if not os.path.exists(path):
            messagebox.showerror("错误", "路径不存在，请检查后重试！")
            return
        
        # 标准化路径
        path = path.replace('/', '\\').strip()
        
        if self.editing_tag_index is not None:
            # 编辑模式
            old_path = self.existing_paths[self.editing_tag_index]
            
            # 检查是否与其他标签重复
            for i, existing_path in enumerate(self.existing_paths):
                if i != self.editing_tag_index and existing_path.lower() == path.lower():
                    messagebox.showerror("错误", "该路径的标签已存在！")
                    return
            
            # 更新标签
            self.existing_paths[self.editing_tag_index] = path
            
            # 保存配置
            self.save_quick_tags()
            
            # 刷新界面显示
            self.refresh_tags_display()
            
            messagebox.showinfo("成功", f"标签 '{name}' 更新成功！")
        else:
            # 新增模式
            # 检查是否已存在
            if any(existing_path.lower() == path.lower() for existing_path in self.existing_paths):
                messagebox.showerror("错误", "该路径的标签已存在！")
                return
            
            # 限制数量
            if len(self.existing_paths) >= 10:
                messagebox.showwarning("警告", "最多只能添加10个快捷标签，请先删除一些后再添加！")
                return
            
            # 添加新标签
            self.add_quick_tag(name, path)
            
            messagebox.showinfo("成功", f"快捷标签 '{name}' 添加成功！")
        
        # 刷新列表显示
        self.refresh_tag_list(list_frame)
        
        # 清空表单
        self.clear_tag_form()
    
    def clear_tag_form(self):
        """清空标签表单"""
        self.tag_name_entry.delete(0, tk.END)
        self.tag_path_entry.delete(0, tk.END)
        self.editing_tag_index = None
        self.submit_button.config(text="提交")
    
    def refresh_tags_display(self):
        """刷新主界面中的标签显示"""
        # 清空现有标签
        for widget in self.tag_container.winfo_children():
            widget.destroy()
        
        # 重新添加所有标签
        for path in self.existing_paths:
            name = os.path.basename(path)
            self.create_tag_widget(name, path)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        gui = GitMergeGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")