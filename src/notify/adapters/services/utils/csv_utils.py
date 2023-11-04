from csv import DictReader
from itertools import islice
from typing import Any, Generator


def read_csv_in_chunks(
    csv_reader: DictReader, chunk_size: int
) -> Generator[list[dict[str, Any]], None, None]:
    while True:
        chunk = list(islice(csv_reader, chunk_size))
        if not chunk:
            break
        yield chunk
