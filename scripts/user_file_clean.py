import os
import glob

# 设置根目录
root_dir = os.path.join('data_user', 'localhost_9527', 'anp_users')

# 遍历所有 user_* 目录
for user_dir in glob.glob(os.path.join(root_dir, 'user_*')):
    key_path = os.path.join(user_dir, 'key-1_private.pem')
    if not os.path.isfile(key_path):
        # 构造新的目录名
        parent = os.path.dirname(user_dir)
        new_dir = os.path.join(parent, 'break_' + os.path.basename(user_dir))
        # 避免已存在同名目录
        if not os.path.exists(new_dir):
            print(f"Renaming {user_dir} -> {new_dir}")
            os.rename(user_dir, new_dir)
        else:
            print(f"目标目录 {new_dir} 已存在，跳过。")
    else:
        print(f"{user_dir} 已有 key-1_private.pem，跳过。")