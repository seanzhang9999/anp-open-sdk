import os
import re

SRC_DIR = '.'  # 根目录，可自定义
MD_FILE = 'zh_lines_for_translation.md'

def is_chinese(s):
    return re.search(r'[\u4e00-\u9fa5]', s) is not None

def scan_py_files(src_dir):
    zh_lines = []
    for root, dirs, files in os.walk(src_dir):
        # Exclude .venv directory
        dirs[:] = [d for d in dirs if d != '.venv']
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
    zh_lines = scan_py_files(SRC_DIR)
    write_md(zh_lines, MD_FILE)
    print(f"Extracted {len(zh_lines)} Chinese lines. See {MD_FILE}")