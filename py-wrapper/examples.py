"""
更多 Python 封装使用示例。

运行：
- uv run py-wrapper/examples.py

注意：在运行之前请先执行 dotnet publish（参见 README）。
"""

from aot_wrapper import TextProcessor


def demo_with_context():
    print("\n=== 示例1：使用 with 上下文管理器（推荐） ===")
    try:
        with TextProcessor(prefix="[CTX]") as tp:
            print("  ", tp.process("first message"))
            print("  ", tp.process("second message"))
    except Exception as e:
        print("  发生错误：", e)


def demo_manual_lifecycle():
    print("\n=== 示例2：手动创建与销毁（演示错误场景） ===")
    try:
        tp = TextProcessor(prefix="[MANUAL]")
        print("  ", tp.process("hello manual"))
        # 主动释放资源
        tp.close()
        # 继续调用将触发错误（演示句柄已销毁的防御）
        try:
            tp.process("should fail")
        except Exception as inner:
            print("  预期错误：", inner)
    except Exception as e:
        print("  发生错误：", e)


def demo_multiple_instances():
    print("\n=== 示例3：多个实例并行存在（不同前缀） ===")
    try:
        with TextProcessor(prefix="[A]") as a, TextProcessor(prefix="[B]") as b:
            print("  A:", a.process("alpha"))
            print("  B:", b.process("beta"))
    except Exception as e:
        print("  发生错误：", e)


def helper_use_processor(tp: TextProcessor, msg1: str, msg2: str):
    """在独立的函数中复用已创建的 TextProcessor。"""
    print("  helper:", tp.process(msg1))
    print("  helper:", tp.process(msg2))


def demo_reuse_across_functions():
    print("\n=== 示例4：跨函数复用同一实例 ===")
    try:
        with TextProcessor(prefix="[FUNC]") as tp:
            helper_use_processor(tp, "from helper 1", "from helper 2")
    except Exception as e:
        print("  发生错误：", e)


if __name__ == "__main__":
    print("--- 开始更多示例 ---")
    demo_with_context()
    demo_manual_lifecycle()
    demo_multiple_instances()
    demo_reuse_across_functions()
    print("\n--- 更多示例结束 ---")

