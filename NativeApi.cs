using System.Runtime.InteropServices;

namespace MyAotLibrary;

/// <summary>
/// 暴露给 Python (C) 的静态 API。
/// 负责管理对象的生命周期和方法调用。
/// </summary>
public static class NativeApi
{
    // --- 1. 对象生命周期 ---

    /// <summary>
    /// 创建 TextProcessor 实例并返回一个句柄。
    /// </summary>
    [UnmanagedCallersOnly(EntryPoint = "create_processor")]
    public static IntPtr CreateProcessor(IntPtr prefixPtr)
    {
        try
        {
            string? prefixMaybe = Marshal.PtrToStringUTF8(prefixPtr);
            string prefix = prefixMaybe ?? string.Empty;
            var processor = new TextProcessor(prefix);

            // 关键：创建一个 GCHandle 来 "固定" 托管对象，
            // 防止 GC 在 C++ 持有它时将其移动或回收。
            // 我们返回一个指向此句柄的 IntPtr。
            GCHandle handle = GCHandle.Alloc(processor);
            return GCHandle.ToIntPtr(handle);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[C# ERROR] 创建失败: {ex.Message}");
            return IntPtr.Zero; // 在 Python 中表示失败
        }
    }

    /// <summary>
    /// 释放 GCHandle，允许 GC 回收对象。
    /// </summary>
    [UnmanagedCallersOnly(EntryPoint = "destroy_processor")]
    public static void DestroyProcessor(IntPtr processorHandle)
    {
        if (processorHandle == IntPtr.Zero)
            return;

        try
        {
            // 从 IntPtr 转换回 GCHandle
            GCHandle handle = GCHandle.FromIntPtr(processorHandle);

            // 获取对象实例（如果需要调用清理方法）
            if (handle.Target is TextProcessor processor)
            {
                processor.Cleanup();
            }

            // 释放句柄
            handle.Free();
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[C# ERROR] 销毁失败: {ex.Message}");
        }
    }

    // --- 2. 实例方法调用 ---

    /// <summary>
    /// 调用实例的 Process 方法。
    /// </summary>
    [UnmanagedCallersOnly(EntryPoint = "processor_process_text")]
    public static IntPtr ProcessorProcessText(IntPtr processorHandle, IntPtr textPtr)
    {
        if (processorHandle == IntPtr.Zero)
            return IntPtr.Zero;

        try
        {
            // 1. 从句柄获取实例
            GCHandle handle = GCHandle.FromIntPtr(processorHandle);
            if (handle.Target is not TextProcessor processor)
            {
                return IntPtr.Zero;
            }

            // 2. 转换输入
            string? textMaybe = Marshal.PtrToStringUTF8(textPtr);
            string text = textMaybe ?? string.Empty;

            // 3. 调用业务逻辑
            string result = processor.Process(text);

            // 4. 转换并返回输出 (Python 必须释放这个！)
            return Marshal.StringToCoTaskMemUTF8(result);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[C# ERROR] 处理失败: {ex.Message}");
            return IntPtr.Zero;
        }
    }

    // --- 3. 内存管理 (Python 必须调用) ---

    /// <summary>
    /// 释放由 C# 分配并返回给 Python 的字符串内存。
    /// </summary>
    [UnmanagedCallersOnly(EntryPoint = "free_string_memory")]
    public static void FreeStringMemory(IntPtr stringPtr)
    {
        Marshal.FreeCoTaskMem(stringPtr);
    }
}
