# Smoke-Test Checklist

Run from a clean repository checkout after activating the development virtual environment.

```bash
python -m pip install -e . pytest
python -m pytest
python -m bible_reader --help
python -m bible_reader --version
python -m bible_reader doctor
python -m bible_reader books
python -m bible_reader chapters John
python -m bible_reader --no-color John 3:16
python -m bible_reader --no-color read John 3
python -m bible_reader --no-color search shepherd
python -m bible_reader --no-color compare John 3:16
python -m bible_reader tui
```

Console command smoke test:

```bash
bible --help
bible --version
bible doctor
bible books
bible chapters Ps
bible --no-color Ps 23
bible --no-color search world --book John
bible --no-color compare Romans 8:28-30 --versions ASV
```

Import smoke test using the tiny checked-in fixture:

```bash
rm -f /tmp/bible-reader-smoke.sqlite3 /tmp/bible-reader-smoke-study.json
bible import-usfx tests/fixtures/asv_tiny.usfx --db /tmp/bible-reader-smoke.sqlite3
bible --db /tmp/bible-reader-smoke.sqlite3 --no-color Ps 23
bible --study /tmp/bible-reader-smoke-study.json bookmark add John 3:16 --label Gospel
bible --study /tmp/bible-reader-smoke-study.json bookmarks
bible --study /tmp/bible-reader-smoke-study.json note add "John 3:16" "Read in discourse context"
bible --study /tmp/bible-reader-smoke-study.json notes
```

Expected result: commands complete without tracebacks. Search with no matches may intentionally return exit code `1`.


## Default database smoke test

```bash
bible init-db --force
bible doctor
bible books
bible John 3:16
```

The initialized default database currently contains the packaged ASV sample bundle until a full public-domain ASV import source is wired in.


## ASV USFX smoke test

With a local eBible ASV USFX zip downloaded:

```bash
bible init-db --force --usfx-source ~/Downloads/bible-sources/eng-asv_usfx.zip
bible doctor
bible Genesis 1:1
bible read Psalm 23
bible search resurrection --book Romans
```
