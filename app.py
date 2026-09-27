import ctypes
import io
import json
import os
from pathlib import Path
import queue
import re
import sys
import tempfile
import threading
import uuid

BASE = Path(__file__).resolve().parent
VERSION = '1.0.0'
DATA_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'ImageToPDF'
INBOX = DATA_DIR / 'inbox'
MUTEX_NAME = 'Local\\ImageToPDF_v1'
EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp')


def natural_key(path):
    return [int(s) if s.isdigit() else s.casefold() for s in re.split(r'(\d+)', Path(path).name)]


def export_pdf(paths, destination, progress=lambda n: None):
    from PIL import Image, ImageOps
    from pypdf import PdfWriter
    writer = PdfWriter()
    temporary = None
    try:
        for index, path in enumerate(paths):
            try:
                with Image.open(path) as original:
                    im = ImageOps.exif_transpose(original)
                    rgba = im.convert('RGBA')
                    rgb = Image.new('RGB', rgba.size, 'white')
                    rgb.paste(rgba, mask=rgba.getchannel('A'))
                    stream = io.BytesIO()
                    rgb.save(stream, 'PDF', resolution=150.0, quality=95)
                    stream.seek(0)
                    writer.append(stream)
                    rgb.close()
                    rgba.close()
                progress(index + 1)
            except Exception as exc:
                raise RuntimeError(f'{Path(path).name}\n{exc}') from exc
        with tempfile.NamedTemporaryFile(dir=Path(destination).parent, suffix='.pdf', delete=False) as output:
            temporary = output.name
            writer.write(output)
        os.replace(temporary, destination)
        temporary = None
    finally:
        writer.close()
        if temporary:
            Path(temporary).unlink(missing_ok=True)


class App:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.root = root
        self.paths = []
        self.busy = False
        self.events = queue.Queue()
        root.title(f'ImageToPDF {VERSION} · 이미지를 PDF로 엮기')
        icon = BASE / 'assets' / 'app.ico'
        if icon.exists():
            root.iconbitmap(str(icon))
        root.geometry('940x620')
        root.minsize(760, 480)
        root.option_add('*Font', ('맑은 고딕', 10))
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='이미지를 PDF로 엮기', font=('맑은 고딕', 19, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='목록의 위에서 아래 순서로, 이미지 한 장당 PDF 한 페이지가 만들어집니다.').pack(anchor='w', pady=(5, 14))
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', pady=(0, 10))
        self.controls = []
        for label, command in [('이미지 추가', self.add_dialog), ('▲ 위로', lambda: self.move(-1)), ('▼ 아래로', lambda: self.move(1)), ('이름순 정렬', self.sort), ('순서 뒤집기', self.reverse), ('선택 제거', self.remove)]:
            button = ttk.Button(toolbar, text=label, command=command)
            button.pack(side='left', padx=(0, 6))
            self.controls.append(button)
        body = ttk.Panedwindow(frame, orient='horizontal')
        body.pack(fill='both', expand=True)
        left = ttk.Frame(body)
        right = ttk.Frame(body, padding=12)
        body.add(left, weight=3)
        body.add(right, weight=2)
        self.list = tk.Listbox(left, selectmode='extended', exportselection=False, activestyle='none', relief='flat', selectbackground='#2563eb')
        scroll = ttk.Scrollbar(left, orient='vertical', command=self.list.yview)
        self.list.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.list.pack(fill='both', expand=True)
        self.list.bind('<<ListboxSelect>>', self.preview)
        self.list.bind('<Alt-Up>', lambda e: self.move(-1))
        self.list.bind('<Alt-Down>', lambda e: self.move(1))
        self.list.bind('<Delete>', lambda e: self.remove())
        self.preview_label = ttk.Label(right, text='이미지를 선택하면\n미리보기가 표시됩니다.', anchor='center')
        self.preview_label.pack(fill='both', expand=True)
        self.detail = ttk.Label(right, wraplength=300)
        self.detail.pack(fill='x', pady=10)
        self.status = tk.StringVar(value='이미지를 추가하거나 탐색기 우클릭 메뉴로 보내세요.')
        ttk.Label(frame, textvariable=self.status).pack(anchor='w', pady=(12, 6))
        self.bar = ttk.Progressbar(frame, mode='determinate')
        self.bar.pack(fill='x', pady=(0, 10))
        self.save_button = ttk.Button(frame, text='PDF로 저장…', command=self.save)
        self.save_button.pack(anchor='e')
        self.poll()

    def add_dialog(self):
        from tkinter import filedialog
        self.add(filedialog.askopenfilenames(title='PDF로 엮을 이미지 선택', filetypes=[('이미지', ' '.join('*' + x for x in EXTENSIONS))]))

    def add(self, paths):
        known = {os.path.normcase(p) for p in self.paths}
        for path in sorted(paths, key=natural_key):
            p = str(Path(path).resolve())
            if Path(p).suffix.lower() in EXTENSIONS and Path(p).is_file() and os.path.normcase(p) not in known:
                self.paths.append(p)
                known.add(os.path.normcase(p))
        self.refresh()

    def refresh(self, selection=()):
        self.list.delete(0, 'end')
        for i, path in enumerate(self.paths):
            self.list.insert('end', f'{i + 1:03d}   {Path(path).name}')
        for i in selection:
            self.list.selection_set(i)
        if selection:
            self.list.see(selection[0])
        self.status.set(f'{len(self.paths)}개 이미지 · 위/아래 버튼 또는 Alt+↑/↓로 순서를 변경하세요.')
        self.preview()

    def move(self, direction):
        if self.busy:
            return
        selected = set(self.list.curselection())
        for i in sorted(selected, reverse=direction > 0):
            j = i + direction
            if 0 <= j < len(self.paths) and j not in selected:
                self.paths[i], self.paths[j] = self.paths[j], self.paths[i]
                selected.remove(i)
                selected.add(j)
        self.refresh(sorted(selected))

    def sort(self):
        self.paths.sort(key=natural_key)
        self.refresh()

    def reverse(self):
        self.paths.reverse()
        self.refresh()

    def remove(self):
        if not self.busy:
            for i in reversed(self.list.curselection()):
                del self.paths[i]
            self.refresh()

    def preview(self, event=None):
        from PIL import Image, ImageOps, ImageTk
        selection = self.list.curselection()
        if not selection:
            self.preview_label.configure(image='', text='이미지를 선택하면\n미리보기가 표시됩니다.')
            self.detail.configure(text='')
            self.photo = None
            return
        path = self.paths[selection[0]]
        try:
            with Image.open(path) as original:
                im = ImageOps.exif_transpose(original)
                size = im.size
                im.thumbnail((330, 350))
                self.photo = ImageTk.PhotoImage(im)
            self.preview_label.configure(image=self.photo, text='')
            self.detail.configure(text=f'{size[0]} × {size[1]} 픽셀\n{path}')
        except Exception as exc:
            self.preview_label.configure(image='', text='미리보기를 불러올 수 없습니다.')
            self.detail.configure(text=str(exc))

    def save(self):
        from tkinter import filedialog, messagebox
        if self.busy or not self.paths:
            if not self.paths:
                messagebox.showinfo('이미지 추가', '먼저 이미지를 추가해 주세요.')
            return
        target = filedialog.asksaveasfilename(title='PDF 저장', defaultextension='.pdf', initialfile='묶은 이미지.pdf', filetypes=[('PDF', '*.pdf')])
        if not target:
            return
        if os.path.normcase(str(Path(target).resolve())) in {os.path.normcase(p) for p in self.paths}:
            messagebox.showerror('저장 오류', '원본 이미지와 다른 파일 이름을 선택하세요.')
            return
        self.busy = True
        for button in self.controls + [self.save_button]:
            button.configure(state='disabled')
        self.bar.configure(maximum=len(self.paths), value=0)
        paths = self.paths.copy()
        def worker():
            try:
                export_pdf(paths, target, lambda n: self.events.put(('progress', n)))
                self.events.put(('done', target))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        from tkinter import messagebox
        if not self.busy:
            incoming = []
            for entry in INBOX.glob('*.json'):
                try:
                    incoming.extend(json.loads(entry.read_text(encoding='utf-8')))
                    entry.unlink()
                except (OSError, ValueError):
                    continue
            if incoming:
                self.add(incoming)
                self.root.deiconify()
                self.root.lift()
        while not self.events.empty():
            kind, value = self.events.get_nowait()
            if kind == 'progress':
                self.bar.configure(value=value)
                self.status.set(f'PDF 생성 중: {value} / {len(self.paths)}')
            else:
                self.busy = False
                for button in self.controls + [self.save_button]:
                    button.configure(state='normal')
                if kind == 'done':
                    self.status.set(f'저장 완료: {value}')
                    if messagebox.askyesno('저장 완료', f'PDF를 저장했습니다.\n{value}\n\n지금 열까요?'):
                        try:
                            os.startfile(value)
                        except OSError as exc:
                            messagebox.showerror('PDF 열기 실패', f'파일은 저장되었습니다.\n{exc}')
                else:
                    self.status.set('저장 실패 · 이미지 파일을 확인해 주세요.')
                    messagebox.showerror('PDF 저장 실패', value)
        self.root.after(250, self.poll)

    def close(self):
        from tkinter import messagebox
        if self.busy:
            messagebox.showinfo('저장 중', 'PDF 저장이 끝난 뒤 창을 닫아 주세요.')
        else:
            self.root.destroy()


def main():
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        import smoke_test
        smoke_test.run(Path(sys.argv[2]))
        return
    INBOX.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        token = uuid.uuid4().hex
        pending = INBOX / (token + '.tmp')
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
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        root = tk.Tk()
        App(root)
        root.mainloop()
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))


if __name__ == '__main__':
    main()
