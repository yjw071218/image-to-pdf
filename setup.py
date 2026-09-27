import ctypes
from pathlib import Path
import sys
import winreg

BASE = Path(__file__).resolve().parent
EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp', '.pdf')
KEYS = [rf'Software\Classes\SystemFileAssociations\{ext}\shell\ImageToPDF_ME' for ext in EXTENSIONS]

def install():
    command = f'"{Path(sys.executable).with_name("pythonw.exe")}" "{BASE / "app.py"}" "%1"'
    for path in KEYS:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
            for name, value in [('', 'PDF·이미지 엮기 / 페이지 편집'), ('MultiSelectModel', 'Player'), ('Icon', str(BASE / 'assets' / 'app.ico'))]:
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path + r'\command') as key:
            winreg.SetValueEx(key, '', 0, winreg.REG_SZ, command)
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    print('Context menu installed.')

def uninstall():
    for path in KEYS:
        for target in (path + r'\command', path):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, target)
            except FileNotFoundError:
                pass
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    print('Context menu removed.')

if __name__ == '__main__':
    uninstall() if '--uninstall' in sys.argv else install()
