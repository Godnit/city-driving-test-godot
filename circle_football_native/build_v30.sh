#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p=Path('circle_football_native/build_v27.sh').read_text()
p=p.replace('python3 v27_patch.py\n','python3 v27_patch.py\npython3 v28_patch.py\npython3 v29_patch.py\npython3 v30_patch.py\n',1)
p=p.replace("grep -q 'splashUntil=SystemClock.uptimeMillis()+2600L' src/com/godnit/circlefootballlite/MainActivity.java","grep -q 'splashUntil=SystemClock.uptimeMillis()+4000L' src/com/godnit/circlefootballlite/MainActivity.java",1)
p=p.replace("grep -q 'versionName=\"2.7.0\"' AndroidManifest.xml","grep -q 'versionName=\"3.0.0\"' AndroidManifest.xml\ngrep -q 'goalLatchedV29' src/com/godnit/circlefootballlite/MainActivity.java\ngrep -q 'possessionV29' src/com/godnit/circlefootballlite/MainActivity.java\ngrep -q 'roleChaserV30' src/com/godnit/circlefootballlite/MainActivity.java",1)
p=p.replace('CircleFootball-Android81-v2.7.apk','CircleFootball-Android81-v3.0.apk')
p=p.replace("package: name='com.godnit.circlefootballlite.v27'","package: name='com.godnit.circlefootballlite.v30'")
p=p.replace("versionCode='18'","versionCode='21'")
p=p.replace("versionName='2.7.0'","versionName='3.0.0'")
Path('/tmp/build_v30_inner.sh').write_text(p)
PY
bash /tmp/build_v30_inner.sh
