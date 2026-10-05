"""Simulate Explorer launching one process per selected image."""
import ctypes
from pathlib import Path
import subprocess
import sys
import os
import uuid
import tempfile
import time
import tkinter as tk
from PIL import Image
import app
from ui import App
from test_app import make_pdf


def test():
    session = uuid.uuid4().hex
    inbox = app.DATA_DIR / 'tests' / session / 'inbox-v2'
    instance_name = 'Local\\ImageToPDF_v2_' + session
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, instance_name)
    assert handle and ctypes.get_last_error() != 183, 'Unable to create isolated test instance.'
    inbox.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    ui = App(root, inbox=inbox)
    processes = []
    command = [sys.executable] if getattr(sys, 'frozen', False) else [str(Path(sys.executable).with_name('pythonw.exe')), str(app.BASE / 'app.py')]
    try:
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for i in range(100):
                path = Path(directory) / f'테스트 문서 {i}{".png" if i % 2 == 0 else ".pdf"}'
                if i % 2 == 0:
                    Image.new('RGB', (10, 10), 'red').save(path)
                else:
                    make_pdf(path, [f'PDF {i} page 1', f'PDF {i} page 2'])
                paths.append(str(path))
            for path in paths:
                processes.append(subprocess.Popen(command + [path], env={**os.environ, 'IMAGETOPDF_TEST_SESSION': session}))
            deadline = time.monotonic() + 100
            while len(ui.paths) < len(paths) and time.monotonic() < deadline:
                root.update()
                time.sleep(.03)
            assert set(ui.paths) == set(paths), (len(ui.paths), len(paths))
            assert len(ui.items) == 150, 'All PDF pages must be collected'
            for process in processes:
                assert process.wait(timeout=10) == 0
            print('PASS: 100 simultaneous image/PDF invocations collected as 150 pages in one isolated window, including Korean/space paths')
    finally:
        ui.dispose()
        kernel.CloseHandle(ctypes.c_void_p(handle))
        if not list(inbox.iterdir()):
            inbox.rmdir()
            inbox.parent.rmdir()


if __name__ == '__main__':
    test()
