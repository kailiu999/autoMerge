import PyInstaller.__main__
import os

# 获取当前脚本所在目录的绝对路径
base_path = os.path.dirname(os.path.abspath(__file__))

# 主程序文件路径
main_script = os.path.join(base_path, 'baotou_gui.py')

# PyInstaller参数配置
PyInstaller.__main__.run([
    main_script,
    '--name=Git合并工具',  # 生成的exe文件名
    '--onefile',  # 打包成单个exe文件
    '--noconsole',  # 不显示控制台窗口
    '--clean',  # 清理临时文件
    '--add-data', f'{os.path.join(base_path, "git_merge_auto.py")};.',  # 添加依赖的Python脚本
    '--add-data', f'{os.path.join(base_path, "run_git_merge.bat")};.',  # 添加批处理脚本
    '--add-data', f'{os.path.join(base_path, "baotou-management-web.bat")};.',  # 添加管理web批处理脚本
    '--hidden-import=tkinter',  # 添加隐式导入的模块
    '--hidden-import=subprocess',
    '--hidden-import=sys',
    '--hidden-import=os',
    '--hidden-import=json',  # 添加可能用到的json模块
    '--hidden-import=threading',  # 添加可能用到的线程模块
    # 设置程序版本信息
    '--version-file=version.txt',
    # 设置文件信息
    f'--workpath={os.path.join(base_path, "build")}',  # 设置工作目录
    f'--distpath={os.path.join(base_path, "dist")}',  # 设置输出目录
    '--collect-all=tkinter',  # 确保收集所有tkinter相关文件
])