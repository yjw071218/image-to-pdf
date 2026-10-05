"""Windows single-instance launcher for ImageToPDF."""
import ctypes
import json
import os
from pathlib import Path
import re
import sys
import uuid

VERSION = '2.1.1'
BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'ImageToPDF'
INBOX = DATA_DIR / 'inbox-v2'
MUTEX_NAME = 'Local\\ImageToPDF_v2'
TEST_SESSION = os.environ.get('IMAGETOPDF_TEST_SESSION', '')
if re.fullmatch(r'[0-9a-f]{32}', TEST_SESSION):
    DATA_DIR = DATA_DIR / 'tests' / TEST_SESSION
    INBOX = DATA_DIR / 'inbox-v2'
    MUTEX_NAME += '_' + TEST_SESSION


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        import smoke_test
        smoke_test.run(Path(sys.argv[2]))
        return
    INBOX.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    pending = INBOX / (token + '.tmp')
    # An empty request also restores an already running window.
    pending.write_text(json.dumps(sys.argv[1:]), encoding='utf-8')
    pending.replace(INBOX / (token + '.json'))
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        kernel.CloseHandle(ctypes.c_void_p(handle))
        return
    try:
        import tkinter as tk
        from ui import App
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        root = tk.Tk()
        App(root, INBOX, DATA_DIR)
        root.mainloop()
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))


if __name__ == '__main__':
    main()
