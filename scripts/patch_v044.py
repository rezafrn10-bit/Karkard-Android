from pathlib import Path
import sys

root = Path("project")
main = root / "app/src/main/java/ir/karkard/app/MainActivity.kt"
s = main.read_text(encoding="utf-8")

old = '''    fun deleteWorkRecords(start: String, end: String): Int {
        require(start <= end)
        val database = writableDatabase
        database.beginTransaction()
        return try {
            val args = arrayOf(start, end)
            val affected = countWorkRecords(start, end)
            database.delete("workdays", "date >= ? AND date <= ?", args)
            // Only user-authored holiday reasons; official calendar records are preserved.
            database.delete("holidays", "date >= ? AND date <= ?", args)
            database.setTransactionSuccessful()
            affected
        } finally { database.endTransaction() }
    }

    fun saveDay(d: WorkDay) {
'''
new = '''    /** The single deletion path for one Jalali day, shared by day and range deletion. */
    fun deleteDay(date: String) {
        val database = writableDatabase
        database.beginTransaction()
        try {
            database.delete("workdays", "date = ?", arrayOf(date))
            // Only user-authored holiday reasons; official calendar records are preserved.
            database.delete("holidays", "date = ?", arrayOf(date))
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
    }

    /** Deletes an inclusive Jalali range by invoking the same daily deletion method per date. */
    fun deleteWorkRecords(start: String, end: String): Int {
        require(start <= end)
        val first = parsedJalaliDate(start) ?: throw IllegalArgumentException("Invalid start date")
        val last = parsedJalaliDate(end) ?: throw IllegalArgumentException("Invalid end date")
        val affected = countWorkRecords(start, end)
        var current = first
        while (!current.isAfter(last)) {
            deleteDay(jalaliDateString(current))
            current = current.plusDays(1)
        }
        return affected
    }

    fun saveDayAndHoliday(d: WorkDay, holidayReason: String?) {
        val database = writableDatabase
        database.beginTransaction()
        try {
            saveDay(d)
            if (holidayReason.isNullOrBlank()) removeHoliday(d.date)
            else saveHoliday(d.date, holidayReason.trim())
            database.setTransactionSuccessful()
        } finally {
            database.endTransaction()
        }
    }

    fun saveDay(d: WorkDay) {
'''
assert old in s, "deleteWorkRecords block not found"
s = s.replace(old, new)

old = '''    // Every persisted edit increments workRevision; this read is the display's
    // source of truth when returning to any date, without restarting the app.
    val persistedDay = remember(date, refresh, workRevision) {
        db.getDay(date).let { if (db.hasWorkDay(date)) it else it.copy(dayType=defaultDayType(date)) }
    }
'''
new = '''    // Re-read persisted data whenever the selected date changes or the home screen
    // becomes visible again. Uncommitted editor state is intentionally discarded.
    LaunchedEffect(screen, date) {
        if (screen == "home") {
            day = db.getDay(date).let { if (db.hasWorkDay(date)) it else it.copy(dayType = defaultDayType(date)) }
        }
    }
'''
assert old in s, "persistedDay block not found"
s = s.replace(old, new)
s = s.replace('modifier = Modifier.padding(padding), date = date, rawDay = persistedDay,',
              'modifier = Modifier.padding(padding), date = date, rawDay = day,')

old = '''                        onDayChange = { updated ->
                            // Save every edit immediately, so navigating to another date does not discard it.
                            val saved = updated.copy(date = date)
                            val previousType = day.dayType
                            day = saved
                            db.saveDay(saved)
                            workRevision++
                            if (previousType == "تعطیل مناسبتی" && !hasDayStatus(saved,"تعطیل مناسبتی")) {
                                db.removeHoliday(date)
                            }
                        },
'''
new = '''                        onDayChange = { updated ->
                            // Editing changes UI state only. Persistence is explicit via
                            // the "ذخیره اطلاعات روز" button.
                            day = updated.copy(date = date)
                        },
'''
assert old in s, "onDayChange block not found"
s = s.replace(old, new)
s = s.replace('''                db.deleteWorkRecords(date, date)
                confirmDayDeletion = false
''', '''                db.deleteDay(date)
                confirmDayDeletion = false
''')

old = '''                            db.saveDay(savedDay)
                            if (hasDayStatus(savedDay,"تعطیل مناسبتی")) {
                                if (holidayReason.isNotBlank()) db.saveHoliday(normalized, holidayReason.trim()) else db.removeHoliday(normalized)
                            } else {
                                db.removeHoliday(normalized)
                            }
                            onSaved(savedDay)
'''
new = '''                            db.saveDayAndHoliday(
                                savedDay,
                                holidayReason.takeIf { hasDayStatus(savedDay, "تعطیل مناسبتی") }
                            )
                            onSaved(savedDay)
'''
assert old in s, "save button block not found"
s = s.replace(old, new)

s = s.replace('''                                "مورخ",
                                fontSize = 32.sp,
                                fontWeight = FontWeight.Bold,
''', '''                                "موَرِّخ",
                                fontSize = 32.sp,
                                fontFamily = FontFamily(Font(R.font.layla_thuluth)),
                                fontWeight = FontWeight.Normal,
''')
s = s.replace('''                PersianText("مورخ", fontSize = 21.sp, fontWeight = FontWeight.Bold, color = Color.White)
''', '''                PersianText("موَرِّخ", fontSize = 24.sp, fontFamily = FontFamily(Font(R.font.layla_thuluth)), fontWeight = FontWeight.Normal, color = Color.White, maxLines = 1)
''')
s = s.replace("نسخهٔ برنامه: ۰.۴۳.۰", "نسخهٔ برنامه: ۰.۴۴.۰")
# Track dirty editor state so calendar defaults never overwrite an unsaved choice.
s = s.replace('    var workRevision by remember { mutableIntStateOf(0) }',
              '    var workRevision by remember { mutableIntStateOf(0) }\n    var dayDirty by remember { mutableStateOf(false) }')
s = s.replace('''            day = db.getDay(date).let { if (db.hasWorkDay(date)) it else it.copy(dayType = defaultDayType(date)) }
        }
    }''', '''            day = db.getDay(date).let { if (db.hasWorkDay(date)) it else it.copy(dayType = defaultDayType(date)) }
            dayDirty = false
        }
    }''')
s = s.replace('''                                day = destination
                                date = newDate''', '''                                day = destination
                                dayDirty = false
                                date = newDate''')
s = s.replace('''                            day = updated.copy(date = date)
                        },''', '''                            day = updated.copy(date = date)
                            dayDirty = true
                        },''')
s = s.replace('onSaved = { saved -> day = saved; date = saved.date; refresh++; workRevision++ }',
              'onSaved = { saved -> day = saved; dayDirty = false; date = saved.date; refresh++; workRevision++ }')
s = s.replace('''                            day = reset
                            workRevision++''', '''                            day = reset
                            dayDirty = false
                            workRevision++''')
s = s.replace('date = date, rawDay = day,', 'date = date, rawDay = day, isDayDirty = dayDirty,')
s = s.replace('''    rawDay: WorkDay,
    jalaliYear: Int,''', '''    rawDay: WorkDay,
    isDayDirty: Boolean,
    jalaliYear: Int,''')
s = s.replace('val day = applyCalendarHoliday(rawDay, db)', 'val day = if (isDayDirty) rawDay else applyCalendarHoliday(rawDay, db)')
s = s.replace('''                            workRevision++
                            day = if (date >= deletedFrom''', '''                            workRevision++
                            dayDirty = false
                            day = if (date >= deletedFrom''')

main.write_text(s, encoding="utf-8")

cal = root / "app/src/main/java/ir/karkard/app/JalaliCalendar.kt"
t = cal.read_text(encoding="utf-8")
assert "رفتن به ثبت کارکرد این روز" in t
cal.write_text(t.replace("رفتن به ثبت کارکرد این روز", "رفتن به این روز"), encoding="utf-8")

strings = root / "app/src/main/res/values/strings.xml"
strings_text = strings.read_text(encoding="utf-8")
strings.write_text(strings_text.replace("<string name=" + chr(34) + "app_name" + chr(34) + ">مورخ</string>", "<string name=" + chr(34) + "app_name" + chr(34) + ">موَرِّخ</string>"), encoding="utf-8")

gradle = root / "app/build.gradle.kts"
g = gradle.read_text(encoding="utf-8")
assert 'versionCode = 43' in g and 'versionName = "0.43.0"' in g
g = g.replace("versionCode = 43", "versionCode = 44").replace('versionName = "0.43.0"', 'versionName = "0.44.0"')
gradle.write_text(g, encoding="utf-8")

notes = """# یادداشت انتشار نسخهٔ ۰٫۴۴٫۰

- حذف بازه‌ای اکنون برای هر تاریخ از تابع مشترک deleteDay(date) استفاده می‌کند؛ حذف روزانه و بازه‌ای یک منطق دارند.
- ویرایش فرم روز فقط وضعیت رابط کاربری را تغییر می‌دهد؛ ثبت ساعت‌ها، شیفت، مرخصی، یادداشت و علت تعطیلی تنها با دکمهٔ «ذخیره اطلاعات روز» و در یک تراکنش انجام می‌شود.
- با تغییر تاریخ یا نمایش دوبارهٔ صفحهٔ خانه، داده‌ها دوباره از دیتابیس خوانده می‌شوند؛ خروج از صفحه یا بستن برنامه موجب ذخیرهٔ خودکار نمی‌شود.
- متن دکمهٔ تقویم به «رفتن به این روز» تغییر کرد.
- نام نمایشی برنامه با قلم ثلث Layla Thuluth نمایش داده می‌شود. قلم تحت SIL Open Font License 1.1 است و اعلان مجوز آن همراه پروژه نگه داشته می‌شود.
- شناسهٔ بسته، ApplicationId و تنظیمات امضای برنامه بدون تغییر باقی مانده‌اند.

این بسته بر پایهٔ سورس ZIP موجود در مخزن ساخته شده است. نتیجهٔ کامپایل Android و آزمون رابط باید در GitHub Actions بررسی شود.
"""
(root / "RELEASE_NOTES_v044_FA.md").write_text(notes, encoding="utf-8")
font_dir = root / "app/src/main/res/font"
font_dir.mkdir(parents=True, exist_ok=True)
font_source = Path("/tmp/LaylaThuluth.ttf")
if not font_source.exists():
    raise SystemExit("Missing /tmp/LaylaThuluth.ttf; download the licensed font before patching")
(font_dir / "layla_thuluth.ttf").write_bytes(font_source.read_bytes())
license_source = Path("/tmp/LaylaThuluth-LICENSE.txt")
notice_source = Path("/tmp/LaylaThuluth-UPSTREAM-NOTICES.txt")
if license_source.exists():
    (root / "OFL_Layla_Thuluth.txt").write_bytes(license_source.read_bytes())
if notice_source.exists():
    (root / "Layla_Thuluth_UPSTREAM_NOTICES.txt").write_bytes(notice_source.read_bytes())
print("Patched source tree for 0.44.0")
