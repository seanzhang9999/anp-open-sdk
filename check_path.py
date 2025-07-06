import sys
import importlib

try:
    # 尝试导入有问题的模块
    module = importlib.import_module("anp_open_sdk.core.base_user_data")

    # 打印出该模块的实际文件路径
    print("\n✅ Python is loading this file:")
    print(f"   {module.__file__}\n")

except Exception as e:
    print(f"\n❌ Failed to import the module. Error: {e}")

print("🐍 Current Python executable:")
print(f"   {sys.executable}\n")

print("📦 Python's import paths (sys.path):")
for p in sys.path:
    print(f"   - {p}")
print("\n")