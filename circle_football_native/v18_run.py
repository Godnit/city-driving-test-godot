from pathlib import Path

src = Path('v18_patch.py').read_text(encoding='utf-8')
old = r'(?:static\s+)?(?:void|float|int|boolean|short\[\]|String|MediaPlayer)\s+'
new = r'(?:static\s+)?(?:void|float(?:\[\])?|int|boolean|short\[\]|String|MediaPlayer)\s+'
if old not in src:
    raise RuntimeError('v18 matcher pattern not found')
fixed = src.replace(old, new, 1)
exec(compile(fixed, 'v18_patch_runtime.py', 'exec'), {'__name__':'__main__'})
