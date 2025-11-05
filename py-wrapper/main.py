# 导入你精心封装的代理类
from aot_wrapper import TextProcessor

print("--- 开始 Python AOT 代理演示 ---")

# 推荐的方式：使用 'with' 语句
# 这样能保证 C# 对象被自动创建和销毁
print("\n--- 演示 'with' 语句 (推荐) ---")
try:
    with TextProcessor(prefix="[LOG]") as logger:
        message1 = logger.process("This is the first message")
        message2 = logger.process("This is the second message")

        print(f"  Python 收到: {message1}")
        print(f"  Python 收到: {message2}")

    print("--- 'with' 语句块结束，C# 对象应已被销毁 ---")

except Exception as e:
    print(f"\n发生错误: {e}")


# --- 手动管理生命周期 (不推荐，但可行) ---
print("\n--- 演示手动管理生命周期 ---")
try:
    manual_proc = TextProcessor(prefix="[MANUAL]")
    print(f"  Python 收到: {manual_proc.process('Hello')}")

    # 手动释放资源
    manual_proc.close()

    # 这一行会抛出异常，因为句柄已被释放
    # manual_proc.process('World')

except Exception as e:
    print(f"\n发生错误: {e}")

print("\n--- 演示结束 ---")
