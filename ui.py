"""Tk page editor shared by the source and packaged application."""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from pdf_engine import (Cancelled, EXTENSIONS, Options, PAPERS, PageItem,
                        PasswordRequired, export_pdf, load_pages, natural_key,
                        parse_pages, render_preview)


class App:
    def __init__(self, root, inbox=None, data_dir=None):
        self.root = root
        self.inbox = inbox
        self.data_dir = data_dir
        self.items = []
        self.source_paths = set()
        self.undo_stack = []
        self.redo_stack = []
        self.busy = False
        self.dirty = False
        self.events = queue.Queue()
        self.cancel_event = threading.Event()
        self.preview_job = None
        self.poll_job = None
        self.photo = None
        self.closed = False
        self.controls = []
        root.title('ImageToPDF 2.0.0 · PDF 병합 / 페이지 편집')
        icon = Path(__file__).resolve().parent / 'assets' / 'app.ico'
        if icon.exists():
            root.iconbitmap(str(icon))
        root.geometry('1180x820')
        root.minsize(980, 740)
        root.option_add('*Font', ('맑은 고딕', 10))
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='PDF와 이미지를 한 권으로', font=('맑은 고딕', 19, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='PDF를 추가하면 페이지별로 펼쳐집니다. 순서를 정하고 필요 없는 페이지를 삭제한 뒤 새 PDF로 저장하세요.').pack(anchor='w', pady=(4, 12))
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill='x', pady=(0, 6))
        for label, command in [('PDF · 이미지 추가', self.add_dialog), ('▲ 위로', lambda: self.move(-1)), ('▼ 아래로', lambda: self.move(1)), ('이름순', self.sort), ('순서 뒤집기', self.reverse), ('선택 삭제', self.remove), ('실행 취소', self.undo), ('다시 실행', self.redo)]:
            self.button(toolbar, label, command)
        second = ttk.Frame(frame)
        second.pack(fill='x', pady=(0, 8))
        for label, command in [('↶ 90°', lambda: self.rotate(-90)), ('↷ 90°', lambda: self.rotate(90)), ('선택 복제', self.duplicate), ('빈 페이지 추가', self.blank), ('전체 선택', self.select_all), ('홀수 선택', lambda: self.select_parity(0)), ('짝수 선택', lambda: self.select_parity(1))]:
            self.button(second, label, command)
        ranges = ttk.Frame(frame)
        ranges.pack(fill='x', pady=(0, 10))
        ttk.Label(ranges, text='현재 목록 페이지 번호').pack(side='left', padx=(0, 8))
        self.range_var = tk.StringVar()
        entry = ttk.Entry(ranges, textvariable=self.range_var, width=24)
        entry.pack(side='left', padx=(0, 8))
        self.controls.append((entry, 'normal'))
        self.button(ranges, '번호로 선택', self.select_range)
        self.button(ranges, '번호로 삭제', self.delete_range)
        ttk.Label(ranges, text='예: 1, 3-5, 8   ·   Ctrl/Shift로 여러 페이지 선택').pack(side='left', padx=8)
        body = ttk.Panedwindow(frame, orient='horizontal')
        body.pack(fill='both', expand=True)
        left, right = ttk.Frame(body), ttk.Frame(body, padding=(12, 0, 0, 0))
        body.add(left, weight=3)
        body.add(right, weight=2)
        self.list = tk.Listbox(left, selectmode='extended', exportselection=False, activestyle='none', relief='solid', borderwidth=1, selectbackground='#2563eb')
        vertical = ttk.Scrollbar(left, orient='vertical', command=self.list.yview)
        horizontal = ttk.Scrollbar(left, orient='horizontal', command=self.list.xview)
        self.list.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side='right', fill='y')
        horizontal.pack(side='bottom', fill='x')
        self.list.pack(fill='both', expand=True)
        self.list.bind('<<ListboxSelect>>', self.schedule_preview)
        self.list.bind('<Alt-Up>', lambda e: self.move(-1))
        self.list.bind('<Alt-Down>', lambda e: self.move(1))
        self.list.bind('<Delete>', lambda e: self.remove())
        self.list.bind('<Control-a>', self.select_all)
        self.list.bind('<Control-z>', lambda e: self.undo())
        self.list.bind('<Control-y>', lambda e: self.redo())
        ttk.Label(right, text='출력 미리보기 · PDF는 원래 용지 크기 유지').pack(anchor='w', pady=(0, 5))
        self.preview_label = tk.Label(right, text='페이지를 선택하면\n미리보기가 표시됩니다.', background='#e5e9ef', anchor='center')
        self.preview_label.pack(fill='both', expand=True)
        self.detail = ttk.Label(right, wraplength=410)
        self.detail.pack(fill='x', pady=(6, 0))
        settings = ttk.LabelFrame(frame, text='이미지 / 빈 페이지 용지 설정 · 비율 유지 + 흰 여백 (잘림 없음)', padding=10)
        settings.pack(fill='x', pady=(12, 6))
        self.paper = tk.StringVar(value='A4')
        self.orientation = tk.StringVar(value='세로')
        self.margin = tk.StringVar(value='0')
        self.custom_width = tk.StringVar(value='210')
        self.custom_height = tk.StringVar(value='297')
        self.dpi = tk.StringVar(value='200')
        self.quality = tk.StringVar(value='90')
        self.setting_vars = (self.paper, self.orientation, self.margin, self.custom_width, self.custom_height, self.dpi, self.quality)
        first_settings = ttk.Frame(settings)
        first_settings.pack(fill='x')
        for label, variable, values, width in [('용지', self.paper, list(PAPERS), 14), ('방향', self.orientation, ['세로', '가로', '자동'], 7), ('여백(mm)', self.margin, None, 6), ('사용자 지정(mm)', self.custom_width, None, 6), ('×', self.custom_height, None, 6)]:
            self.field(first_settings, label, variable, values, width)
        second_settings = ttk.Frame(settings)
        second_settings.pack(fill='x', pady=(8, 0))
        self.field(second_settings, '이미지 최대 해상도(DPI)', self.dpi, ['100', '150', '200', '300'], 7)
        self.field(second_settings, 'JPEG 품질(40~100)', self.quality, ['60', '75', '90', '95', '100'], 7)
        ttk.Label(second_settings, text='PDF 텍스트·벡터는 원본 유지 · 원본 크기 모드에서는 여백 미적용').pack(side='left', padx=10)
        self.load_settings()
        for variable in self.setting_vars:
            variable.trace_add('write', self.schedule_preview)
        self.status = tk.StringVar(value='PDF 또는 이미지를 추가하세요. 원본 파일은 변경하지 않습니다.')
        ttk.Label(frame, textvariable=self.status).pack(anchor='w', pady=(6, 4))
        footer = ttk.Frame(frame)
        footer.pack(fill='x')
        self.bar = ttk.Progressbar(footer, mode='determinate')
        self.bar.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.cancel_button = ttk.Button(footer, text='작업 취소', command=self.cancel, state='disabled')
        self.cancel_button.pack(side='left', padx=(0, 8))
        self.button(footer, '선택 페이지만 저장…', lambda: self.save(selected_only=True))
        self.button(footer, '전체 PDF로 저장…', self.save)
        self.poll()

    @property
    def paths(self):
        return list(dict.fromkeys(item.path for item in self.items if item.path))

    def button(self, parent, label, command):
        button = ttk.Button(parent, text=label, command=command)
        button.pack(side='left', padx=(0, 5))
        self.controls.append((button, 'normal'))
        return button

    def field(self, parent, label, variable, values, width):
        ttk.Label(parent, text=label).pack(side='left', padx=(0, 5))
        state = 'readonly' if values else 'normal'
        widget = ttk.Combobox(parent, textvariable=variable, values=values, width=width, state=state) if values else ttk.Entry(parent, textvariable=variable, width=width)
        widget.pack(side='left', padx=(0, 12))
        self.controls.append((widget, state))

    def options(self):
        try:
            value = Options(self.paper.get(), self.orientation.get(), float(self.margin.get()), float(self.custom_width.get()), float(self.custom_height.get()), int(self.dpi.get()), int(self.quality.get()))
            value.validate()
            return value
        except (ValueError, OverflowError) as exc:
            raise ValueError(f'용지 설정을 확인하세요.\n{exc}') from exc

    def load_settings(self):
        if not self.data_dir:
            return
        try:
            value = Options(**json.loads((self.data_dir / 'settings.json').read_text(encoding='utf-8')))
            value.validate()
            for variable, content in zip(self.setting_vars, asdict(value).values()):
                variable.set(str(content))
        except (OSError, ValueError, TypeError):
            pass

    def save_settings(self):
        if self.data_dir:
            try:
                value = self.options()
                self.data_dir.mkdir(parents=True, exist_ok=True)
                temp = self.data_dir / 'settings.tmp'
                temp.write_text(json.dumps(asdict(value), ensure_ascii=False), encoding='utf-8')
                temp.replace(self.data_dir / 'settings.json')
            except (OSError, ValueError):
                pass

    def set_busy(self, value, total=1):
        self.busy = value
        for widget, state in self.controls:
            widget.configure(state='disabled' if value else state)
        self.cancel_button.configure(state='normal' if value else 'disabled')
        if value:
            self.cancel_event.clear()
            self.work_total = total
            self.bar.configure(maximum=total, value=0)

    def checkpoint(self):
        self.undo_stack.append(self.items.copy())
        self.undo_stack = self.undo_stack[-50:]
        self.redo_stack.clear()
        self.dirty = True

    def refresh(self, selection=()):
        self.list.delete(0, 'end')
        for i, item in enumerate(self.items):
            kind = {'pdf': 'PDF', 'image': '이미지', 'blank': '빈쪽'}[item.kind]
            angle = f' · {item.rotation}°' if item.rotation else ''
            self.list.insert('end', f'{i + 1:04d}   [{kind}] {item.label}{angle}')
        for i in selection:
            if 0 <= i < len(self.items):
                self.list.selection_set(i)
        if selection:
            self.list.see(selection[0])
        self.status.set(f'총 {len(self.items)}페이지 · 목록 맨 위가 첫 페이지입니다. Alt+↑/↓ 순서 변경 · Delete 삭제')
        self.schedule_preview()

    def add_dialog(self):
        self.add(filedialog.askopenfilenames(title='PDF 또는 이미지 추가', filetypes=[('PDF 및 이미지', ' '.join('*' + x for x in EXTENSIONS)), ('PDF', '*.pdf'), ('모든 파일', '*.*')]))

    def add(self, paths):
        if self.busy:
            return
        known = {os.path.normcase(path) for path in self.paths}
        pending = []
        for path in sorted(paths, key=natural_key):
            normalized = str(Path(path).resolve())
            if os.path.normcase(normalized) not in known:
                pending.append(normalized)
                known.add(os.path.normcase(normalized))
        if not pending:
            return
        self.set_busy(True, len(pending))
        self.status.set('파일과 페이지 정보를 불러오는 중…')

        def worker():
            items, errors = [], []
            for i, path in enumerate(pending):
                if self.cancel_event.is_set():
                    break
                password = ''
                while True:
                    try:
                        items.extend(load_pages(path, password))
                        break
                    except PasswordRequired:
                        request = {'path': path, 'event': threading.Event(), 'password': None}
                        self.events.put(('password', request))
                        while not request['event'].wait(.1):
                            if self.cancel_event.is_set():
                                break
                        if self.cancel_event.is_set() or request['password'] is None:
                            errors.append(f'{Path(path).name}: 암호 입력을 취소했습니다.')
                            break
                        password = request['password']
                    except Exception as exc:
                        errors.append(f'{Path(path).name}: {exc}')
                        break
                self.events.put(('progress', (i + 1, '파일 불러오기')))
            self.events.put(('loaded', (items, errors)))
        threading.Thread(target=worker, daemon=True).start()

    def move(self, direction):
        if self.busy:
            return 'break'
        selected = set(self.list.curselection())
        if not selected:
            return 'break'
        self.checkpoint()
        for i in sorted(selected, reverse=direction > 0):
            j = i + direction
            if 0 <= j < len(self.items) and j not in selected:
                self.items[i], self.items[j] = self.items[j], self.items[i]
                selected.remove(i)
                selected.add(j)
        self.refresh(sorted(selected))
        return 'break'

    def sort(self):
        if not self.busy and self.items:
            self.checkpoint()
            self.items.sort(key=lambda item: (natural_key(item.path), item.index))
            self.refresh()

    def reverse(self):
        if not self.busy and self.items:
            self.checkpoint()
            self.items.reverse()
            self.refresh()

    def remove(self, indices=None):
        if self.busy:
            return
        selected = list(self.list.curselection()) if indices is None else list(indices)
        if selected:
            self.checkpoint()
            for i in sorted(set(selected), reverse=True):
                del self.items[i]
            self.refresh([min(min(selected), len(self.items) - 1)] if self.items else [])

    def rotate(self, angle):
        selected = self.list.curselection()
        if not self.busy and selected:
            self.checkpoint()
            for i in selected:
                self.items[i] = replace(self.items[i], rotation=(self.items[i].rotation + angle) % 360)
            self.refresh(selected)

    def duplicate(self):
        selected = self.list.curselection()
        if not self.busy and selected:
            self.checkpoint()
            insert_at = selected[-1] + 1
            self.items[insert_at:insert_at] = [self.items[i] for i in selected]
            self.refresh(list(range(insert_at, insert_at + len(selected))))

    def blank(self):
        if not self.busy:
            self.checkpoint()
            selected = self.list.curselection()
            position = selected[-1] + 1 if selected else len(self.items)
            self.items.insert(position, PageItem(kind='blank'))
            self.refresh([position])

    def undo(self):
        if not self.busy and self.undo_stack:
            self.redo_stack.append(self.items.copy())
            self.items = self.undo_stack.pop()
            self.dirty = True
            self.refresh()
        return 'break'

    def redo(self):
        if not self.busy and self.redo_stack:
            self.undo_stack.append(self.items.copy())
            self.items = self.redo_stack.pop()
            self.dirty = True
            self.refresh()
        return 'break'

    def select_all(self, event=None):
        self.list.selection_set(0, 'end')
        self.schedule_preview()
        return 'break'

    def select_parity(self, parity):
        self.list.selection_clear(0, 'end')
        for i in range(parity, len(self.items), 2):
            self.list.selection_set(i)
        self.schedule_preview()

    def select_range(self):
        if self.busy:
            return
        try:
            indices = parse_pages(self.range_var.get(), len(self.items))
            self.list.selection_clear(0, 'end')
            for i in indices:
                self.list.selection_set(i)
            self.list.see(indices[0])
            self.schedule_preview()
        except ValueError as exc:
            messagebox.showerror('페이지 번호 확인', str(exc), parent=self.root)

    def delete_range(self):
        if not self.busy:
            try:
                self.remove(parse_pages(self.range_var.get(), len(self.items)))
            except ValueError as exc:
                messagebox.showerror('페이지 번호 확인', str(exc), parent=self.root)

    def schedule_preview(self, *args):
        if self.closed:
            return
        if len(args) == 3 and args[2] == 'write' and self.items:
            self.dirty = True
        if self.preview_job:
            self.root.after_cancel(self.preview_job)
        self.preview_job = self.root.after(180, self.preview)

    def preview(self, event=None):
        if self.preview_job:
            self.root.after_cancel(self.preview_job)
        self.preview_job = None
        selected = self.list.curselection()
        if not selected:
            self.photo = None
            self.preview_label.configure(image='', text='페이지를 선택하면\n미리보기가 표시됩니다.')
            self.detail.configure(text='')
            return
        from PIL import ImageTk
        item = self.items[selected[0]]
        try:
            # Existing PDF pages do not depend on image paper settings.
            settings = Options() if item.kind == 'pdf' else self.options()
            size = (max(150, min(460, self.preview_label.winfo_width() - 18)), max(120, min(440, self.preview_label.winfo_height() - 18)))
            with render_preview(item, settings, size) as image:
                self.photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=self.photo, text='')
            self.detail.configure(text=f'출력 {selected[0] + 1}쪽 · {len(selected)}페이지 선택\n{item.label}')
        except Exception as exc:
            self.preview_label.configure(image='', text='미리보기를 불러올 수 없습니다.')
            self.detail.configure(text=str(exc))

    def save(self, selected_only=False):
        if self.busy:
            return
        selected = list(self.list.curselection()) if selected_only else list(range(len(self.items)))
        if not selected:
            messagebox.showinfo('페이지 선택', '저장할 페이지를 추가하거나 선택해 주세요.', parent=self.root)
            return
        try:
            options = self.options()
        except ValueError as exc:
            messagebox.showerror('설정 확인', str(exc), parent=self.root)
            return
        target = filedialog.asksaveasfilename(parent=self.root, title='선택 페이지 추출' if selected_only else 'PDF로 저장', defaultextension='.pdf', initialfile='추출한 페이지.pdf' if selected_only else '묶은 문서.pdf', filetypes=[('PDF', '*.pdf')])
        if not target:
            return
        normalized = os.path.normcase(str(Path(target).resolve()))
        if any(normalized == os.path.normcase(p) or (Path(target).exists() and Path(p).exists() and os.path.samefile(target, p)) for p in self.source_paths):
            messagebox.showerror('원본 보호', '원본과 다른 파일 이름으로 저장해 주세요.', parent=self.root)
            return
        items = [self.items[i] for i in selected]
        self.save_settings()
        self.set_busy(True, len(items))
        self.status.set('PDF를 만드는 중…')
        def worker():
            try:
                export_pdf(items, target, options, lambda n: self.events.put(('progress', (n, 'PDF 저장'))), self.cancel_event)
                self.events.put(('done', (target, selected_only)))
            except Cancelled:
                self.events.put(('cancelled', None))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def cancel(self):
        self.cancel_event.set()
        self.status.set('현재 페이지 처리가 끝나면 취소합니다…')

    def poll(self):
        if not self.busy and self.inbox:
            incoming = []
            received = False
            for entry in self.inbox.glob('*.json'):
                try:
                    value = json.loads(entry.read_text(encoding='utf-8'))
                    if isinstance(value, list) and all(isinstance(p, str) for p in value):
                        incoming.extend(value)
                        received = True
                    entry.unlink()
                except (OSError, ValueError):
                    continue
            if received:
                if incoming:
                    self.add(incoming)
                self.root.deiconify()
                self.root.lift()
        while not self.events.empty():
            kind, value = self.events.get_nowait()
            if kind == 'password':
                if not self.cancel_event.is_set():
                    value['password'] = simpledialog.askstring('PDF 열기 암호', f'{Path(value["path"]).name}\nPDF 암호를 입력하세요. (메모리에만 보관)', show='*', parent=self.root)
                value['event'].set()
            elif kind == 'progress':
                self.bar.configure(value=value[0])
                self.status.set(f'{value[1]}: {value[0]} / {self.work_total}')
            else:
                self.set_busy(False)
                if kind == 'loaded':
                    items, errors = value
                    if items:
                        self.checkpoint()
                        start = len(self.items)
                        self.items.extend(items)
                        self.source_paths.update(item.path for item in items if item.path)
                        self.refresh([start])
                    else:
                        self.status.set('추가된 페이지가 없습니다.')
                    if errors:
                        messagebox.showwarning('추가하지 못한 파일', '\n\n'.join(errors[:12]), parent=self.root)
                elif kind == 'done':
                    target, selected_only = value
                    if not selected_only:
                        self.dirty = False
                    self.status.set(f'저장 완료: {target}')
                    if messagebox.askyesno('저장 완료', f'PDF를 저장했습니다.\n{target}\n\n지금 열까요?', parent=self.root):
                        try:
                            os.startfile(target)
                        except OSError as exc:
                            messagebox.showerror('PDF 열기 실패', str(exc), parent=self.root)
                elif kind == 'cancelled':
                    self.status.set('작업을 취소했습니다. 기존 출력 파일은 유지됩니다.')
                elif kind == 'error':
                    self.status.set('PDF 저장에 실패했습니다.')
                    messagebox.showerror('저장 실패', value, parent=self.root)
        self.poll_job = self.root.after(150, self.poll)

    def dispose(self):
        self.closed = True
        for job in (self.preview_job, self.poll_job):
            if job:
                self.root.after_cancel(job)
        self.root.destroy()

    def close(self):
        if self.busy:
            messagebox.showinfo('작업 중', '작업 취소를 누르거나 처리가 끝난 뒤 창을 닫아 주세요.', parent=self.root)
            return
        if self.dirty and not messagebox.askyesno('편집 내용 닫기', '아직 저장하지 않은 편집 내용이 있습니다. 창을 닫을까요?', parent=self.root):
            return
        self.save_settings()
        self.dispose()
