from pathlib import Path
import re

# IMPORTANT: This patch changes identity only. Gameplay remains exactly v2.2.
m = Path('AndroidManifest.xml')
s = m.read_text(encoding='utf-8')
s = s.replace('com.godnit.circlefootballlite.v22', 'com.godnit.circlefootballlite.v32')
s = re.sub(r'android:versionCode="\d+"', 'android:versionCode="22"', s, count=1)
s = re.sub(r'android:versionName="[^"]+"', 'android:versionName="3.2.0"', s, count=1)
m.write_text(s, encoding='utf-8')
print('Applied v3.2 identity only; gameplay remains exact v2.2')
