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
adb devices -l
timeout 120s adb wait-for-device
boot_completed=""
for attempt in $(seq 1 60); do
  boot_completed="$(timeout 10s adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  if [[ "$boot_completed" == "1" ]]; then
    break
  fi
  echo "Android boot is not complete yet (attempt $attempt/60)."
  sleep 5
done
if [[ "$boot_completed" != "1" ]]; then
  echo "Android emulator did not finish booting." >&2
  adb devices -l >&2 || true
  adb logcat -d -t 300 >&2 || true
  exit 1
fi
api_level="$(timeout 30s adb shell getprop ro.build.version.sdk | tr -d '\r')"
echo "Detected API level: $api_level"
if [[ "$api_level" != "34" ]]; then
  echo "Expected Android API 34, received $api_level." >&2
  exit 1
fi

# Reproduce the known-good Test 254 weekday so the daily save/reload test
# runs on every CI date instead of being silently skipped on Fridays/holidays.
adb root
timeout 30s adb wait-for-device
timeout 30s adb shell settings put global auto_time 0
timeout 30s adb shell settings put global auto_time_zone 0
timeout 30s adb shell setprop persist.sys.timezone Etc/UTC
timeout 30s adb shell date -s '2026-11-05 12:00:00'
test_date="$(timeout 30s adb shell date -u '+%Y-%m-%d' | tr -d '\r')"
if [[ "$test_date" != "2026-11-05" ]]; then
  echo "Expected deterministic Test 254 date 2026-11-05, received $test_date." >&2
  exit 1
fi

timeout 30s adb shell cmd package path android
timeout 30s adb shell am get-current-user

echo "Emulator preflight passed. Running connectedDebugAndroidTest..."
gradle --no-daemon --no-build-cache --rerun-tasks --max-workers=2 --stacktrace connectedDebugAndroidTest

echo "Instrumentation test reports:"
find app/build/reports/androidTests app/build/outputs/androidTest-results -type f \( -name '*.html' -o -name '*.xml' \) -print 2>/dev/null || true
