from pathlib import Path

src = Path('v17_patch.py').read_text(encoding='utf-8')
old = '''def replace_method(text, name, replacement):
    needle = name + '('
    pos = text.find(needle)
    if pos < 0:
        raise RuntimeError('method not found: ' + name)
    line_start = text.rfind('\\n', 0, pos) + 1
    brace = text.find('{', pos)
    depth = 0
    end = None
    for i in range(brace, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise RuntimeError('unterminated method: ' + name)
    return text[:line_start] + replacement.rstrip() + text[end:]
'''
new = '''def replace_method(text, name, replacement):
    import re
    pattern = (r'(?m)^        (?:@Override\\s+)?(?:(?:public|protected|private)\\s+)?'
               r'(?:static\\s+)?(?:void|float\\[\\]|float|int|boolean|short\\[\\]|String)\\s+'
               + re.escape(name) + r'\\s*\\(')
    m = re.search(pattern, text)
    if not m:
        raise RuntimeError('method declaration not found: ' + name)
    line_start = m.start()
    brace = text.find('{', m.end())
    depth = 0
    end = None
    for i in range(brace, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise RuntimeError('unterminated method: ' + name)
    return text[:line_start] + replacement.rstrip() + text[end:]
'''
if old not in src:
    raise RuntimeError('expected replace_method implementation not found')
fixed = src.replace(old, new, 1)
exec(compile(fixed, 'v17_patch_runtime.py', 'exec'), {'__name__':'__main__'})
