"""Verify every wheel and sdist uses the release tag before any upload."""
import sys
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

from packaging.version import Version

tag = sys.argv[1]
if not tag.startswith("v"):
    raise SystemExit("Expected a v-prefixed release tag")
expected = Version(tag[1:])
for package in ("kitsuyui-animal", "kitsuyui-content_addr", "kitsuyui-hello"):
    dist = Path("packages") / package / "dist"
    wheels, sdists = list(dist.glob("*.whl")), list(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit(f"{package}: expected exactly one wheel and sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        metadata = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise SystemExit(f"{package}: wheel metadata missing or ambiguous")
        wheel_version = Parser().parsestr(archive.read(metadata[0]).decode())["Version"]
    with tarfile.open(sdists[0]) as archive:
        metadata = [m for m in archive.getmembers() if m.name.count("/") == 1 and m.name.endswith("/PKG-INFO")]
        if len(metadata) != 1:
            raise SystemExit(f"{package}: sdist metadata missing or ambiguous")
        sdist_version = Parser().parsestr(archive.extractfile(metadata[0]).read().decode())["Version"]
    if Version(wheel_version) != expected or Version(sdist_version) != expected:
        raise SystemExit(f"{package}: expected {expected}, got {wheel_version}, {sdist_version}")
    print(f"{package}: {expected}")
