"""Include the license texts for the bundled Python runtime and dependencies."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys

destination = Path('build/third-party-licenses')
destination.mkdir(parents=True, exist_ok=True)
for package in ('Pillow', 'pypdf', 'typing_extensions'):
    dist = distribution(package)
    for file in dist.files or []:
        if 'license' in str(file).lower() or 'copying' in str(file).lower():
            source = Path(dist.locate_file(file))
            if source.is_file():
                target = destination / package / str(file).replace('/', '_')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
runtime = Path(sys.base_prefix)
for source in [runtime / 'LICENSE.txt', *runtime.glob('tcl/**/license.terms')]:
    if source.is_file():
        shutil.copyfile(source, destination / ('Python_' + str(source.relative_to(runtime)).replace('\\', '_').replace('/', '_')))
print('Collected third-party license texts.')
