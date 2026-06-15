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
