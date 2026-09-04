from pathlib import Path
import re

src = Path('v18_patch.py').read_text(encoding='utf-8')
old = r'(?:static\s+)?(?:void|float|int|boolean|short\[\]|String|MediaPlayer)\s+'
new = r'(?:static\s+)?(?:void|float(?:\[\])?|int|boolean|short\[\]|String|MediaPlayer)\s+'
if old not in src:
    raise RuntimeError('v18 matcher pattern not found')
fixed = src.replace(old, new, 1)
exec(compile(fixed, 'v18_patch_runtime.py', 'exec'), {'__name__':'__main__'})

# v18 replaces the v17 wall helpers with stronger versions next to resolveBallDisc.
# Remove the later v17 copies so Java sees only the new implementation.
java_path = Path('src/com/godnit/circlefootballlite/MainActivity.java')
text = java_path.read_text(encoding='utf-8')

def remove_later_copies(text, method_name):
    pattern = re.compile(r'(?m)^        void\s+' + re.escape(method_name) + r'\s*\(')
    while True:
        matches = list(pattern.finditer(text))
        if len(matches) <= 1:
            return text
        m = matches[-1]
        brace = text.find('{', m.end())
        if brace < 0:
            raise RuntimeError('opening brace not found for duplicate ' + method_name)
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
            raise RuntimeError('unterminated duplicate method ' + method_name)
        while end < len(text) and text[end] in '\r\n':
            end += 1
        text = text[:m.start()] + text[end:]

for method in ('resolveWallPin', 'limitBallSpeed'):
    text = remove_later_copies(text, method)

java_path.write_text(text, encoding='utf-8')
print('Removed duplicate v1.7 wall helpers after v1.8 patch')
