# Release validation — 1.0.0

Validated locally on Windows 11 x64 with Python 3.10.11, Pillow 12.3.0, pypdf 6.19.0, PyInstaller 6.22.3 and Inno Setup 7.1.0.

| Check | Result |
| --- | --- |
| Source application regression checks | Passed |
| Frozen standalone application regression checks | Passed |
| Installed application regression checks | Passed |
| Correct PDF page count, order and dimensions | Passed |
| Transparent pixels flattened to white | Passed |
| EXIF orientation applied | Passed |
| Failed conversion preserves existing output file | Passed |
| UI reordering, duplicate removal and preview | Passed |
| 20 simultaneous invocations collected in one window | Passed |
| Korean filenames and filenames containing spaces | Passed |
| Installer creates correct executable command in registry | Passed |
| Uninstaller removes executable and all eight file-type menu entries | Passed |
| Reinstallation | Passed |

These checks simulate Explorer's per-file process invocation and inspect installed registry entries. They do not automate physical Explorer context-menu clicks. Other machines, Windows 10, and ARM emulation were not tested.

Run `app.py --self-test <report.json>` or `ImageToPDF.exe --self-test <report.json>` to repeat application checks. Close existing ImageToPDF windows first. Installer and archive checksums are provided with each release.
