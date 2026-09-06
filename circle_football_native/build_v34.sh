#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p=Path('circle_football_native/build_v33.sh').read_text()
p=p.replace('python3 v33_visual_patch.py\n','python3 v33_visual_patch.py\npython3 v34_patch.py\n',1)
p=p.replace("grep -q 'float speed=220f\\*s;' src/com/godnit/circlefootballlite/MainActivity.java",
            "grep -q 'float speed=190f\\*s;' src/com/godnit/circlefootballlite/MainActivity.java\ngrep -q 'countdownV34' src/com/godnit/circlefootballlite/MainActivity.java\ngrep -q 'collidePostV34' src/com/godnit/circlefootballlite/MainActivity.java\ngrep -q 'stabilizeSqueezeV34' src/com/godnit/circlefootballlite/MainActivity.java",1)
p=p.replace("grep -q 'versionName=\"3.3.0\"' AndroidManifest.xml","grep -q 'versionName=\"3.4.0\"' AndroidManifest.xml",1)
p=p.replace('CircleFootball-Android81-v3.3.apk','CircleFootball-Android81-v3.4.apk')
p=p.replace("package: name='com.godnit.circlefootballlite.v33'","package: name='com.godnit.circlefootballlite.v34'")
p=p.replace("versionCode='23'","versionCode='24'")
p=p.replace("versionName='3.3.0'","versionName='3.4.0'")
Path('/tmp/build_v34_inner.sh').write_text(p)
PY
bash /tmp/build_v34_inner.sh
