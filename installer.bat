@echo off
echo Git合并工具安装程序
echo.

set "INSTALL_DIR=%PROGRAMFILES%\GitMergeTool"
set "DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\Git合并工具.lnk"
set "START_MENU_SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Git合并工具.lnk"

echo 正在安装到: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo 复制文件...
copy "GitMergeTool.exe" "%INSTALL_DIR%\" >nul
if errorlevel 1 (
    echo 错误: 无法复制文件到安装目录
    echo 请以管理员身份运行此安装程序
    pause
    exit /b 1
)

echo 创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\GitMergeTool.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo 创建开始菜单快捷方式...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\GitMergeTool.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo.
echo 安装完成！
echo 安装位置: %INSTALL_DIR%
echo 桌面快捷方式已创建
echo 开始菜单快捷方式已创建
echo.
pause
