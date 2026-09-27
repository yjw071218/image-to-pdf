"""Functional checks for image layout, PDF editing, and the page editor."""
from dataclasses import replace
from pathlib import Path
import tempfile
import threading
import time
import tkinter as tk
from unittest.mock import patch

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from pdf_engine import (Cancelled, MM, Options, PAPERS, PageItem, PasswordRequired,
                        export_pdf, load_pages, parse_pages, render_preview)
from ui import App


def make_pdf(path, labels, width=300, height=400, password=None):
    writer = PdfWriter()
    for label in labels:
        page = writer.add_blank_page(width, height)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
        content = DecodedStreamObject()
        content.set_data(f'BT /F1 18 Tf 20 30 Td ({label}) Tj ET'.encode('ascii'))
        page[NameObject('/Contents')] = content
    if password:
        writer.encrypt(password, algorithm='AES-256')
    writer.write(path)
    writer.close()


def wait_ui(ui):
    deadline = time.monotonic() + 20
    while ui.busy and time.monotonic() < deadline:
        ui.root.update()
        time.sleep(.02)
    assert not ui.busy, 'UI worker timed out'


def raises(exception, function):
    try:
        function()
    except exception:
        return
    raise AssertionError(f'Expected {exception.__name__}')


def test():
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        wide, tall, transparent = folder / '2.png', folder / '10.png', folder / 'transparent.png'
        Image.new('RGB', (600, 200), 'red').save(wide)
        Image.new('RGB', (200, 600), 'blue').save(tall)
        Image.new('RGBA', (100, 100), (0, 0, 0, 0)).save(transparent)
        items = load_pages(wide) + load_pages(tall) + load_pages(transparent)
        target = folder / 'images.pdf'
        export_pdf(items, target)
        reader = PdfReader(target)
        assert len(reader.pages) == 3
        for page in reader.pages:
            assert abs(float(page.mediabox.width) - 210 * MM) < .01
            assert abs(float(page.mediabox.height) - 297 * MM) < .01
        reader.close()
        # Render the actual output PDF to verify padding on the correct axis.
        with render_preview(PageItem(str(target), 0, 'pdf'), Options(), (420, 594)) as image:
            assert min(image.getpixel((210, 30))) > 245, 'Wide image needs top whitespace'
            r, g, b = image.getpixel((210, 297))
            assert r > 240 and g < 20 and b < 20
        with render_preview(PageItem(str(target), 1, 'pdf'), Options(), (420, 594)) as image:
            assert min(image.getpixel((10, 297))) > 245, 'Tall image needs side whitespace'
            r, g, b = image.getpixel((210, 297))
            assert b > 240 and r < 20 and g < 20
        with render_preview(PageItem(str(target), 2, 'pdf'), Options()) as image:
            assert min(image.getpixel((image.width // 2, image.height // 2))) > 245
        for paper, size in PAPERS.items():
            if not size:
                continue
            output = folder / 'size.pdf'
            export_pdf(items[:1], output, Options(paper=paper, orientation='가로', margin_mm=10))
            with PdfReader(output) as result:
                page = result.pages[0]
                assert abs(float(page.mediabox.width) - max(size) * MM) < .01
                assert abs(float(page.mediabox.height) - min(size) * MM) < .01
        custom = Options(paper='사용자 지정', custom_width_mm=100, custom_height_mm=150, margin_mm=10)
        export_pdf(items[:1], folder / 'custom.pdf', custom)
        with PdfReader(folder / 'custom.pdf') as result:
            assert abs(float(result.pages[0].mediabox.width) - 100 * MM) < .01
        with render_preview(PageItem(str(folder / 'custom.pdf'), 0, 'pdf'), Options(), (200, 300)) as image:
            assert min(image.getpixel((5, 150))) > 245
        export_pdf(items[:2], folder / 'auto.pdf', Options(orientation='자동'))
        with PdfReader(folder / 'auto.pdf') as result:
            assert result.pages[0].mediabox.width > result.pages[0].mediabox.height
            assert result.pages[1].mediabox.width < result.pages[1].mediabox.height
        exif = Image.Exif()
        exif[274] = 6
        rotated = folder / 'rotated.jpg'
        Image.new('RGB', (300, 150), 'blue').save(rotated, exif=exif)
        export_pdf(load_pages(rotated), folder / 'exif.pdf', Options(paper='원본 크기'))
        with PdfReader(folder / 'exif.pdf') as result:
            assert result.pages[0].mediabox.height > result.pages[0].mediabox.width
        frames = [Image.new('RGB', (20, 30), color) for color in ('red', 'green')]
        frames[0].save(folder / 'multi.tiff', save_all=True, append_images=frames[1:])
        assert len(load_pages(folder / 'multi.tiff')) == 2
        export_pdf(load_pages(folder / 'multi.tiff'), folder / 'tiff.pdf')
        with PdfReader(folder / 'tiff.pdf') as result:
            assert len(result.pages) == 2
        print('PASS: A4 padding (both axes), all paper sizes, margins, custom/auto orientation, transparency, EXIF, multipage TIFF')

        first, second = folder / 'first.pdf', folder / 'second.pdf'
        make_pdf(first, ['A1', 'A2', 'A3'])
        make_pdf(second, ['B1', 'B2'], width=500, height=250)
        pages_a, pages_b = load_pages(first), load_pages(second)
        edited = [pages_a[2], pages_b[0], replace(pages_a[0], rotation=90), pages_a[0], items[0], PageItem(kind='blank')]
        export_pdf(edited, folder / 'merged.pdf')
        with PdfReader(folder / 'merged.pdf') as result:
            assert len(result.pages) == 6
            assert [result.pages[i].extract_text().strip() for i in range(4)] == ['A3', 'B1', 'A1', 'A1']
            assert result.pages[2].rotation == 90 and result.pages[3].rotation == 0
            assert float(result.pages[1].mediabox.width) == 500
            assert 'A2' not in ''.join(page.extract_text() for page in result.pages)
        export_pdf([pages_a[1]], folder / 'extracted.pdf')
        with PdfReader(folder / 'extracted.pdf') as result:
            assert len(result.pages) == 1 and result.pages[0].extract_text().strip() == 'A2'
        secret = folder / 'locked.pdf'
        make_pdf(secret, ['Secret'], password='test-password')
        raises(PasswordRequired, lambda: load_pages(secret))
        unlocked = load_pages(secret, 'test-password')
        export_pdf(unlocked, folder / 'unlocked.pdf')
        with PdfReader(folder / 'unlocked.pdf') as result:
            assert not result.is_encrypted and 'Secret' in result.pages[0].extract_text()
        with render_preview(unlocked[0], Options()) as image:
            assert image.width > 0
        print('PASS: mixed PDF/image merge, selected page deletion/extraction, duplicate rotation isolation, text preservation, AES password input')

        old_bytes = target.read_bytes()
        corrupt = folder / 'broken.png'
        corrupt.write_bytes(b'broken')
        raises(RuntimeError, lambda: export_pdf([items[0], PageItem(str(corrupt))], target))
        assert target.read_bytes() == old_bytes
        cancel = threading.Event()
        raises(Cancelled, lambda: export_pdf(items, target, progress=lambda n: cancel.set(), cancel=cancel))
        assert target.read_bytes() == old_bytes
        raises(ValueError, lambda: export_pdf(pages_a, first))
        raises(ValueError, lambda: export_pdf([], target))
        raises(ValueError, lambda: Options(margin_mm=200).validate())
        raises(ValueError, lambda: Options(margin_mm=float('nan')).validate())
        assert parse_pages('1, 3-5, 5, 2', 5) == [0, 2, 3, 4, 1]
        assert parse_pages('3-1', 5) == [2, 1, 0]
        for invalid in ('0', '6', '1,,2', 'a', '-1', ''):
            raises(ValueError, lambda: parse_pages(invalid, 5))
        print('PASS: atomic output, cancellation, original-file protection, invalid ranges and settings')

        root = tk.Tk()
        root.withdraw()
        ui = App(root)
        try:
            with patch('ui.messagebox.showwarning', side_effect=AssertionError('Unexpected import warning')):
                ui.add([str(tall), str(wide), str(wide), str(first)])
                wait_ui(ui)
            assert len(ui.items) == 5 and ui.items[0].path == str(wide)
            ui.list.selection_clear(0, 'end')
            ui.list.selection_set(0)
            ui.move(1)
            assert ui.items[1].path == str(wide)
            ui.undo()
            assert ui.items[0].path == str(wide)
            ui.redo()
            assert ui.items[1].path == str(wide)
            ui.range_var.set('3-4')
            ui.delete_range()
            assert len(ui.items) == 3 and ui.items[-1].index == 2
            ui.undo()
            assert len(ui.items) == 5
            ui.list.selection_set(2)
            ui.rotate(90)
            assert ui.items[2].rotation == 90
            ui.duplicate()
            assert len(ui.items) == 6
            ui.blank()
            assert len(ui.items) == 7
            ui.select_parity(0)
            assert ui.list.curselection() == (0, 2, 4, 6)
            ui.list.selection_clear(0, 'end')
            ui.list.selection_set(2)
            ui.preview()
            assert ui.photo is not None
            ui.list.selection_clear(0, 'end')
            ui.list.selection_set(0)
            extracted = folder / 'ui-extracted.pdf'
            with patch('ui.filedialog.asksaveasfilename', return_value=str(extracted)), patch('ui.messagebox.askyesno', return_value=False), patch('ui.messagebox.showerror', side_effect=AssertionError('Unexpected save error')):
                ui.save(selected_only=True)
                wait_ui(ui)
            with PdfReader(extracted) as result:
                assert len(result.pages) == 1
            count = len(ui.items)
            with patch('ui.simpledialog.askstring', side_effect=['wrong', 'test-password']), patch('ui.messagebox.showwarning', side_effect=AssertionError('Unexpected encrypted import warning')):
                ui.add([str(secret)])
                wait_ui(ui)
            assert len(ui.items) == count + 1 and ui.items[-1].password == 'test-password'
        finally:
            ui.dispose()
        print('PASS: UI import, reorder, delete ranges, undo/redo, rotation, duplication, blank insert, preview, selected-page export')


if __name__ == '__main__':
    test()
