import os
import sys
import subprocess
from datetime import datetime

# 颜色常量
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"

def log_error(message):
    print(f"{COLOR_RED}[ERROR] {message}{COLOR_RESET}")

def log_success(message):
    print(f"{COLOR_GREEN}[SUCCESS] {message}{COLOR_RESET}")

def log_warning(message):
    print(f"{COLOR_YELLOW}[WARNING] {message}{COLOR_RESET}")

def run_git_command(cmd, error_msg, allow_conflict=False):
    try:
        # 使用更可靠的编码处理方式
        result = subprocess.run(cmd, check=True, shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        # 统一使用utf-8解码，失败时使用replace策略
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        return subprocess.CompletedProcess(
            result.args, result.returncode, stdout, stderr
        )
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='replace')
        
        # 如果允许冲突，且是rebase或merge冲突，则返回特殊状态码
        if allow_conflict and ("CONFLICT" in err_msg or "git rebase --continue" in err_msg or "git merge --continue" in err_msg):
            log_warning(f"{error_msg}\n{err_msg}")
            log_warning("请手动解决冲突后，在界面上点击'继续'按钮...")
            return subprocess.CompletedProcess(
                e.cmd, 10, e.stdout.decode('utf-8', errors='replace') if e.stdout else "", err_msg
            )
        
        log_error(f"{error_msg}\n{err_msg}")
        if not allow_conflict:
            input("按回车键退出...")
            sys.exit(1)
        return subprocess.CompletedProcess(
            e.cmd, e.returncode, e.stdout.decode('utf-8', errors='replace') if e.stdout else "", err_msg
        )

def execute_git_workflow(project_path):
    try:
        os.chdir(project_path)
    except Exception as e:
        log_error(f"无法切换到目录: {e}")
        return False
    
    # 获取当前分支名称
    try:
        result = run_git_command('git rev-parse --abbrev-ref HEAD', "获取分支名称失败")
        current_branch = result.stdout.strip()
    except Exception as e:
        log_error(f"获取分支名称失败: {str(e)}")
        return False
    
    # 修改检查未提交改动的方式
    try:
        result = run_git_command(
            f'git log {current_branch} --not origin/develop --oneline',
            "检查本地提交失败"
        )
        local_commits = result.stdout.strip()
    except Exception as e:
        log_error(f"检查本地提交失败: {str(e)}")
        return False
    
    if not local_commits:
        log_success(f"当前分支 {current_branch} 没有需要同步到develop的改动，无需操作")
        return True

    print(f"\n当前分支: {current_branch}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 执行git操作流程
    commands = [
        ("git pull --rebase origin develop", "rebase失败，请手动解决冲突！", True),
        ("git switch develop", "切换分支失败！", False),
        ("git pull", "拉取代码失败！", False),
        (f"git merge {current_branch}", "合并失败，请手动解决冲突！", True),
        ("git push", "推送失败！", False),
        (f"git switch {current_branch}", "切换回原分支失败！", False)
    ]
    
    # 记录当前执行到的步骤索引
    step_index = 0
    while step_index < len(commands):
        cmd, error_msg, allow_conflict = commands[step_index]
        print(f">>> 正在执行: {cmd}")
        result = run_git_command(cmd, error_msg, allow_conflict)
        
        # 检查是否遇到冲突
        if result.returncode == 10:  # 自定义状态码，表示冲突
            # 返回特殊状态，通知GUI需要用户处理冲突
            return {"status": "conflict", "step": step_index, "branch": current_branch}
        
        if result and result.stdout:
            print(result.stdout)
        
        step_index += 1
    
    log_success("\n所有操作已完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True

def continue_after_conflict(project_path, step_index, current_branch):
    try:
        os.chdir(project_path)
    except Exception as e:
        log_error(f"无法切换到目录: {e}")
        return False
    
    print(f"\n继续执行，当前分支: {current_branch}")
    
    # 执行git操作流程
    commands = [
        ("git pull --rebase origin develop", "rebase失败，请手动解决冲突！", True),
        ("git switch develop", "切换分支失败！", False),
        ("git pull", "拉取代码失败！", False),
        (f"git merge {current_branch}", "合并失败，请手动解决冲突！", True),
        ("git push", "推送失败！", False),
        (f"git switch {current_branch}", "切换回原分支失败！", False)
    ]
    
    # 从中断的步骤继续执行
    while step_index < len(commands):
        cmd, error_msg, allow_conflict = commands[step_index]
        
        # 对于第一步rebase冲突后继续
        if step_index == 0 and cmd.startswith("git pull --rebase"):
            cmd = "git rebase --continue"
        
        # 对于第四步merge冲突后继续
        if step_index == 3 and cmd.startswith("git merge"):
            cmd = "git merge --continue"
        
        print(f">>> 正在执行: {cmd}")
        result = run_git_command(cmd, error_msg, allow_conflict)
        
        # 检查是否再次遇到冲突
        if result.returncode == 10:  # 自定义状态码，表示冲突
            # 返回特殊状态，通知GUI需要用户处理冲突
            return {"status": "conflict", "step": step_index, "branch": current_branch}
        
        if result and result.stdout:
            print(result.stdout)
        
        step_index += 1
    
    log_success("\n所有操作已完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return True

def main():
    if len(sys.argv) < 2:
        log_error("请传入项目路径作为参数！")
        print(f"用法: python {os.path.basename(__file__)} \"项目路径\"")
        input("按回车键退出...")
        sys.exit(1)
        
    project_path = sys.argv[1]
    
    # 检查是否是继续执行模式
    if len(sys.argv) >= 5 and sys.argv[2] == "--continue":
        step_index = int(sys.argv[3])
        current_branch = sys.argv[4]
        return continue_after_conflict(project_path, step_index, current_branch)
    else:
        return execute_git_workflow(project_path)

if __name__ == "__main__":
    main()