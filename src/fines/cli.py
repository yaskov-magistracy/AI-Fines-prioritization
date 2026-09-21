import argparse
import asyncio
from pathlib import Path

from fines.config import get_settings
from fines.db import init_engine, session_scope
from fines.logging import configure_logging
from fines.pipeline import IngestPipeline


async def _ingest_dir(directory: Path) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_engine(settings)

    pdfs = await asyncio.to_thread(lambda: sorted(directory.rglob("*.pdf")))
    for pdf in pdfs:
        data = await asyncio.to_thread(pdf.read_bytes)
        async with session_scope() as session:
            document = await IngestPipeline(session, settings).ingest(pdf.name, data)
            print(f"{pdf.name}: {document.status}")
    return len(pdfs)


def main() -> None:
    parser = argparse.ArgumentParser(prog="fines")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="загрузить все PDF из папки")
    ingest.add_argument("directory", type=Path)

    args = parser.parse_args()
    if args.command == "ingest":
        count = asyncio.run(_ingest_dir(args.directory))
        print(f"обработано файлов: {count}")


if __name__ == "__main__":
    main()
