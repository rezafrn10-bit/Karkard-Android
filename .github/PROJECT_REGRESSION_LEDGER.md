# Project regression ledger and product direction

Last updated: 2026-11-06  
Reference branch: `main`  
Protected baseline commit: `3d2e8ee41fda6032260f17b666a6239678a1d4c9` (Test 254)

## 1. Non-regression rules

1. Treat the Test 254 commit as the last known-good behavior baseline. Do not rewrite or reset `main` to make a test pass.
2. Keep new work on a feature/fix branch and in a draft PR until all required tests pass.
3. Every production behavior change must include a focused unit or instrumentation regression test.
4. Run the complete existing suite after each change. A green partial test is not a green release.
5. Report test counts and skipped tests exactly. A CI job that never starts is an infrastructure/startup failure, not an app test result.
6. Avoid unrelated refactoring, schema changes, versionCode/versionName changes, and APK publication during regression work.
7. Keep the checked-in `Karkard_Android_Project_v0731.zip` as the input archive for this PR unless a new source archive is explicitly adopted as the baseline.
8. Do not merge PR #1 or PR #3 while their changes overlap. Integrate the required test coverage into one validated branch first.

## 2. Verified timeline

| Milestone | Commit / run | Verified outcome | Scope / boundary |
|---|---|---|---|
| Test 254 baseline | `main` at `3d2e8ee` / workflow run #254 | Successful baseline run | Preserve this behavior; this is the reference point for all follow-up diffs. |
| PR #1 created | `test/monthly-worked-values-ui`, head `d185e0d` | Draft, not merged | Adds assertions for the same 09:10 saved-work value on the daily and monthly reporting surfaces. It shares the same overlay/source area as PR #3 and must not be merged independently. |
| PR #3 holiday regression | `fix/monthly-holiday-card-regression`, head `d3cb79c` / run #301 | Unit/build job successful: 30 passed, 0 failed, 0 skipped. API 34 instrumentation: 4 passed, 0 failed, 0 skipped. Debug APK assembled. | Validates daily editor save/reload, 1405-03-06 official-holiday card category and soft-red fill, manual scroll to current-day card, and DB persistence across reopen. |
| Worked-summary extension | head `4c7893a` | Added assertions for 09:10 on daily summary, monthly summary, and the current-day card. Not validated by CI yet. | Test-only coverage plus test tags. Do not claim this extension passes until a real build and API 34 run completes. |
| Overlay context correction | head `b6ff6ad` | Corrected two patch context lines to match the actual source. | No intended runtime behavior change. |
| Regression ledger added | head `895cb11` | Recorded the protected baseline, chronology, non-regression gates, and product direction on the PR branch. | Documentation only; no app-source or `main` change. |
| CI runs after extension | #302 (`42197233224`), #303 (`42197243093`), #304 (`42197504455`), #305 (`42197511307`, attempt 2) | Failed before runner execution: job has `runner_id=0`, blank `runner_name`, empty `steps=[]`; no downloadable job log. API 34 job skipped because build job failed. | Not evidence of a Kotlin/Gradle/test failure. Diagnose GitHub Actions startup/runner/account state before changing app code. |

PR #3 is still draft/open/unmerged. `main` remains at the Test 254 baseline commit. The results from run #301 apply to the earlier PR #3 patch, not to the later 09:10 worked-summary extension.

## 3. Required regression gates

The following checks are cumulative. New tests extend this list; they do not replace earlier tests.

### Calendar and day-category rules
- 1405-03-06 resolves to `تعطیل رسمی` in the Day and Monthly views.
- The monthly card uses its holiday/red visual treatment and must not show `کاری`.
- A manually selected `تعطیل خاص` on an ordinary date survives calendar refresh.
- Official holidays cannot be downgraded by stale/manual legacy values.
- No attendance/work data is deleted or silently rewritten while resolving display status.

### Work-entry and reporting consistency
- Daily editor saves and reloads clock-in/clock-out values after navigation.
- A deterministic 07:10–16:20 interval displays exactly 09:10 on the daily summary, monthly summary, and that date's monthly card.
- Monthly report can scroll to and display the current-day card.
- Daily work times and holiday reason survive database close/reopen.
- Continue to cover overlap handling, hourly leave, fixed/flexible schedule, incomplete entries, overtime, and midnight-crossing shifts before changing their rules.

### CI / release gate
- Unit tests: full suite green (the currently verified baseline is 30/30, zero skipped).
- Debug APK: assembleDebug succeeds.
- Android API 34 instrumentation: all tests green, zero skipped.
- Patch dry-run against the selected source archive succeeds.
- Record commit SHA, workflow run IDs, exact counts, and skipped tests before considering merge.
- No APK install/release or version-number bump until the user approves after verification.

## 4. Product direction and reference apps

The product is a personal, offline-first Persian work-hours ledger, not an enterprise workforce-management system. Keep the existing product constraints: Solar Hijri calendar, configurable daily target (currently 7 hours), Friday and configurable official holidays, daily notes, overtime and leave records, monthly overview, and no salary calculation.

Use these public Google Play listings as product-pattern references (reviewed 2026-11-06); borrow patterns, not branding or implementation:

- [Timesheet - Work Time Tracker](https://play.google.com/store/apps/details?id=com.rauscha.apps.timesheet): one-tap work-session control, manual corrections, breaks, daily/weekly/monthly statistics, task/project organization, exports, and backup/restore.
- [WorkingHours Time Tracker](https://play.google.com/store/apps/details?id=partl.workinghours): easy manual entry/edit, break deduction, shifts crossing midnight, visual reports, date/task filters, and grouped exports.
- [Timesheet — Work Hours Tracker by ReiVi](https://play.google.com/store/apps/details?id=de.reivi.wageguard): a particularly relevant simple/offline model—personal daily target, overtime balance, manual past-shift edits, monthly PDF report, and no required account or cloud.

### Selective roadmap (not a commitment to implement everything)
1. Stabilize the calculations and ensure every surface reads the same canonical daily result.
2. Improve the daily entry experience: fast edit, clear completeness/unsaved state, notes, and safe correction.
3. Strengthen month navigation and the monthly overview: reliable day categories, clear work/required/overtime/leave totals, and useful drill-down.
4. Add dependable local backup/restore and a clear export path before optional sync or automation.
5. Consider timer widgets, reminders, tags/projects, and richer charts only after the core ledger is stable and only if they fit the personal-workflow goal.

## 5. Change protocol

Before editing:
- Read this ledger, inspect the latest PR head, and compare with the Test 254 baseline.
- Identify which existing regression gates could be affected.
- State the exact intended behavior change and the test that will prove it.

After editing:
- Inspect the full diff for unintended changes.
- Run unit tests, assembleDebug, and API 34 instrumentation.
- Update this ledger with the commit, workflow run, exact results, and any failures.
- If GitHub does not start a runner, stop modifying app logic and diagnose CI/account infrastructure first.
