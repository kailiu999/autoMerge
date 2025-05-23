# Git分支合并工具

一个基于Python和Tkinter的Git分支合并GUI工具，用于简化Git分支合并工作流，特别是在处理多项目时提高工作效率。

![Git分支合并工具界面](ui.png)

## 功能特点

- 图形化界面，操作简单直观
- 自动执行Git分支合并工作流
- 支持多项目快捷切换
- 实时显示命令执行状态和输出
- 自动处理合并冲突场景
- 保存常用项目路径为快捷标签
- 支持超时机制，避免网络问题导致程序卡死
- 多线程处理，界面始终保持响应
- 支持取消正在执行的操作

## 工作流程

此工具自动执行以下Git操作：

1. 从develop分支拉取最新代码并rebase当前分支
2. 切换到develop分支
3. 拉取develop分支最新代码
4. 将功能分支合并到develop分支
5. 推送更新后的develop分支到远程仓库
6. 切换回原功能分支

在合并过程中如遇到冲突，工具会暂停并提示用户手动解决冲突，然后可通过界面上的"继续"按钮恢复自动化流程。

## 使用方法

### 系统要求

- Windows操作系统
- Python 3.6或更高版本
- Git客户端已安装并配置

### ⚠️ 重要：首次使用前的配置

**在使用工具前，请务必修改代码中的项目路径：**

1. 打开 `git_merge_gui.py` 文件
2. 找到第41-44行的快捷标签配置：
   ```python
   self.add_quick_tag("baotou-management-web", "D:\\project\\baotou-management-web")
   self.add_quick_tag("baotou-lifeline-web", "D:\\project\\baotou-lifeline-web")
   self.add_quick_tag("neimeng-lifeline-web", "D:\\project\\neimeng-lifeline-web")
   self.add_quick_tag("neimeng-management-web", "D:\\project\\neimeng-management-web")
   ```
3. 将这些路径替换为你本地的实际项目路径，例如：
   ```python
   self.add_quick_tag("我的项目1", "C:\\Users\\你的用户名\\项目\\项目1")
   self.add_quick_tag("我的项目2", "C:\\Users\\你的用户名\\项目\\项目2")
   ```
4. 如果你不需要这些快捷标签，可以删除这些行或注释掉

### 启动方式

双击`启动Git合并工具.bat`文件或在命令行中运行：

```bash
python git_merge_gui.py
```

### 操作步骤

1. 在界面中输入或选择Git项目的本地路径
2. 点击"运行"按钮开始自动合并流程
3. 如遇到冲突，程序会暂停并提示手动解决
4. 解决冲突后，点击"继续"按钮继续执行剩余步骤
5. 如需中途停止，可点击"取消"按钮终止操作
6. 完成后可通过终端右上角的"清空"按钮清空日志并准备下一次操作

### 快捷标签

工具会记住使用过的项目路径，并创建快捷标签以便于快速访问。点击任意标签即可自动填充相应的项目路径。

### 故障排除

- **程序无响应**：新版本已修复此问题，现在使用多线程处理，界面始终保持响应
- **网络超时**：工具设置了合理的超时时间，网络问题会自动提示
- **操作卡住**：可使用"取消"按钮中断当前操作
- **路径不存在**：请确保输入的项目路径正确且包含.git目录

## 文件说明

- `git_merge_gui.py` - GUI界面实现
- `git_merge_auto.py` - Git命令执行逻辑
- `启动Git合并工具.bat` - 快速启动批处理文件
- `git_macos_bigsur_icon_190141.ico` - 应用程序图标

## 提示

- 使用前请确保当前分支的更改已提交
- 工具执行的是将当前分支合并到develop分支的操作
- 合并冲突需手动解决，然后点击"继续"按钮
- 程序会实时显示各操作的执行状态和输出信息
- 网络较慢时请耐心等待，工具会自动处理超时情况

## 许可证

本项目采用 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解更多详情

```
MIT License

Copyright (c) 2023 项目作者

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
``` 