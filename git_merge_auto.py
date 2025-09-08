import os
import sys
import subprocess
import json
from datetime import datetime

# 颜色常量
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"

def get_subprocess_flags():
    """获取subprocess的创建标志，在打包环境中隐藏控制台"""
    if hasattr(sys, '_MEIPASS') and os.name == 'nt':
        return subprocess.CREATE_NO_WINDOW
    return 0

def log_error(message):
    """记录错误信息"""
    print(f"{COLOR_RED}[ERROR] {message}{COLOR_RESET}")
    sys.stdout.flush()

def log_success(message):
    """记录成功信息"""
    print(f"{COLOR_GREEN}[SUCCESS] {message}{COLOR_RESET}")
    sys.stdout.flush()

def log_warning(message):
    """记录警告信息"""
    print(f"{COLOR_YELLOW}[WARNING] {message}{COLOR_RESET}")
    sys.stdout.flush()

def output_status(status_dict):
    """输出状态信息到stdout，供GUI解析"""
    print(f"STATUS_JSON:{json.dumps(status_dict, ensure_ascii=False)}")
    sys.stdout.flush()

def run_git_command(cmd, error_msg, allow_conflict=False, timeout=60):
    """
    执行git命令，添加超时机制，支持实时输出
    
    Args:
        cmd: 要执行的命令
        error_msg: 错误消息
        allow_conflict: 是否允许冲突
        timeout: 超时时间（秒），默认60秒
    """
    stdout_lines = []
    stderr_lines = []
    process = None
    
    try:
        print(f">>> 正在执行: {cmd}")
        sys.stdout.flush()
        
        # 设置Git环境变量以使用UTF-8编码
        env = os.environ.copy()
        env['LC_ALL'] = 'C.UTF-8'
        env['LANG'] = 'C.UTF-8'
        
        # 使用Popen实现实时输出，指定编码为utf-8
        process = subprocess.Popen(
            cmd, 
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将stderr重定向到stdout以实现实时输出
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',  # 遇到编码错误时替换为占位符
            bufsize=1,  # 行缓冲
            env=env,
            creationflags=get_subprocess_flags()
        )
        
        # 实时读取输出
        try:
            while True:
                if process.stdout is None:
                    break
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.rstrip()
                    print(line)  # 实时打印输出
                    sys.stdout.flush()
                    stdout_lines.append(line)
            
            # 等待进程完成，设置超时
            return_code = process.wait(timeout=timeout)
            
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                process.wait()
            raise subprocess.TimeoutExpired(cmd, timeout)
        
        stdout_output = '\n'.join(stdout_lines)
        stderr_output = '\n'.join(stderr_lines)
        
        # 检查返回码
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, cmd, stdout_output, stderr_output)
            
        return subprocess.CompletedProcess(
            cmd, return_code, stdout_output, stderr_output
        )
        
    except subprocess.TimeoutExpired as e:
        log_error(f"命令执行超时 ({timeout}秒): {cmd}")
        log_error(f"{error_msg}")
        if not allow_conflict:
            input("按回车键退出...")
            sys.exit(1)
        return subprocess.CompletedProcess(
            cmd, 124, "", f"命令执行超时: {cmd}"
        )
        
    except subprocess.CalledProcessError as e:
        # 对于实时输出的情况，错误信息已经在stdout中
        stdout_output = '\n'.join(stdout_lines)
        stderr_output = '\n'.join(stderr_lines)
        
        # 检查是否是冲突相关的错误
        combined_output = stdout_output + stderr_output
        if allow_conflict and ("CONFLICT" in combined_output or 
                              "git rebase --continue" in combined_output or 
                              "git merge --continue" in combined_output):
            log_warning(f"{error_msg}")
            log_warning("检测到冲突，请手动解决冲突后，在界面上点击'继续'按钮...")
            return subprocess.CompletedProcess(
                e.cmd, 10, stdout_output, stderr_output
            )
        
        log_error(f"{error_msg}")
        log_error(f"错误码: {e.returncode}")
        if not allow_conflict:
            # 在打包环境中不显示 input 提示
            if not hasattr(sys, '_MEIPASS'):
                input("按回车键退出...")
            sys.exit(1)
        return subprocess.CompletedProcess(
            e.cmd, e.returncode, stdout_output, stderr_output
        )

def execute_git_workflow(project_path, target_branch="develop"):
    """执行git工作流程"""
    try:
        os.chdir(project_path)
    except Exception as e:
        log_error(f"无法切换到目录: {e}")
        return False
    
    # 获取当前分支名称
    try:
        result = run_git_command('git rev-parse --abbrev-ref HEAD', "获取分支名称失败", timeout=10)
        if result.returncode != 0:
            return False
        current_branch = result.stdout.strip()
    except Exception as e:
        log_error(f"获取分支名称失败: {str(e)}")
        return False
    
    # 修改检查未提交改动的方式
    try:
        result = run_git_command(
            f'git log {current_branch} --not origin/{target_branch} --oneline',
            "检查本地提交失败",
            timeout=10
        )
        if result.returncode != 0:
            return False
        local_commits = result.stdout.strip()
    except Exception as e:
        log_error(f"检查本地提交失败: {str(e)}")
        return False
    
    if not local_commits:
        log_success(f"当前分支 {current_branch} 没有需要同步到{target_branch}的改动，无需操作")
        return True

    print(f"\n当前分支: {current_branch}")
    print(f"目标分支: {target_branch}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    sys.stdout.flush()
    
    # 执行git操作流程
    commands = [
        (f"git pull --rebase origin {target_branch}", "rebase失败，请手动解决冲突！", True, 120),  # rebase可能需要更长时间
        (f"git switch {target_branch}", "切换分支失败！", False, 10),
        ("git pull", "拉取代码失败！", False, 60),
        (f"git merge {current_branch}", "合并失败，请手动解决冲突！", True, 30),
        ("git push", "推送失败！", False, 120),  # push可能需要更长时间
        (f"git switch {current_branch}", "切换回原分支失败！", False, 10)
    ]
    
    # 记录当前执行到的步骤索引
    step_index = 0
    while step_index < len(commands):
        cmd, error_msg, allow_conflict, timeout = commands[step_index]
        result = run_git_command(cmd, error_msg, allow_conflict, timeout)
        
        # 检查是否遇到冲突
        if result.returncode == 10:  # 自定义状态码，表示冲突
            # 输出冲突状态供GUI解析
            conflict_info = {
                "status": "conflict", 
                "step": step_index, 
                "branch": current_branch,
                "target_branch": target_branch,
                "command": cmd
            }
            output_status(conflict_info)
            return conflict_info
        
        # 检查是否超时或其他错误
        if result.returncode != 0:
            if result.returncode == 124:  # 超时
                log_error("操作超时，请检查网络连接或手动执行命令")
            return False
        
        step_index += 1
    
    log_success("\n所有操作已完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.stdout.flush()
    return True

def continue_after_conflict(project_path, step_index, current_branch, target_branch="develop"):
    """冲突解决后继续执行"""
    try:
        os.chdir(project_path)
    except Exception as e:
        log_error(f"无法切换到目录: {e}")
        return False
    
    print(f"\n继续执行，当前分支: {current_branch}")
    print(f"目标分支: {target_branch}")
    sys.stdout.flush()
    
    # 执行git操作流程
    commands = [
        (f"git pull --rebase origin {target_branch}", "rebase失败，请手动解决冲突！", True, 120),
        (f"git switch {target_branch}", "切换分支失败！", False, 10),
        ("git pull", "拉取代码失败！", False, 60),
        (f"git merge {current_branch}", "合并失败，请手动解决冲突！", True, 30),
        ("git push", "推送失败！", False, 120),
        (f"git switch {current_branch}", "切换回原分支失败！", False, 10)
    ]
    
    # 从中断的步骤继续执行
    while step_index < len(commands):
        cmd, error_msg, allow_conflict, timeout = commands[step_index]
        
        # 对于第一步rebase冲突后继续
        if step_index == 0 and cmd.startswith("git pull --rebase"):
            cmd = "git rebase --continue"
        
        # 对于第四步merge冲突后继续
        if step_index == 3 and cmd.startswith("git merge"):
            cmd = "git merge --continue"
        
        result = run_git_command(cmd, error_msg, allow_conflict, timeout)
        
        # 检查是否再次遇到冲突
        if result.returncode == 10:  # 自定义状态码，表示冲突
            # 输出冲突状态供GUI解析
            conflict_info = {
                "status": "conflict", 
                "step": step_index, 
                "branch": current_branch,
                "target_branch": target_branch,
                "command": cmd
            }
            output_status(conflict_info)
            return conflict_info
        
        # 检查是否超时或其他错误
        if result.returncode != 0:
            if result.returncode == 124:  # 超时
                log_error("操作超时，请检查网络连接或手动执行命令")
            return False
        
        step_index += 1
    
    log_success("\n所有操作已完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sys.stdout.flush()
    return True

def main():
    if len(sys.argv) < 2:
        log_error("请传入项目路径作为参数！")
        print(f"用法: python {os.path.basename(__file__)} \"项目路径\" [--target-branch 目标分支]")
        # 在打包环境中不显示 input 提示
        if not hasattr(sys, '_MEIPASS'):
            input("按回车键退出...")
        sys.exit(1)
        
    project_path = sys.argv[1]
    target_branch = "develop"  # 默认目标分支
    
    # 解析目标分支参数
    if "--target-branch" in sys.argv:
        try:
            target_branch_index = sys.argv.index("--target-branch")
            if target_branch_index + 1 < len(sys.argv):
                target_branch = sys.argv[target_branch_index + 1]
        except (ValueError, IndexError):
            log_error("无效的 --target-branch 参数")
            sys.exit(1)
    
    # 检查是否是继续执行模式
    if len(sys.argv) >= 5 and sys.argv[2] == "--continue":
        step_index = int(sys.argv[3])
        current_branch = sys.argv[4]
        
        # 在继续模式中也支持目标分支参数
        continue_target_branch = "develop"
        if len(sys.argv) >= 7 and sys.argv[5] == "--target-branch":
            continue_target_branch = sys.argv[6]
        
        return continue_after_conflict(project_path, step_index, current_branch, continue_target_branch)
    else:
        return execute_git_workflow(project_path, target_branch)

if __name__ == "__main__":
    main()