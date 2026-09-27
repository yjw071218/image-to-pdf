"""Page-oriented PDF composition. All edits are written to a separate file."""
from dataclasses import dataclass, field
from pathlib import Path
import io
import math
import os
import re
import tempfile

from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter, Transformation

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.webp')
EXTENSIONS = IMAGE_EXTENSIONS + ('.pdf',)
MM = 72 / 25.4
PAPERS = {'A4': (210, 297), 'A3': (297, 420), 'A5': (148, 210),
          'B4 (ISO)': (250, 353), 'B5 (ISO)': (176, 250),
          'Letter': (215.9, 279.4), 'Legal': (215.9, 355.6),
          '사용자 지정': None, '원본 크기': None}


class PasswordRequired(ValueError):
    pass


class Cancelled(Exception):
    pass


@dataclass(frozen=True)
class PageItem:
    path: str = ''
    index: int = 0
    kind: str = 'image'
    rotation: int = 0
    password: str = field(default='', repr=False)

    @property
    def label(self):
        if self.kind == 'blank':
            return '빈 페이지'
        suffix = f' · 원본 {self.index + 1}쪽' if self.kind == 'pdf' or self.index else ''
        return Path(self.path).name + suffix


@dataclass(frozen=True)
class Options:
    paper: str = 'A4'
    orientation: str = '세로'
    margin_mm: float = 0
    custom_width_mm: float = 210
    custom_height_mm: float = 297
    dpi: int = 200
    quality: int = 90

    def validate(self):
        if self.paper not in PAPERS:
            raise ValueError('용지 종류를 확인하세요.')
        if self.orientation not in ('세로', '가로', '자동'):
            raise ValueError('용지 방향을 확인하세요.')
        values = (self.margin_mm, self.custom_width_mm, self.custom_height_mm)
        if not all(math.isfinite(v) for v in values):
            raise ValueError('용지 크기와 여백에는 유한한 숫자를 입력하세요.')
        if self.margin_mm < 0:
            raise ValueError('여백은 0mm 이상이어야 합니다.')
        if not 10 <= self.custom_width_mm <= 2000 or not 10 <= self.custom_height_mm <= 2000:
            raise ValueError('사용자 지정 용지는 가로/세로 각각 10~2000mm입니다.')
        if self.dpi not in (100, 150, 200, 300) or not 40 <= self.quality <= 100:
            raise ValueError('해상도 또는 이미지 품질을 확인하세요.')
        if self.paper != '원본 크기':
            width, height = self.page_size((100, 100))
            if min(width, height) <= 2 * self.margin_mm * MM:
                raise ValueError('여백이 용지보다 큽니다. 여백을 줄여 주세요.')

    def page_size(self, original):
        if self.paper == '원본 크기':
            return original
        size = PAPERS[self.paper] or (self.custom_width_mm, self.custom_height_mm)
        width, height = size[0] * MM, size[1] * MM
        if self.orientation == '가로' or (self.orientation == '자동' and original[0] > original[1]):
            width, height = max(width, height), min(width, height)
        elif self.orientation in ('세로', '자동'):
            width, height = min(width, height), max(width, height)
        return width, height


def natural_key(path):
    return [(1, int(s)) if s.isdigit() else (0, s.casefold()) for s in re.split(r'(\d+)', Path(path).name)]


def read_pdf(path, password=''):
    reader = PdfReader(path)
    try:
        if reader.is_encrypted and not reader.decrypt(password):
            raise PasswordRequired(f'{Path(path).name}: PDF 열기 암호가 필요하거나 올바르지 않습니다.')
        return reader
    except Exception:
        reader.close()
        raise


def load_pages(path, password=''):
    path = str(Path(path).resolve())
    suffix = Path(path).suffix.lower()
    if suffix not in EXTENSIONS:
        raise ValueError('지원하지 않는 파일 형식입니다.')
    if suffix == '.pdf':
        reader = read_pdf(path, password)
        try:
            count = len(reader.pages)
            if not count:
                raise ValueError('페이지가 없는 PDF입니다.')
            return [PageItem(path, i, 'pdf', password=password) for i in range(count)]
        finally:
            reader.close()
    with Image.open(path) as image:
        count = getattr(image, 'n_frames', 1) if suffix in ('.tif', '.tiff') else 1
        return [PageItem(path, i) for i in range(count)]


def parse_pages(expression, count):
    """1-based inclusive ranges, in the order entered; reject invalid input."""
    if not expression.strip():
        raise ValueError('페이지 번호를 입력하세요. 예: 1, 3-5, 8')
    result = []
    seen = set()
    for part in expression.replace(' ', '').split(','):
        if not re.fullmatch(r'\d+(?:-\d+)?', part):
            raise ValueError('페이지 형식이 잘못되었습니다. 예: 1, 3-5, 8')
        ends = [int(x) for x in part.split('-')]
        start, end = ends[0], ends[-1]
        if not 1 <= start <= count or not 1 <= end <= count:
            raise ValueError(f'페이지 번호는 1~{count} 범위여야 합니다.')
        step = 1 if end >= start else -1
        for number in range(start, end + step, step):
            if number - 1 not in seen:
                result.append(number - 1)
                seen.add(number - 1)
    return result


def open_image(item):
    with Image.open(item.path) as source:
        source.seek(item.index)
        corrected = ImageOps.exif_transpose(source)
        rgba = corrected.convert('RGBA')
        image = Image.new('RGB', rgba.size, 'white')
        image.paste(rgba, mask=rgba.getchannel('A'))
        rgba.close()
    if item.rotation:
        rotated = image.rotate(-item.rotation, expand=True)
        image.close()
        image = rotated
    return image


def fit_rect(source_size, page_size, margin):
    width, height = page_size
    available = (width - 2 * margin, height - 2 * margin)
    if min(*source_size, *available) <= 0:
        raise ValueError('이미지 또는 여백을 제외한 용지 크기가 올바르지 않습니다.')
    scale = min(available[0] / source_size[0], available[1] / source_size[1])
    draw_width, draw_height = source_size[0] * scale, source_size[1] * scale
    return (width - draw_width) / 2, (height - draw_height) / 2, draw_width, draw_height


def render_preview(item, options, max_size=(430, 470)):
    """Called only on the GUI thread (PDFium is not thread-safe)."""
    if item.kind == 'pdf':
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(item.path, password=item.password or None) as document:
            page = document[item.index]
            try:
                width, height = page.get_size()
                if item.rotation % 180:
                    width, height = height, width
                bitmap = page.render(scale=min(max_size[0] / width, max_size[1] / height), rotation=item.rotation)
                try:
                    return bitmap.to_pil().convert('RGB').copy()
                finally:
                    bitmap.close()
            finally:
                page.close()
    options.validate()
    image = open_image(item) if item.kind == 'image' else None
    try:
        original = (image.width * 72 / options.dpi, image.height * 72 / options.dpi) if image else (210 * MM, 297 * MM)
        page_size = options.page_size(original)
        if item.kind == 'blank' and item.rotation % 180:
            page_size = page_size[::-1]
        ratio = min(max_size[0] / page_size[0], max_size[1] / page_size[1])
        canvas = Image.new('RGB', (max(1, round(page_size[0] * ratio)), max(1, round(page_size[1] * ratio))), 'white')
        if image:
            margin = 0 if options.paper == '원본 크기' else options.margin_mm * MM
            x, y, width, height = fit_rect(image.size, page_size, margin)
            resized = image.resize((max(1, round(width * ratio)), max(1, round(height * ratio))), Image.Resampling.LANCZOS)
            canvas.paste(resized, (round(x * ratio), round(y * ratio)))
            resized.close()
        return canvas
    finally:
        if image:
            image.close()


def export_pdf(items, destination, options=None, progress=lambda n: None, cancel=None):
    options = options or Options()
    options.validate()
    if not items:
        raise ValueError('저장할 페이지가 없습니다.')
    target = Path(destination).resolve()
    for item in items:
        if item.path and (os.path.normcase(str(target)) == os.path.normcase(str(Path(item.path).resolve()))
                          or (target.exists() and os.path.samefile(item.path, target))):
            raise ValueError('원본 파일을 덮어쓸 수 없습니다. 다른 파일 이름으로 저장하세요.')
    writer = PdfWriter()
    readers = {}
    temporary = None

    def check_cancel():
        if cancel and cancel.is_set():
            raise Cancelled()

    try:
        for index, item in enumerate(items):
            check_cancel()
            try:
                if item.kind == 'pdf':
                    key = (item.path, item.password)
                    if key not in readers:
                        reader = read_pdf(*key)
                        # Avoid form-field name collisions between source documents.
                        if reader.get_fields():
                            reader.add_form_topname(f'document{len(readers) + 1}')
                        readers[key] = reader
                    writer.append(readers[key], pages=[item.index], import_outline=False)
                    if item.rotation:
                        writer.pages[-1].rotate(item.rotation)
                elif item.kind == 'blank':
                    width, height = options.page_size((210 * MM, 297 * MM))
                    if item.rotation % 180:
                        width, height = height, width
                    writer.add_blank_page(width, height)
                else:
                    with open_image(item) as image:
                        original_size = (image.width * 72 / options.dpi, image.height * 72 / options.dpi)
                        page_size = options.page_size(original_size)
                        margin = 0 if options.paper == '원본 크기' else options.margin_mm * MM
                        x, y, width, height = fit_rect(image.size, page_size, margin)
                        image.thumbnail((max(1, round(width * options.dpi / 72)), max(1, round(height * options.dpi / 72))), Image.Resampling.LANCZOS)
                        stream = io.BytesIO()
                        image.save(stream, 'PDF', resolution=options.dpi, quality=options.quality)
                        stream.seek(0)
                        image_reader = PdfReader(stream)
                        try:
                            source = image_reader.pages[0]
                            page = writer.add_blank_page(*page_size)
                            transform = Transformation().scale(width / float(source.mediabox.width), height / float(source.mediabox.height)).translate(x, y)
                            page.merge_transformed_page(source, transform)
                        finally:
                            image_reader.close()
                progress(index + 1)
            except Cancelled:
                raise
            except Exception as exc:
                raise RuntimeError(f'{item.label}\n{exc}') from exc
        writer.add_metadata({'/Producer': 'ImageToPDF 2.0.0'})
        check_cancel()
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.pdf', delete=False) as output:
            temporary = output.name
            writer.write(output)
        check_cancel()
        os.replace(temporary, target)
        temporary = None
    finally:
        writer.close()
        for reader in readers.values():
            reader.close()
        if temporary:
            Path(temporary).unlink(missing_ok=True)
