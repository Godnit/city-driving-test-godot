#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p=Path('circle_football_native/build_v29.sh').read_text()
p=p.replace('python3 v29_patch.py\\n','python3 v29_patch.py\\npython3 v30_patch.py\\n',1)
p=p.replace("grep -q 'versionName=\\\"2.9.0\\\"' AndroidManifest.xml","grep -q 'versionName=\\\"3.0.0\\\"' AndroidManifest.xml\\ngrep -q 'roleChaserV30' src/com/godnit/circlefootballlite/MainActivity.java",1)
p=p.replace('CircleFootball-Android81-v2.9.apk','CircleFootball-Android81-v3.0.apk')
p=p.replace("package: name='com.godnit.circlefootballlite.v29'","package: name='com.godnit.circlefootballlite.v30'")
p=p.replace("versionCode='20'","versionCode='21'")
p=p.replace("versionName='2.9.0'","versionName='3.0.0'")
Path('/tmp/build_v30_inner.sh').write_text(p)
PY
bash /tmp/build_v30_inner.sh
