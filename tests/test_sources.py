import hashlib

import pytest

from irish_schools import sources
from irish_schools.sources import ChecksumError, Source


def make_source(tmp_path, content: bytes, sha256: str | None = None, stable=True):
    origin = tmp_path / "origin.xlsx"
    origin.write_bytes(content)
    return Source(
        id="test",
        kind="post_primary_list",
        url=origin.as_uri(),
        sha256=sha256 or hashlib.sha256(content).hexdigest(),
        checksum_stable=stable,
    )


def test_manifest_ids_are_unique():
    ids = [s.id for s in sources.load_manifest()]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("kind", ["post_primary_list", "primary_list"])
def test_manifest_years_are_contiguous(kind):
    lists = [s for s in sources.load_manifest() if s.kind == kind]
    years = sorted(s.academic_year for s in lists if s.academic_year is not None)
    assert len(years) == len(lists)
    assert years == list(range(years[0], years[-1] + 1))


def test_filename_uses_url_suffix_or_extension():
    s = Source(id="a", kind="k", url="https://x/y/file.xlsx?v=1", sha256="")
    assert s.filename == "a.xlsx"
    s = Source(
        id="b", kind="k", url="https://x/api?f=1", sha256="", extension="geojson"
    )
    assert s.filename == "b.geojson"


def test_fetch_downloads_and_verifies(tmp_path):
    source = make_source(tmp_path, b"school data")
    path = sources.fetch(source, tmp_path / "out")
    assert path.read_bytes() == b"school data"


def test_fetch_rejects_bad_checksum(tmp_path):
    source = make_source(tmp_path, b"school data", sha256="0" * 64)
    with pytest.raises(ChecksumError):
        sources.fetch(source, tmp_path / "out")


def test_unstable_source_warns_on_bad_checksum(tmp_path):
    source = make_source(tmp_path, b"school data", sha256="0" * 64, stable=False)
    with pytest.warns(UserWarning):
        sources.fetch(source, tmp_path / "out")
