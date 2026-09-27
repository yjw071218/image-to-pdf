"""Simulate Explorer launching one process per selected image."""
import ctypes
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from PIL import Image
import app


def test():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, app.MUTEX_NAME)
    assert handle and ctypes.get_last_error() != 183, 'Close the app before testing.'
    app.INBOX.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    ui = app.App(root)
    processes = []
    command = [sys.executable] if getattr(sys, 'frozen', False) else [str(Path(sys.executable).with_name('pythonw.exe')), str(app.BASE / 'app.py')]
    try:
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for i in range(20):
                path = Path(directory) / f'테스트 이미지 {i}.png'
                Image.new('RGB', (10, 10), 'red').save(path)
                paths.append(str(path))
            for path in paths:
                processes.append(subprocess.Popen(command + [path]))
            deadline = time.monotonic() + 20
            while len(ui.paths) < len(paths) and time.monotonic() < deadline:
                root.update()
                time.sleep(.03)
            assert set(ui.paths) == set(paths), (len(ui.paths), len(paths))
            for process in processes:
                assert process.wait(timeout=10) == 0
            print('PASS: 20 simultaneous invocations collected in one window, including Korean and spaces in paths')
    finally:
        root.destroy()
        kernel.CloseHandle(ctypes.c_void_p(handle))


if __name__ == '__main__':
    test()
