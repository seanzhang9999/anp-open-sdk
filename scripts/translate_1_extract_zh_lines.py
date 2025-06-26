import os
import re

SRC_DIRS = [
    'anp_open_sdk_framework_demo/', 
    'data_user/localhost_9527/',
]
MD_FILE = 'zh_lines_for_translation.md'

def is_chinese(line):
    return re.search('[\u4e00-\u9fff]', line)


def scan_py_files(src_dir):
    zh_lines = []
    for root, dirs, files in os.walk(src_dir):
        # Exclude .venv directory
        dirs[:] = [d for d in dirs if d != '.venv']
        print(f"Scanning {root}")  # <-- 添加这一行
        for f in files:
            if f.endswith('.py'):
                full_path = os.path.join(root, f)
                with open(full_path, 'r', encoding='utf-8') as fp:
                    for idx, line in enumerate(fp, 1):
                        if is_chinese(line):
                            zh_lines.append((full_path, idx, line.rstrip('\n')))
    return zh_lines

def write_md(zh_lines, md_file):
    with open(md_file, 'w', encoding='utf-8') as f:
        last_file = None
        for file, lineno, line in zh_lines:
            if file != last_file:
                f.write(f'\n## {file}\n\n')
                last_file = file
            f.write(f'- Line {lineno}: `{line}`\n')
            f.write(f'  - Translation: \n\n')

if __name__ == '__main__':
    all_zh_lines = []
    for src_dir in SRC_DIRS:
        all_zh_lines.extend(scan_py_files(src_dir))
    write_md(all_zh_lines, MD_FILE)
    print(f"Extracted {len(all_zh_lines)} Chinese lines. See {MD_FILE}")
