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

def run_git_command(cmd, error_msg):
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
        log_error(f"{error_msg}\n{err_msg}")
        input("按回车键退出...")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        log_error("请传入项目路径作为参数！")
        print(f"用法: python {os.path.basename(__file__)} \"项目路径\"")
        input("按回车键退出...")
        sys.exit(1)
        
    project_path = sys.argv[1]
    try:
        os.chdir(project_path)
    except Exception as e:
        log_error(f"无法切换到目录: {e}")
        sys.exit(1)
    
    # 获取当前分支名称
    # 修改获取分支名称的方式
    try:
        result = run_git_command('git rev-parse --abbrev-ref HEAD', "获取分支名称失败")
        current_branch = result.stdout.strip()
    except Exception as e:
        log_error(f"获取分支名称失败: {str(e)}")
        sys.exit(1)
    
    # 修改检查未提交改动的方式
    try:
        result = run_git_command(
            f'git log {current_branch} --not origin/develop --oneline',
            "检查本地提交失败"
        )
        local_commits = result.stdout.strip()
    except Exception as e:
        log_error(f"检查本地提交失败: {str(e)}")
        sys.exit(1)
    
    if not local_commits:
        log_success(f"当前分支 {current_branch} 没有需要同步到develop的改动，无需操作")
        sys.exit(0)

    print(f"\n当前分支: {current_branch}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 执行git操作流程
    commands = [
        ("git pull --rebase origin develop", "rebase失败，请手动解决冲突！"),
        ("git switch develop", "切换分支失败！"),
        ("git pull", "拉取代码失败！"),
        (f"git merge {current_branch}", "合并失败，请手动解决冲突！"),
        ("git push", "推送失败！"),
        (f"git switch {current_branch}", "切换回原分支失败！")
    ]
    
    for cmd, error_msg in commands:
        print(f">>> 正在执行: {cmd}")
        result = run_git_command(cmd, error_msg)
        if result and result.stdout:
            print(result.stdout)
    
    log_success("\n所有操作已完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()