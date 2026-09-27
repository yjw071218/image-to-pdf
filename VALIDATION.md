# Release validation — 2.0.0

Validated on Windows 11 x64, Python 3.10.11, Pillow 12.3.0, pypdf 6.19.0, PDFium/pypdfium2 5.13.0, cryptography 50.0.1, PyInstaller 6.22.3 and Inno Setup 7.1.0.

The following checks passed both in the Python source application and in the self-contained Windows executable:

| Check | Result |
| --- | --- |
| A4 physical page dimensions; actual rendered top/bottom and left/right padding | Passed |
| A3, A5, ISO B4/B5, Letter, Legal, custom sizes, landscape and automatic orientation | Passed |
| Minimum margins, transparent pixels and EXIF orientation | Passed |
| Import and export every frame of a multipage TIFF | Passed |
| Merge images and pages from multiple PDFs in an arbitrary order | Passed |
| Delete unselected source pages and extract individual pages | Passed |
| Retain PDF text and original PDF page dimensions | Passed |
| Duplicate a page and rotate only one copy | Passed |
| Open, preview and export an AES-256-encrypted PDF using its password | Passed |
| Retry an incorrect password in the import UI | Passed |
| Reject invalid page ranges, excessive margins and nonfinite sizes | Passed |
| Preserve existing output on conversion failure or cancellation | Passed |
| Reject overwriting an original source PDF | Passed |
| UI reorder, range deletion, undo/redo, rotation, duplication and blank insertion | Passed |
| UI previews and selected-page-only export | Passed |
| 20 simultaneous image/PDF launches produce 30 pages in one isolated window | Passed |
| Korean and space-containing source paths | Passed |

The installer compiled successfully with context-menu registration for nine file types (PDF plus eight image extensions). A screenshot of the actual page editor is included in `assets/screenshot.png`.

The 2.0 installer was not installed over the currently running 1.0 application, to preserve the user's open work. Installation/removal had been tested for 1.0; 2.0 validation covers source, frozen executable, installer compilation and registration-script review. Manual Explorer clicks, other machines, Windows 10 and ARM emulation were not tested.

Run `app.py --self-test <report.json>` or `ImageToPDF.exe --self-test <report.json>` to repeat application checks. The concurrency check uses an isolated instance and does not interact with a running user session.
