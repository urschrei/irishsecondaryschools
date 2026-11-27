"""Read the source manifest and download the source files."""

import hashlib
import shutil
import tomllib
import urllib.request
import warnings
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "sources.toml"
SOURCE_DIR = ROOT / "sources"

# gov.ie refuses requests that have no browser-like User-Agent.
USER_AGENT = "Mozilla/5.0 (compatible; irish-schools-build)"


class ChecksumError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    id: str
    kind: str
    url: str
    sha256: str
    academic_year: int | None = None
    extension: str | None = None
    checksum_stable: bool = True

    @property
    def filename(self) -> str:
        ext = self.extension or Path(urlparse(self.url).path).suffix.lstrip(".")
        return f"{self.id}.{ext}"

    def path(self, directory: Path = SOURCE_DIR) -> Path:
        return directory / self.filename


def load_manifest(path: Path = MANIFEST) -> list[Source]:
    with path.open("rb") as f:
        data = tomllib.load(f)
    return [Source(**entry) for entry in data["source"]]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(source: Source, path: Path) -> None:
    """Compare the file checksum with the manifest.

    Raise ChecksumError on a mismatch, or warn if the source does not
    give stable bytes.
    """
    actual = sha256_of(path)
    if actual == source.sha256:
        return
    message = f"{source.id}: expected sha256 {source.sha256}, got {actual}"
    if source.checksum_stable:
        raise ChecksumError(message)
    warnings.warn(message, stacklevel=2)


def fetch(source: Source, directory: Path = SOURCE_DIR, force: bool = False) -> Path:
    """Download one source file if it is not present, then verify it."""
    target = source.path(directory)
    if force or not target.exists():
        directory.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".part")
        request = urllib.request.Request(source.url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=300) as response:
            with partial.open("wb") as out:
                shutil.copyfileobj(response, out)
        partial.replace(target)
    verify(source, target)
    return target


def fetch_all(directory: Path = SOURCE_DIR, force: bool = False) -> list[Path]:
    return [fetch(s, directory, force) for s in load_manifest()]
