import re

MD_FILE = 'zh_lines_for_translation.md'

def parse_md(md_file):
    replacements = {}
    current_file = None
    with open(md_file, 'r', encoding='utf-8') as f:
        for line in f:
            file_match = re.match(r'## (.+)', line)
            if file_match:
                current_file = file_match.group(1).strip()
                continue
            line_match = re.match(r'- Line (\d+): `(.*)`', line)
            if line_match:
                lineno = int(line_match.group(1))
                orig = line_match.group(2)
                translation_line = next(f)
                trans_match = re.match(r'\s*- Translation:\s*(.*)', translation_line)
                translation = trans_match.group(1) if trans_match else ''
                if translation.strip():
                    replacements.setdefault(current_file, []).append((lineno, orig, translation.strip()))
    return replacements



def replace_lines(replacements):
    for file, items in replacements.items():
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for lineno, orig, trans in items:
            idx = lineno - 1
            orig_line = lines[idx]
            if orig_line.strip() == orig.strip():
                leading_ws = re.match(r'^(\s*)', orig_line).group(1)
                lines[idx] = f"{leading_ws}{trans}\n"
            else:
                print(f"[WARN] Line {lineno} in {file} does not match, skipped.")
        with open(file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Updated {file}")

if __name__ == '__main__':
    replacements = parse_md(MD_FILE)
    replace_lines(replacements)
    print("Replacement done.")