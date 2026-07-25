#!/usr/bin/env bash
set -euxo pipefail

GODOT_VERSION=${GODOT_VERSION:-4.6.3}
ANDROID_SDK_ROOT=${ANDROID_SDK_ROOT:-/tmp/android-sdk}
BUILD_TOOLS_VERSION=${BUILD_TOOLS_VERSION:-36.0.0}
APK_NAME=${APK_NAME:-RealityBuilder-Lite-v0.10.17-Android.apk}

# Reconstruct source.
cat reality_builder_build/source.tar.xz.b64.part* > /tmp/source.b64
echo 'c7ab30484a65f2728fba7906b1c690a5aedfb818a2b299fb50f58dac9a41e024  /tmp/source.b64' | sha256sum -c -
base64 --decode /tmp/source.b64 > /tmp/RealityBuilder.tar.xz
echo 'c11bd036e629990c006f3c22127349c2c6ae8d615fcf041c26fdc607251cf85d  /tmp/RealityBuilder.tar.xz' | sha256sum -c -
rm -rf /tmp/reality-builder-source RealityBuilder
mkdir -p /tmp/reality-builder-source
python3 - <<'PY'
import tarfile
with tarfile.open('/tmp/RealityBuilder.tar.xz', mode='r:xz') as archive:
    archive.extractall('/tmp/reality-builder-source')
PY
PROJECT_FILE=$(find /tmp/reality-builder-source -type f -name project.godot -print -quit)
test -n "$PROJECT_FILE"
PROJECT_SOURCE=$(dirname "$PROJECT_FILE")
cp -a "$PROJECT_SOURCE" RealityBuilder

# Apply the low-end Android override.
test -s reality_builder_build/overrides/game_session.gd
cp reality_builder_build/overrides/game_session.gd RealityBuilder/scripts/game_session.gd
sed -i 's/OS.get_name() == "Android"/OS.get_name() == "Android" or OS.has_environment("RB_FORCE_MOBILE")/' RealityBuilder/scripts/game_session.gd
sed -i 's/PackedStringArray("4.3", "GL Compatibility")/PackedStringArray("4.6", "GL Compatibility")/' RealityBuilder/project.godot
sed -i 's/run\/max_fps=45/run\/max_fps=30/' RealityBuilder/project.godot
if ! grep -q '^textures/vram_compression/import_etc2_astc=true$' RealityBuilder/project.godot; then
  sed -i '/^\[rendering\]$/a textures/vram_compression/import_etc2_astc=true' RealityBuilder/project.godot
fi
grep -q 'WorldLoadingLayer' RealityBuilder/scripts/game_session.gd
grep -q 'sun.shadow_enabled = not low_end_mobile' RealityBuilder/scripts/game_session.gd

# Install Android tooling required by Godot 4.6.
rm -rf "$ANDROID_SDK_ROOT" /tmp/android-tools /tmp/android-tools.zip
mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools/latest" /tmp/android-tools
wget -q -O /tmp/android-tools.zip https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
unzip -q /tmp/android-tools.zip -d /tmp/android-tools
cp -a /tmp/android-tools/cmdline-tools/. "$ANDROID_SDK_ROOT/cmdline-tools/latest/"
SDKMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
yes | "$SDKMANAGER" --sdk_root="$ANDROID_SDK_ROOT" --licenses >/dev/null || true
"$SDKMANAGER" --sdk_root="$ANDROID_SDK_ROOT" \
  'platform-tools' \
  "build-tools;$BUILD_TOOLS_VERSION" \
  'platforms;android-36' \
  'cmake;3.10.2.4988404' \
  'ndk;28.1.13356709'

TEMPLATE_SOURCE=$(find /root/.local/share/godot -type f -name android_debug.apk -printf '%h\n' 2>/dev/null | head -n 1)
test -n "$TEMPLATE_SOURCE"
TEMPLATE_TARGET="$HOME/.local/share/godot/export_templates/${GODOT_VERSION}.stable"
mkdir -p "$TEMPLATE_TARGET"
cp -a "$TEMPLATE_SOURCE"/. "$TEMPLATE_TARGET"/
test -f "$TEMPLATE_TARGET/android_debug.apk"
test -f "$TEMPLATE_TARGET/android_release.apk"

JAVA_HOME_REAL=${JAVA_HOME:-$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")}
mkdir -p "$HOME/.android" "$HOME/.config/godot"
DEBUG_KEYSTORE="$HOME/.android/reality_builder_lite.keystore"
rm -f "$DEBUG_KEYSTORE"
keytool -genkeypair -v \
  -keystore "$DEBUG_KEYSTORE" \
  -storepass android \
  -alias realitybuilderlite \
  -keypass android \
  -dname 'CN=Reality Builder Lite,O=Godnit,C=YE' \
  -keyalg RSA -keysize 2048 -validity 10000 -deststoretype PKCS12

printf '[gd_resource type="EditorSettings" format=3]\n\n[resource]\n' > "$HOME/.config/godot/editor_settings-4.6.tres"
{
  printf '\nexport/android/java_sdk_path = "%s"\n' "$JAVA_HOME_REAL"
  printf 'export/android/android_sdk_path = "%s"\n' "$ANDROID_SDK_ROOT"
  printf 'export/android/debug_keystore = "%s"\n' "$DEBUG_KEYSTORE"
  printf 'export/android/debug_keystore_user = "realitybuilderlite"\n'
  printf 'export/android/debug_keystore_pass = "android"\n'
} >> "$HOME/.config/godot/editor_settings-4.6.tres"

cat > RealityBuilder/export_presets.cfg <<EOF
[preset.0]
name="Android"
platform="Android"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/android/$APK_NAME"
patches=PackedStringArray()
encryption_include_filters=""
encryption_exclude_filters=""
seed=0
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.0.options]
custom_template/debug=""
custom_template/release=""
gradle_build/use_gradle_build=false
gradle_build/export_format=0
architectures/armeabi-v7a=true
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
version/code=1017
version/name="0.10.17"
package/unique_name="com.godnit.realitybuilder.lite"
package/name="Reality Builder Lite"
package/signed=true
package/app_category=1
keystore/debug="$DEBUG_KEYSTORE"
keystore/debug_user="realitybuilderlite"
keystore/debug_password="android"
launcher_icons/main_192x192="res://assets/icon.png"
screen/immersive_mode=true
screen/support_small=true
screen/support_normal=true
screen/support_large=true
screen/support_xlarge=true
user_data_backup/allow=false
command_line/extra_args=""
apk_expansion/enable=false
permissions/internet=false
permissions/access_network_state=false
permissions/vibrate=false
EOF

# Parse/import all scripts.
cd RealityBuilder
godot --headless --editor --quit --path . 2>&1 | tee import-lite.log
if grep -E 'SCRIPT ERROR|Parse Error|Invalid call' import-lite.log; then
  echo 'Godot import found a script error.' >&2
  exit 21
fi

# Start an actual starter world and wait for all major systems to initialize.
cat > scripts/runtime_smoke_test.gd <<'GDSCRIPT'
extends SceneTree

func _initialize() -> void:
    call_deferred("_run_test")

func _run_test() -> void:
    var session_script = load("res://scripts/game_session.gd")
    if session_script == null:
        push_error("Could not load game_session.gd")
        quit(31)
        return
    var session = session_script.new()
    session.world_id = "ci_smoke_world"
    session.world_name = "اختبار"
    session.world_template = "starter"
    session.world_save_path = "user://ci_smoke_world.json"
    root.add_child(session)
    for _frame in range(240):
        await process_frame
        if session.hud != null and session.world != null and session.player != null and session.planning_system != null:
            print("RUNTIME_WORLD_SESSION_OK")
            session.queue_free()
            quit(0)
            return
    push_error("World session did not finish initialization within 240 frames")
    quit(32)
GDSCRIPT
RB_FORCE_MOBILE=1 timeout 120s godot --headless --path . --script res://scripts/runtime_smoke_test.gd 2>&1 | tee runtime-lite.log
grep -q 'RUNTIME_WORLD_SESSION_OK' runtime-lite.log

# Export and validate the Android APK.
mkdir -p build/android
godot --headless --verbose --path . --export-debug Android "build/android/$APK_NAME" 2>&1 | tee build/android/export-lite.log
test -s "build/android/$APK_NAME"
if grep -E 'SCRIPT ERROR|Parse Error|Invalid call' build/android/export-lite.log; then
  echo 'Godot export found a script error.' >&2
  exit 22
fi
"$ANDROID_SDK_ROOT/build-tools/$BUILD_TOOLS_VERSION/apksigner" verify --verbose "build/android/$APK_NAME"
unzip -tq "build/android/$APK_NAME"
"$ANDROID_SDK_ROOT/build-tools/$BUILD_TOOLS_VERSION/aapt" dump badging "build/android/$APK_NAME" | tee build/android/badging-lite.txt
grep -q "package: name='com.godnit.realitybuilder.lite'" build/android/badging-lite.txt
grep -q 'armeabi-v7a' build/android/badging-lite.txt
grep -q 'arm64-v8a' build/android/badging-lite.txt
sha256sum "build/android/$APK_NAME" | tee build/android/SHA256SUMS-LITE.txt
SIZE=$(stat -c%s "build/android/$APK_NAME")
SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $SIZE/1048576}")
echo "APK size: $SIZE_MB MB ($SIZE bytes)"
test "$SIZE" -le $((150 * 1024 * 1024))
