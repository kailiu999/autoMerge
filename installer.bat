@echo off
echo Git�ϲ����߰�װ����
echo.

set "INSTALL_DIR=%PROGRAMFILES%\GitMergeTool"
set "DESKTOP_SHORTCUT=%USERPROFILE%\Desktop\Git�ϲ�����.lnk"
set "START_MENU_SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Git�ϲ�����.lnk"

echo ���ڰ�װ��: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo �����ļ�...
copy "GitMergeTool.exe" "%INSTALL_DIR%\" >nul
if errorlevel 1 (
    echo ����: �޷������ļ�����װĿ¼
    echo ���Թ���Ա������д˰�װ����
    pause
    exit /b 1
)

echo ���������ݷ�ʽ...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\GitMergeTool.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo ������ʼ�˵���ݷ�ʽ...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\GitMergeTool.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()" >nul 2>&1

echo.
echo ��װ��ɣ�
echo ��װλ��: %INSTALL_DIR%
echo �����ݷ�ʽ�Ѵ���
echo ��ʼ�˵���ݷ�ʽ�Ѵ���
echo.
pause
