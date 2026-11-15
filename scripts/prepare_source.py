"""Prepare local paper text with the official MarkItDown CLI."""

from argparse import ArgumentParser
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, distributions, version
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


def digest(path):
    result = sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Local source file')
    parser.add_argument('-o', '--output', required=True, type=Path, help='Task-local Markdown file')
    parser.add_argument('--reuse', action='store_true', help='Record or verify a reusable conversion')
    args = parser.parse_args()

    try:
        source, output = args.input.resolve(), args.output.resolve()
        metadata = output.with_name(output.name + '.meta.json')
        if not source.is_file():
            raise ValueError('Input must be an existing local file.')
        if output.suffix.lower() != '.md' or source == output:
            raise ValueError('Use a separate .md path for output.')
        cached = args.reuse and output.is_file() and metadata.is_file()
        if not cached and (output.exists() or (args.reuse and metadata.exists())):
            raise ValueError('Output or cache record already exists. Use a new output path.')

        markitdown_version = version('markitdown')
        if args.reuse:
            key = {
                'schema': 1,
                'source': str(source),
                'source_sha256': digest(source),
                'executable': sys.executable,
                'python': sys.version,
                'markitdown': markitdown_version,
                'packages': sorted([d.metadata['Name'], d.version]
                                   for d in distributions() if d.metadata['Name']),
            }
        if cached:
            record = json.loads(metadata.read_text(encoding='utf-8'))
            markdown = output.read_bytes()
            if record != {'key': key, 'output_sha256': sha256(markdown).hexdigest()}:
                raise ValueError('Source, environment or output has changed. Use a new output path.')
            text = markdown.decode('utf-8')
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=output.parent) as scratch:
                temporary = Path(scratch) / 'source.md'
                result = subprocess.run(
                    [sys.executable, '-X', 'utf8', '-m', 'markitdown', str(source), '-o', str(temporary)],
                    cwd=scratch, capture_output=True, encoding='utf-8', errors='replace',
                )
                if result.returncode:
                    raise ValueError(f'MarkItDown failed: {result.stderr.strip()[-1400:]}')
                text = temporary.read_text(encoding='utf-8-sig')
            if args.reuse and digest(source) != key['source_sha256']:
                raise ValueError('Source changed during conversion. Run again when the file is stable.')

        if not any(char.isalnum() for char in text):
            parser.exit(2, 'No readable text found. Inspect the source pages or use local OCR as needed.\n')
        if not cached:
            markdown = text.encode('utf-8')
            with output.open('xb') as file:
                file.write(markdown)
            if args.reuse:
                record = {'key': key, 'output_sha256': sha256(markdown).hexdigest()}
                with metadata.open('x', encoding='utf-8', newline='\n') as file:
                    json.dump(record, file, ensure_ascii=False, indent=2)
    except PackageNotFoundError:
        parser.exit(1, 'MarkItDown is missing in this Python environment. Install markitdown[pdf] or use an existing environment.\n')
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')

    print(f'{"Reused" if cached else "Prepared"} {output}')
    if '\ufffd' in text:
        parser.exit(2, 'Markdown saved with Unicode replacement characters. Compare with the source before using it.\n')
    print('Check relevant passages against the original before building the reader.')


if __name__ == '__main__':
    main()
