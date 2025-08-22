# 邮件客户端打包指南

本项目可以使用 `PyInstaller` 工具打包成一个独立的 Windows 可执行文件 (`.exe`)。

## 步骤

### 1. 安装依赖

首先，请确保您已经安装了 Python。然后，在项目根目录下打开命令行或终端，安装所需的库：

```bash
pip install -r requirements.txt
```

### 2. 安装 PyInstaller

如果尚未安装 PyInstaller，请运行以下命令：

```bash
pip install pyinstaller
```

### 3. 执行打包命令

在命令行或终端中，确保您位于 `email_client` 文件夹的**上一级目录**（即项目根目录），然后运行以下命令：

```bash
pyinstaller --name "邮件发送客户端" --onefile --windowed --icon="path/to/your/icon.ico" email_client/gui_app.py
```

**命令参数说明:**
*   `--name "邮件发送客户端"`: 指定生成的 `.exe` 文件的名称。
*   `--onefile`: 将所有内容打包成一个单独的 `.exe` 文件。
*   `--windowed`: 运行时不显示黑色的命令行窗口（因为这是一个GUI应用）。
*   `--icon="path/to/your/icon.ico"`: (可选) 为您的应用程序指定一个图标。请将 `path/to/your/icon.ico` 替换为您的图标文件的实际路径。如果不需要图标，可以移除此参数。
*   `email_client/gui_app.py`: 要打包的主程序文件路径。

### 4. 查找 .exe 文件

打包成功后，`PyInstaller` 会在当前目录下创建一个 `dist` 文件夹。您可以在 `dist` 文件夹中找到生成的 `邮件发送客户端.exe` 文件，直接双击运行。
