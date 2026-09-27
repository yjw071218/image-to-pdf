import tempfile
from pathlib import Path
import tkinter as tk
from PIL import Image
from pypdf import PdfReader
import app

def test():
    previous_inbox = app.INBOX
    with tempfile.TemporaryDirectory() as directory:
        folder = Path(directory)
        paths = []
        for name, size, color in [('2.png', (300, 150), (255, 0, 0, 255)), ('10.png', (150, 300), (0, 0, 0, 0))]:
            path = folder / name
            Image.new('RGBA', size, color).save(path)
            paths.append(str(path))
        target = folder / 'output.pdf'
        app.export_pdf(paths, target)
        reader = PdfReader(target)
        assert len(reader.pages) == 2
        assert float(reader.pages[0].mediabox.width) == 144
        assert float(reader.pages[1].mediabox.height) == 144
        pixel = reader.pages[1].images[0].image.convert('RGB').getpixel((10, 10))
        assert min(pixel) >= 250, pixel
        original = target.read_bytes()
        corrupt = folder / 'broken.png'
        corrupt.write_bytes(b'broken')
        try:
            app.export_pdf([str(corrupt)], target)
            raise AssertionError('Expected failure')
        except RuntimeError:
            pass
        assert target.read_bytes() == original
        exif = Image.Exif()
        exif[274] = 6
        rotated = folder / 'rotated.jpg'
        Image.new('RGB', (300, 150), 'blue').save(rotated, exif=exif)
        app.export_pdf([str(rotated)], folder / 'rotated.pdf')
        page = PdfReader(folder / 'rotated.pdf').pages[0]
        assert float(page.mediabox.height) > float(page.mediabox.width)
        root = tk.Tk()
        root.withdraw()
        app.INBOX = folder / 'inbox'
        app.INBOX.mkdir()
        ui = app.App(root)
        ui.add(paths[::-1] + paths)
        assert ui.paths == paths
        ui.list.selection_set(0)
        ui.move(1)
        assert ui.paths == paths[::-1]
        ui.reverse()
        assert ui.paths == paths
        ui.list.selection_set(0)
        ui.preview()
        assert ui.photo is not None
        root.update()
        root.destroy()
    app.INBOX = previous_inbox
    print('PASS: page order, transparency, EXIF rotation, atomic save, UI ordering, preview, duplicate removal')

if __name__ == '__main__':
    test()
