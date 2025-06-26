import re

MD_FILE = 'zh_lines_for_translation.md'
OUT_FILE = 'zh_lines_for_translation_check.txt'

def find_chinese_span(s):
    matches = list(re.finditer(r'[\u4e00-\u9fa5]', s))
    if not matches:
        return None, None
    return matches[0].start(), matches[-1].end()

def strip_outer_quotes(s):
    if s.startswith("'") and s.endswith("'") and len(s) > 1:
        return s[1:-1]
    return s

def strip_spaces(s):
    return s.strip()

def check_translations(md_file, out_file):
    problem_count = 0
    with open(md_file, 'r', encoding='utf-8') as f, open(out_file, 'w', encoding='utf-8') as out:
        current_file = None
        for line in f:
            file_match = re.match(r'## (.+)', line)
            if file_match:
                current_file = file_match.group(1).strip()
                out.write(line)
                continue  # 章节头要输出
            line_match = re.match(r'- Line (\d+): `(.*)`', line)
            if line_match:
                lineno = int(line_match.group(1))
                orig = line_match.group(2)
                translation_line = next(f)
                trans_match = re.match(r'\s*- Translation:\s*(.*)', translation_line)
                translation = trans_match.group(1) if trans_match else ''
                orig_stripped = strip_outer_quotes(orig)
                start, end = find_chinese_span(orig_stripped)
                if start is not None and end is not None:
                    prefix = orig_stripped[:start]
                    suffix = orig_stripped[end:]
                    # 忽略空格进行前后缀比较
                    prefix_ok = strip_spaces(translation).startswith(strip_spaces(prefix))
                    suffix_ok = strip_spaces(translation).endswith(strip_spaces(suffix))
                    if not (prefix_ok and suffix_ok):
                        out.write(f'- Line {lineno}: `{orig}`\n')
                        out.write(f'- Translation: {translation}\n')
                        out.write(f'# [CHECK] prefix: `{prefix}` in translation: {prefix_ok}, suffix: `{suffix}` in translation: {suffix_ok}\n')
                        problem_count += 1
                continue
            # 其他行直接跳过

    if problem_count > 0:
        print(f"Check done. Found {problem_count} problem(s). Please review {OUT_FILE}.")
    else:
        print(f"Check done. No problems found! {OUT_FILE} is empty.")

if __name__ == '__main__':
    check_translations(MD_FILE, OUT_FILE)