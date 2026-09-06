#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
cd "$ROOT/circle_football_native"

export ANDROID_SDK_ROOT="${RUNNER_TEMP:-/tmp}/android-sdk"
mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools/latest" "${RUNNER_TEMP:-/tmp}/cf-tools"
if [ ! -x "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" ]; then
  wget -q -O "${RUNNER_TEMP:-/tmp}/tools.zip" https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
  rm -rf "${RUNNER_TEMP:-/tmp}/cf-tools"/*
  unzip -q "${RUNNER_TEMP:-/tmp}/tools.zip" -d "${RUNNER_TEMP:-/tmp}/cf-tools"
  cp -a "${RUNNER_TEMP:-/tmp}/cf-tools/cmdline-tools/." "$ANDROID_SDK_ROOT/cmdline-tools/latest/"
fi
yes | "$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$ANDROID_SDK_ROOT" --licenses >/dev/null || true
"$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager" --sdk_root="$ANDROID_SDK_ROOT" "platforms;android-35" "build-tools;35.0.1"

# EXACT v2.2 gameplay stack. Do not apply any gameplay patch newer than v2.2.
python3 v17_run.py
python3 v18_run.py
python3 v22_patch.py
python3 v32_identity_patch.py

grep -q 'float speed=220f\*s;' src/com/godnit/circlefootballlite/MainActivity.java
grep -q 'versionName="3.2.0"' AndroidManifest.xml
! grep -q 'ballHolderV29' src/com/godnit/circlefootballlite/MainActivity.java
! grep -q 'possessionV29' src/com/godnit/circlefootballlite/MainActivity.java
! grep -q 'roleChaserV30' src/com/godnit/circlefootballlite/MainActivity.java
! grep -q 'kickAimPointer' src/com/godnit/circlefootballlite/MainActivity.java
! grep -q 'humanHasBall' src/com/godnit/circlefootballlite/MainActivity.java

sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg
mkdir -p res/raw "${RUNNER_TEMP:-/tmp}/cf-audio"
A="${RUNNER_TEMP:-/tmp}/cf-audio"
curl -fL --retry 3 -o "$A/kick_a.mp3" https://assets.mixkit.co/active_storage/sfx/2108/2108-preview.mp3
curl -fL --retry 3 -o "$A/kick_b.mp3" https://assets.mixkit.co/active_storage/sfx/2112/2112-preview.mp3
curl -fL --retry 3 -o "$A/ball_bounce.mp3" https://assets.mixkit.co/active_storage/sfx/2077/2077-preview.mp3
curl -fL --retry 3 -o "$A/goal_cheer.mp3" https://assets.mixkit.co/active_storage/sfx/3022/3022-preview.mp3
curl -fL --retry 3 -o "$A/crowd_burst.mp3" https://assets.mixkit.co/active_storage/sfx/2111/2111-preview.mp3
curl -fL --retry 3 -o "$A/ui_click.mp3" https://assets.mixkit.co/active_storage/sfx/1114/1114-preview.mp3
curl -fL --retry 3 -o "$A/crowd_loop.mp3" https://assets.mixkit.co/active_storage/sfx/363/363-preview.mp3
curl -fL --retry 3 -o "$A/menu_music.mp3" https://raw.githubusercontent.com/argosopentech/Conquest/d0dbaa8fb50ef9348a8910cac2c80e453c99bd0a/Assets/Audio/loops/mixkit-sports-highlights-51.mp3

ffmpeg -hide_banner -loglevel error -y -i "$A/kick_a.mp3" -t 1.4 -ac 1 -ar 22050 -b:a 80k res/raw/kick_a.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/kick_b.mp3" -t 1.4 -ac 1 -ar 22050 -b:a 80k res/raw/kick_b.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/ball_bounce.mp3" -t 1.2 -ac 1 -ar 22050 -b:a 72k res/raw/ball_bounce.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/goal_cheer.mp3" -t 3.6 -ac 1 -ar 22050 -b:a 80k res/raw/goal_cheer.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/crowd_burst.mp3" -t 2.7 -ac 1 -ar 22050 -b:a 72k res/raw/crowd_burst.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/ui_click.mp3" -t 0.8 -ac 1 -ar 22050 -b:a 64k res/raw/ui_click.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/crowd_loop.mp3" -t 16 -ac 2 -ar 32000 -b:a 80k res/raw/crowd_loop.mp3
ffmpeg -hide_banner -loglevel error -y -i "$A/menu_music.mp3" -t 28 -ac 2 -ar 32000 -b:a 96k res/raw/menu_music.mp3

BT="$ANDROID_SDK_ROOT/build-tools/35.0.1"
JAR="$ANDROID_SDK_ROOT/platforms/android-35/android.jar"
rm -rf build obj dex classes.dex
mkdir -p build obj dex
javac -encoding UTF-8 -source 8 -target 8 -classpath "$JAR" -d obj $(find src -name '*.java' -print)
"$BT/d8" --min-api 21 --lib "$JAR" --output dex $(find obj -name '*.class' -print)
"$BT/aapt" package -f -M AndroidManifest.xml -S res -I "$JAR" -F build/base.apk
cp dex/classes.dex classes.dex
"$BT/aapt" add build/base.apk classes.dex >/dev/null
"$BT/zipalign" -f 4 build/base.apk build/aligned.apk
rm -f classes.dex

keytool -genkeypair -noprompt -keystore build/app.keystore -storepass android -alias app -keypass android -dname "CN=CircleFootball" -keyalg RSA -keysize 2048 -validity 10000
"$BT/apksigner" sign --ks build/app.keystore --ks-pass pass:android --key-pass pass:android --out build/CircleFootball-Android81-v3.2.apk build/aligned.apk
"$BT/apksigner" verify --verbose build/CircleFootball-Android81-v3.2.apk
"$BT/aapt" dump badging build/CircleFootball-Android81-v3.2.apk | tee build/badging.txt
grep -q "package: name='com.godnit.circlefootballlite.v32'" build/badging.txt
grep -q "versionCode='22'" build/badging.txt
grep -q "versionName='3.2.0'" build/badging.txt
grep -q "sdkVersion:'21'" build/badging.txt
unzip -l build/CircleFootball-Android81-v3.2.apk | tee build/apk-files.txt
echo "APK_SIZE_BYTES=$(stat -c%s build/CircleFootball-Android81-v3.2.apk)" | tee build/size.txt
