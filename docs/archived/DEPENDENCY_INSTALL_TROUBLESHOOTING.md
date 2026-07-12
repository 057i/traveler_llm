# 依赖安装故障排除指南

## 当前问题

依赖安装失败，错误信息：
```
OSError: [WinError 5] 拒绝访问: 'hnswlib.cp312-win_amd64.pyd'
```

## 问题原因

`.pyd`文件（Python动态链接库）被占用，无法卸载或替换。可能的原因：
1. 后端服务仍在运行
2. Python进程未完全关闭
3. 杀毒软件占用文件
4. Windows文件系统延迟释放

## 解决方案

### 方案1：重启计算机（最简单有效）
```bash
# 重启后执行
cd E:\大模型开发\代码\网站\travel_proj\backend
.venv\Scripts\pip.exe install -r requirements_stable.txt
```

### 方案2：手动删除虚拟环境并重建
```powershell
# 1. 确保没有Python进程
Get-Process python | Stop-Process -Force

# 2. 删除虚拟环境
Remove-Item -Recurse -Force .venv

# 3. 重建虚拟环境
python -m venv .venv

# 4. 激活并安装依赖
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r backend\requirements_stable.txt
```

### 方案3：使用安全模式删除文件
```powershell
# 启动到安全模式，然后删除：
Remove-Item -Recurse -Force E:\大模型开发\代码\网站\travel_proj\.venv\Lib\site-packages\*hnswlib*
```

### 方案4：延迟删除
```powershell
# 1. 停止所有Python进程
Get-Process python | Stop-Process -Force

# 2. 等待30秒让Windows释放文件句柄
Start-Sleep -Seconds 30

# 3. 再次尝试安装
cd E:\大模型开发\代码\网站\travel_proj\backend
.venv\Scripts\pip.exe install -r requirements_stable.txt
```

## 推荐操作步骤

### 最简单的方法（推荐）：

1. **关闭PyCharm**（如果打开）
2. **停止所有Python进程**：
   ```powershell
   Get-Process python | Stop-Process -Force
   ```
3. **等待1分钟**让Windows释放文件
4. **重启计算机**
5. **重新安装依赖**：
   ```powershell
   cd E:\大模型开发\代码\网站\travel_proj\backend
   .venv\Scripts\pip.exe install -r requirements_stable.txt
   ```

### 如果不想重启：

1. **关闭所有Python相关程序**（PyCharm, VS Code, 终端等）
2. **等待2-3分钟**
3. **使用任务管理器**手动结束所有python.exe进程
4. **重新打开新的PowerShell窗口**
5. **重试安装**

## 验证安装成功

安装成功后运行：
```powershell
python backend\verify_dependencies.py
```

应该看到：
```
[SUCCESS] All dependencies are correctly installed!
[VERIFIED] No dependency conflicts detected!
```

## 后续步骤

安装成功后：

### 1. 配置PyCharm
- Settings → Python Interpreter
- 添加：`.venv\Scripts\python.exe`
- 标记backend为Sources Root
- Invalidate Caches and Restart

### 2. 测试系统
```powershell
# 启动后端
cd backend
python main.py

# 另一个终端启动前端
cd frontend
npm run dev
```

## 预防措施

为避免将来再次出现此问题：

1. **关闭IDE后再更新依赖**
2. **确保后端服务已停止**
3. **一次只运行一个Python进程**
4. **定期清理虚拟环境**：
   ```powershell
   pip cache purge
   ```

## 备选方案：使用系统Python

如果虚拟环境问题持续，可以临时使用系统Python：

```powershell
# 安装到系统Python
python -m pip install -r backend\requirements_stable.txt

# PyCharm使用系统Python
# Settings → Python Interpreter → 选择系统Python
```

**注意**：这不是最佳实践，但可以让你继续工作。

---

**当前状态**：依赖安装因文件占用失败，需要重启计算机或重建虚拟环境后重试。

**所有其他工作已完成**：API优化、功能对调、ChromaDB配置、文档创建等都已完成✅
