#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p=Path('circle_football_native/build_v28.sh').read_text()
p=p.replace('python3 v28_patch.py\\n','python3 v28_patch.py\\npython3 v29_patch.py\\n',1)
p=p.replace("grep -q 'versionName=\\\"2.8.0\\\"' AndroidManifest.xml","grep -q 'versionName=\\\"2.9.0\\\"' AndroidManifest.xml\\ngrep -q 'goalLatchedV29' src/com/godnit/circlefootballlite/MainActivity.java\\ngrep -q 'possessionV29' src/com/godnit/circlefootballlite/MainActivity.java\\ngrep -q 'fieldNameV29' src/com/godnit/circlefootballlite/MainActivity.java",1)
p=p.replace('CircleFootball-Android81-v2.8.apk','CircleFootball-Android81-v2.9.apk')
p=p.replace("package: name='com.godnit.circlefootballlite.v28'","package: name='com.godnit.circlefootballlite.v29'")
p=p.replace("versionCode='19'","versionCode='20'")
p=p.replace("versionName='2.8.0'","versionName='2.9.0'")
Path('/tmp/build_v29_inner.sh').write_text(p)
PY
bash /tmp/build_v29_inner.sh
