# AotPyWrapperSample

一个使用 .NET NativeAOT 构建的原生库（C#），并通过 Python `ctypes` 进行调用的示例工程。Python 侧提供了一个轻量封装（代理类），演示如何安全地创建/销毁原生对象并交换字符串数据。

> 约定：本文档中的所有 Python 命令均使用 `uv`，不使用 `python` 或 `pip`。需要安装依赖时统一使用 `uv add`。


## 项目结构
- `MyAotLibrary.csproj`：C# 原生库项目（目标框架 `net9.0`）。
- `TextProcessor.cs` / `NativeApi.cs`：导出供 Python 调用的 AOT API（创建/销毁、处理字符串、释放内存）。
- `py-wrapper/aot_wrapper.py`：Python 端 `ctypes` 封装，定位已发布的原生库并声明函数签名。
- `py-wrapper/main.py`：演示脚本，展示上下文管理器与手动释放两种用法。
- `bin/Release/net9.0/<rid>/publish/`：`dotnet publish` 输出目录，Python 从此处加载原生库。


## 环境准备
- 安装 `.NET SDK 9.0`（或对应本机已安装版本）。
- 安装 `uv`（Python 包/运行管理器），并确保本机有 Python 3.11+。
- 可选：`pytest`（如果需要运行 Python 侧测试）。


## 构建原生库（NativeAOT）
Python 封装会从 `bin/Release/net9.0/<rid>/publish/` 读取原生库文件：
- Windows：`MyAotLibrary.dll`
- Linux：`MyAotLibrary.so`
- macOS：`MyAotLibrary.dylib`

使用以下命令进行发布（示例以 Release、`net9.0` 为主）：
- Windows（x64）：
  - `dotnet publish MyAotLibrary.csproj -c Release -f net9.0 -r win-x64 /p:PublishAot=true --self-contained true`
- Linux（x64）：
  - `dotnet publish MyAotLibrary.csproj -c Release -f net9.0 -r linux-x64 /p:PublishAot=true --self-contained true`
- macOS（Apple Silicon）：
  - `dotnet publish MyAotLibrary.csproj -c Release -f net9.0 -r osx-arm64 /p:PublishAot=true --self-contained true`

发布完成后，确认目录存在：
- `bin/Release/net9.0/win-x64/publish/MyAotLibrary.dll`
- 或 `bin/Release/net9.0/linux-x64/publish/MyAotLibrary.so`
- 或 `bin/Release/net9.0/osx-arm64/publish/MyAotLibrary.dylib`

> 提示：如果你改用 `Debug` 或修改 `TargetFramework`，请同步调整 `py-wrapper/aot_wrapper.py` 中的 `base_path` 与框架/目录，以确保能正确定位原生库。


## 运行 Python 演示
- 在仓库根目录执行：
  - `uv run py-wrapper/main.py`

脚本会：
- 使用 `with TextProcessor(prefix="[LOG]")` 自动创建/销毁 C# 对象；
- 演示手动创建并调用 `close()` 的方式；
- 在处理字符串后，自动调用 C# 的 `free_string_memory` 释放返回的内存。

## 更多示例
- 在仓库根目录执行：
  - `uv run py-wrapper/examples.py`

包含内容：
- 使用上下文管理器进行资源自动释放；
- 手动生命周期管理并演示销毁后调用的错误；
- 多个实例并行（不同前缀），观察行为差异；
- 在独立函数中复用同一实例（跨函数传递代理）。


## Python 依赖与测试
- 添加测试依赖：
  - `uv add pytest`
- 运行测试（如有）：
  - `uv run pytest -q`

> 当前 `py-wrapper/aot_wrapper.py` 仅使用标准库（`ctypes` / `os` / `sys` / `pathlib`），无需额外三方库即可运行示例。


## 常见问题
- 文件未找到（`FileNotFoundError`）：
  - 请先执行上文的 `dotnet publish`，并确认发布目录和文件名与当前操作系统匹配；
  - 确保 `aot_wrapper.py` 的 `base_path` 与你的发布目录一致。
- 运行时报错或返回空指针：
  - Python 侧已对空指针（`IntPtr.Zero`）进行检查与错误提示；
  - 如需排查，请在 C# 侧确认导出方法签名与 `ctypes` 的 `argtypes/restype` 一致。
- 资源释放：
  - Python 在读取原生字符串后会调用 `free_string_memory` 释放内存；
  - 原生对象由 `TextProcessor.close()` 释放，推荐使用 `with` 语句自动管理生命周期。


## 代码约定
- Python 侧涉及类名时，使用 `cls.__qualname__`，不要使用 `cls.__name__`。
- 需要安装依赖或执行脚本时，统一用 `uv add` / `uv run`。


## 示例：自行调用封装
```python
from aot_wrapper import TextProcessor

with TextProcessor(prefix="[LOG]") as tp:
    print(tp.process("First"))
    print(tp.process("Second"))

# 手动方式
proc = TextProcessor(prefix="[MANUAL]")
print(proc.process("Hello"))
proc.close()
```


## 目录与路径说明
- Python 封装默认查找：`bin/Release/net9.0/<rid>/publish/`；
- 你可以按需修改 `py-wrapper/aot_wrapper.py` 中的 `base_path`（例如切换到 `Debug` 或变更目标框架）。


## 参考与扩展
- 如需把更多方法暴露给 Python：
  - 在 C# 侧添加导出函数并维护一个可用的句柄类型；
  - 在 Python 侧添加相应的 `argtypes` / `restype` 声明与封装方法；
  - 确保所有跨语言分配的内存都由一侧统一释放，避免泄漏。
