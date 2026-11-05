#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is not set}"
LOG_FILE="$PROJECT_ROOT/instrumentation-logcat.txt"

capture_logcat() {
  adb logcat -d -v time > "$LOG_FILE" 2>&1 || true
}
trap capture_logcat EXIT

echo "Working directory: $PWD"
test -f settings.gradle.kts || test -f settings.gradle
test -f app/src/androidTest/java/ir/karkard/app/DailyUiFlowInstrumentedTest.kt

echo "Instrumentation test sources:"
find app/src/androidTest/java -type f -name '*Test.kt' -print

echo "Required UI regression tests:"
grep -nE 'fun (dailyEditorSavePersistsTimesAndReloadsThemAfterLeavingTheScreen|monthlyReportCanManuallyReachTheCurrentDayCard)' app/src/androidTest/java/ir/karkard/app/DailyUiFlowInstrumentedTest.kt

echo "Checking Android emulator readiness..."
api_level="$(timeout 30s adb shell getprop ro.build.version.sdk | tr -d '\r')"
echo "Detected API level: $api_level"
if [[ "$api_level" != "34" ]]; then
  echo "Expected Android API 34, received $api_level." >&2
  exit 1
fi

timeout 30s adb shell cmd package path android
timeout 30s adb shell am get-current-user

echo "Emulator preflight passed. Running connectedDebugAndroidTest..."
gradle --no-daemon --no-build-cache --rerun-tasks --stacktrace connectedDebugAndroidTest

echo "Instrumentation test reports:"
find app/build/reports/androidTests app/build/outputs/androidTest-results -type f \( -name '*.html' -o -name '*.xml' \) -print 2>/dev/null || true
