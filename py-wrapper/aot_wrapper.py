import ctypes
import os
import sys
from pathlib import Path

# --- 1. 加载原生库 ---


def _get_lib_path():
    """根据操作系统确定库文件路径和加载器"""
    base_path = Path(os.path.dirname(__file__)).parent / "bin/Release/net9.0"
    base_path = base_path.as_posix()

    if sys.platform == "win32":
        lib_path = os.path.join(base_path, "win-x64/publish/MyAotLibrary.dll")
        loader = ctypes.WinDLL
    elif sys.platform == "linux":
        lib_path = os.path.join(base_path, "linux-x64/publish/MyAotLibrary.so")
        loader = ctypes.CDLL
    elif sys.platform == "darwin":  # macOS
        lib_path = os.path.join(base_path, "osx-arm64/publish/MyAotLibrary.dylib")
        loader = ctypes.CDLL
    else:
        raise RuntimeError("Unsupported platform")

    if not os.path.exists(lib_path):
        raise FileNotFoundError(f"库文件未找到，请先编译 C# 项目: {lib_path}")

    return loader(lib_path)


# 加载库
_lib = _get_lib_path()

# --- 2. 定义函数原型 (至关重要！) ---

# void* create_processor(char* prefix)
_lib.create_processor.argtypes = [ctypes.c_char_p]
_lib.create_processor.restype = ctypes.c_void_p  # IntPtr 对应 c_void_p

# void destroy_processor(void* handle)
_lib.destroy_processor.argtypes = [ctypes.c_void_p]
_lib.destroy_processor.restype = None

# char* processor_process_text(void* handle, char* text)
_lib.processor_process_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
_lib.processor_process_text.restype = ctypes.c_void_p  # 返回的是指针

# void free_string_memory(void* stringPtr)
_lib.free_string_memory.argtypes = [ctypes.c_void_p]
_lib.free_string_memory.restype = None

# --- 3. 创建 Python 代理类 ---


class TextProcessor:
    """
    一个 Python 代理类，它在后台管理 C# AOT 对象的生命周期。

    这是你的库用户唯一会看到的类。
    它实现了上下文管理器（'with' 语句）以确保资源被正确释放。
    """

    def __init__(self, prefix: str):
        """
        在 C# 中创建一个 TextProcessor 实例。
        """
        prefix_bytes = prefix.encode("utf-8")

        # 调用 C# API 来创建对象
        self._handle = _lib.create_processor(prefix_bytes)

        if not self._handle:
            raise RuntimeError(f"创建 C# TextProcessor 失败 (前缀: {prefix})")

        # print(f"[Python] 代理已创建, 句柄: {self._handle}")

    def process(self, text: str) -> str:
        """
        调用 C# 实例的 Process 方法。
        """
        if not self._handle:
            raise RuntimeError("实例已被销毁，无法调用方法")

        text_bytes = text.encode("utf-8")

        # 1. 调用 C#，获取一个字符串指针。
        # 注意：这里的 result_ptr 可能是一个 Python 'int' 或 'c_void_p' 对象。
        result_ptr = _lib.processor_process_text(self._handle, text_bytes)

        # 检查 C# 是否返回了空指针 (IntPtr.Zero)
        if result_ptr == 0:
            raise RuntimeError("C# 方法执行失败或返回空指针 (IntPtr.Zero)")

        try:
            # 2. **【核心修复】**：使用 raw integer 地址 (result_ptr) 直接实例化 c_char_p
            # 这样保证了 c_char_ptr 始终是一个带有 .value 属性的 ctypes 指针对象。
            c_char_ptr = ctypes.c_char_p(result_ptr)

            # 3. 读取指针的值并解码
            result_str = c_char_ptr.value
            result_str = result_str.decode("utf-8") if result_str is not None else ""

        except Exception as e:
            # 打印更清晰的错误信息
            raise RuntimeError(f"从 C# 结果转换字符串时发生错误: {e}")

        finally:
            # 4. 关键：无论成功失败，只要 result_ptr 是非零地址，就必须释放它
            _lib.free_string_memory(result_ptr)

        return result_str

    def close(self):
        """
        显式销毁 C# 对象。
        """
        if self._handle:
            # print(f"[Python] 正在销毁代理, 句柄: {self._handle}")
            _lib.destroy_processor(self._handle)
            self._handle = None  # 防止重复释放

    # --- 资源管理三件套 ---

    def __enter__(self):
        """用于 'with' 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """在 'with' 语句结束时自动调用 close()"""
        self.close()

    def __del__(self):
        """
        作为最后的保险，当 Python GC 回收此对象时尝试释放。
        注意：不保证 __del__ 会被及时调用，所以 'with' 语句是首选。
        """
        self.close()
