# Data Sources and Import Policy

`bible-reader` is offline-first, but bundled text must still be legally reusable.
The first full bundled translation target is the American Standard Version
(ASV 1901), which is public domain in the United States.

## Translation import goals

- Keep Scripture text separate from user notes, bookmarks, and commentary.
- Import into SQLite rather than reading large source files at runtime.
- Validate source bundles before database writes.
- Preserve poetry line breaks and paragraph/pericope break metadata when known.
- Support multiple translations without changing the core reference parser.
- Avoid network access during normal reading/search commands.

## Current bundle shape

The importer expects JSON with three top-level keys:

```json
{
  "translation": {
    "code": "ASV",
    "name": "American Standard Version",
    "language": "en",
    "copyright": "Public domain: ASV 1901"
  },
  "books": [
    {"id": 43, "name": "John", "testament": "NT", "order": 43}
  ],
  "verses": [
    {
      "book": "John",
      "chapter": 3,
      "verse": 16,
      "text": "For God so loved the world...",
      "paragraph_break_before": true
    }
  ]
}
```

This is an internal import format. The final ASV source may come from a
public-domain source in another format, then be converted into this shape.

## Safety rules

- Do not scrape or bundle copyrighted translations without permission.
- Do not execute downloaded data as code.
- Do not build SQL with string interpolation from source text or user input.
- Use parameterized SQLite writes and reads.
- Treat imported Bible/commentary data as untrusted text.

## ASV USFX source import

Stage 6 adds a local-file converter for ASV USFX XML source files. The intended
upstream source is a public-domain ASV 1901 USFX/USFM distribution such as the
ASV resources published by eBible.

The converter does not download files automatically. Download the source
manually, verify that it is ASV 1901/public domain, then import either the local
USFX XML file or the eBible USFX zip archive:

```bash
mkdir -p ~/Downloads/bible-sources
curl -L -o ~/Downloads/bible-sources/eng-asv_usfx.zip \
  https://ebible.org/scriptures/eng-asv_usfx.zip
bible init-db --force --usfx-source ~/Downloads/bible-sources/eng-asv_usfx.zip
```

You can also import into an explicit SQLite database path:

```bash
bible import-usfx ~/Downloads/bible-sources/eng-asv_usfx.zip \
  --db ~/.local/share/bible-reader/bible-reader.sqlite3
```

For normalized internal bundles, use:

```bash
bible import-bundle path/to/asv_bundle.json --db ~/.local/share/bible-reader/bible.sqlite3
```

Reading from an imported database is explicit for now:

```bash
bible --db ~/.local/share/bible-reader/bible.sqlite3 John 3:16
bible --db ~/.local/share/bible-reader/bible.sqlite3 read Ps 23
```

The converter currently targets Scripture verse text plus paragraph/poetry
formatting hooks. Footnotes, cross-references, headings, and superscriptions are
intentionally left for later source-format passes so they can be modeled cleanly
rather than jammed into verse text.

## Full ASV local database workflow

After importing the eBible ASV USFX zip with `init-db --usfx-source`, normal
commands automatically use the default local SQLite database:

```bash
bible doctor
bible Genesis 1:1
bible read Matthew 5
bible search resurrection --book Romans
```

Do not commit generated `.sqlite3` files. The repo should contain importer code,
tests, and documentation; each user should build their own local database from
public-domain source files.
