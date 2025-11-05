namespace MyAotLibrary;

/// <summary>
/// 这是我们真正的业务逻辑类。
/// 它对 Python 完全隐藏。
/// </summary>
internal class TextProcessor
{
    private readonly string _prefix;

    internal TextProcessor(string prefix)
    {
        this._prefix = prefix;
        Console.WriteLine($"[C#] TextProcessor 实例已创建，前缀: '{_prefix}'");
    }

    internal string Process(string text)
    {
        return $"{this._prefix}: {text.ToUpper()}";
    }

    internal void Cleanup()
    {
        // 可以在这里执行任何清理逻辑
        Console.WriteLine($"[C#] TextProcessor 实例 (前缀: '{_prefix}') 正在清理...");
    }
}
