#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本 - 将Git合并工具打包为独立的桌面应用
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """安装必要的依赖"""
    print("正在安装构建依赖...")
    
    try:
        # 检查并安装 pyinstaller
        result = subprocess.run([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("安装 PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        else:
            print("PyInstaller 已安装")
            
        # 检查并安装 pillow (用于图标处理)
        result = subprocess.run([sys.executable, "-m", "pip", "show", "pillow"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("安装 Pillow...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pillow"], check=True)
        else:
            print("Pillow 已安装")
            
    except subprocess.CalledProcessError as e:
        print(f"安装依赖失败: {e}")
        return False
    
    return True

def create_spec_file():
    """创建 PyInstaller 规格文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['git_merge_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('git_merge_auto.py', '.'),
        ('git_macos_bigsur_icon_190141.ico', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GitMergeTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI应用不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='git_macos_bigsur_icon_190141.ico',
    version_file='version_info.txt'
)
'''
    
    with open('GitMergeTool.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("已创建 PyInstaller 规格文件: GitMergeTool.spec")

def create_version_info():
    """创建版本信息文件"""
    version_info = '''# UTF-8
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Git合并工具'),
         StringStruct(u'FileDescription', u'Git分支自动合并工具'),
         StringStruct(u'FileVersion', u'1.0.0.0'),
         StringStruct(u'InternalName', u'GitMergeTool'),
         StringStruct(u'LegalCopyright', u'Copyright © 2024'),
         StringStruct(u'OriginalFilename', u'GitMergeTool.exe'),
         StringStruct(u'ProductName', u'Git合并工具'),
         StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("已创建版本信息文件: version_info.txt")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    try:
        # 清理之前的构建
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        
        # 运行 PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", "GitMergeTool.spec", "--clean"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("构建成功！")
        print(f"可执行文件位置: {os.path.abspath('dist/GitMergeTool.exe')}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_installer_script():
    """创建安装脚本"""
    installer_content = '''@echo off
echo Git合并工具安装程序
echo.

set "INSTALL_DIR=%PROGRAMFILES%\\GitMergeTool"
set "DESKTOP_SHORTCUT=%USERPROFILE%\\Desktop\\Git合并工具.lnk"
set "START_MENU_SHORTCUT=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Git合并工具.lnk"

echo 正在安装到: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo 复制文件...
copy "GitMergeTool.exe" "%INSTALL_DIR%\\" >nul
if errorlevel 1 (
    echo 错误: 无法复制文件到安装目录
    echo 请以管理员身份运行此安装程序
    pause
    exit /b 1
)

echo 创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\GitMergeTool.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo 创建开始菜单快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\GitMergeTool.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo.
echo 安装完成！
echo 安装位置: %INSTALL_DIR%
echo 桌面快捷方式已创建
echo 开始菜单快捷方式已创建
echo.
pause
'''
    
    with open('installer.bat', 'w', encoding='gbk') as f:
        f.write(installer_content)
    
    print("已创建安装脚本: installer.bat")

def main():
    """主函数"""
    print("=== Git合并工具桌面应用构建脚本 ===")
    print()
    
    # 检查当前目录
    required_files = ['git_merge_gui.py', 'git_merge_auto.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"错误: 找不到必需文件 {file}")
            print("请在项目根目录运行此脚本")
            sys.exit(1)
    
    # 步骤1: 安装依赖
    if not install_dependencies():
        print("依赖安装失败，退出")
        sys.exit(1)
    
    # 步骤2: 创建配置文件
    create_spec_file()
    create_version_info()
    
    # 步骤3: 构建可执行文件
    if not build_executable():
        print("构建失败，退出")
        sys.exit(1)
    
    # 步骤4: 创建安装脚本
    create_installer_script()
    
    print()
    print("=== 构建完成 ===")
    print("生成的文件:")
    print(f"  可执行文件: {os.path.abspath('dist/GitMergeTool.exe')}")
    print(f"  安装脚本: {os.path.abspath('installer.bat')}")
    print()
    print("使用说明:")
    print("1. 直接双击 dist/GitMergeTool.exe 启动GUI应用")
    print("2. 或者运行 installer.bat 安装到系统")
    print("3. 不再需要使用bat文件启动，exe文件是独立的GUI应用")

if __name__ == "__main__":
    main()