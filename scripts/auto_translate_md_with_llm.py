import os
import re
import asyncio

# 你可以用 openai.AsyncOpenAI 或 openai.OpenAI
from openai import AsyncOpenAI

MD_FILE = 'zh_lines_for_translation.md'
MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1")

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

async def translate_text(text, model=MODEL_NAME):
    # 1. 提取原文前缀（如 #、//、空格等）
    prefix_match = re.match(r'^(\s*(?:#|//)*\s*)', text)
    prefix = prefix_match.group(1) if prefix_match else ''
    content = text[len(prefix):] if prefix else text

    prompt = (
        "Translate the following Chinese code line or comment into professional English. "
        "You may keep the code/comment structure if needed. "
        "Do not explain. Just output the translation.\n"
        f"{content}"
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
        )
        translated = response.choices[0].message.content.strip()
        # 2. 去除 ```、```python 及多余换行
        translated = re.sub(r"^```(?:\w+)?\s*|```$", "", translated, flags=re.MULTILINE).strip()
        # 3. 去掉翻译内容开头的 //、#、空格等注释符
        translated = re.sub(r'^(\s*(?:#|//)*\s*)', '', translated)
        # 4. 用原文前缀替换
        return f"{prefix}{translated}"
    except Exception as e:
        print(f"[ERROR] OpenAI API failed: {e}")
        return ""

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
            # 下一行是 Translation
            if i+1 < len(lines) and lines[i+1].strip().startswith('- Translation:'):
                trans_line = lines[i+1]
                orig = line_match.group(2)
                # 只翻译空的 Translation
                if trans_line.strip() == '- Translation:':
                    if translated_count >= max_translate:
                        # 达到上限，后续内容原样追加
                        new_lines.extend(lines[i+1:])
                        break
                    print(f"Translating: {orig}")
                    translation = await translate_text(orig)
                    new_lines.append(f'  - Translation: {translation}\n')
                    translated_count += 1
                    i += 2
                    continue
        i += 1

    # 写回
    with open(md_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Auto-translation finished for {md_file}, translated {translated_count} lines.")


if __name__ == '__main__':
    asyncio.run(process_md(MD_FILE))