import os
import re
import asyncio

from openai import AsyncOpenAI

MD_FILE = 'zh_lines_for_translation.md'
MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1")

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

async def translate_single_segment(chinese_text, model=MODEL_NAME):
    prompt = (
        "Translate the following Chinese text into professional English. "
        "Do not add any extra symbols or code block markers. Just output the translation.\n"
        f"{chinese_text}"
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=128,
        )
        translated = response.choices[0].message.content.strip()
        translated = re.sub(r"^```(?:\w+)?\s*|```$", "", translated, flags=re.MULTILINE).strip()
        return translated
    except Exception as e:
        print(f"[ERROR] OpenAI API failed: {e}")
        return chinese_text

async def translate_chinese_segments(text, model=MODEL_NAME):
    pattern = re.compile(r'[\u4e00-\u9fa5]+')
    segments = []
    last_end = 0
    tasks = []
    for m in pattern.finditer(text):
        segments.append((m.start(), m.end(), m.group()))
        tasks.append(translate_single_segment(m.group(), model))
    translations = await asyncio.gather(*tasks) if tasks else []
    result = []
    seg_idx = 0
    for i, (start, end, _) in enumerate(segments):
        result.append(text[last_end:start])
        result.append(translations[seg_idx])
        last_end = end
        seg_idx += 1
    result.append(text[last_end:])
    return ''.join(result)

async def process_md(md_file, max_translate=2100):
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    translated_count = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        line_match = re.match(r'- Line (\d+): `(.*)`', line)
        if line_match:
            if i+1 < len(lines) and lines[i+1].strip().startswith('- Translation:'):
                trans_line = lines[i+1]
                orig = line_match.group(2)
                if trans_line.strip() == '- Translation:':
                    if translated_count >= max_translate:
                        new_lines.extend(lines[i+1:])
                        break
                    print(f"Translating: {orig}")
                    translation = await translate_chinese_segments(orig)
                    new_lines.append(f'  - Translation: {translation}\n')
                    translated_count += 1
                    i += 2
                    continue
        i += 1

    with open(md_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Auto-translation finished for {md_file}, translated {translated_count} lines.")

if __name__ == '__main__':
    asyncio.run(process_md(MD_FILE))