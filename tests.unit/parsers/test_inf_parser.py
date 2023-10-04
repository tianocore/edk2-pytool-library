from pathlib import Path

from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser

INF_EXAMPLE1 = """
[Defines]
  INF_VERSION                    = 0x00010005
  BASE_NAME                      = TestLib
  FILE_GUID                      = ffffffff-ffff-ffff-ffff-ffffffffffff
  MODULE_TYPE                    = DXE_DRIVER
  VERSION_STRING                 = 1.0
  LIBRARY_CLASS                  = BaseTestLib

[Sources]
# [Binaries]
  File1.c

[Sources.common]
  File2.c

[Sources.IA32]
  # Random Comment
  File3.c
  # File999.c

[sources.IA32, sources.X64]
  File4.c

[LibraryClasses]
  Library1

[Binaries]
  Binary1.efi

[LibraryClasses.common]
  Library2

[LibraryClasses.IA32]
  Library3

[LibraryClasses.IA32, LibraryClasses.X64]
  Library4
"""
def test_inf_parser_scoped_libraryclasses(tmp_path: Path):
    """Test that we accurately detect scoped library classes."""
    inf_path = tmp_path / "test.inf"
    inf_path.touch()
    inf_path.write_text(INF_EXAMPLE1)

    infp = InfParser()
    infp.ParseFile(inf_path)

    assert sorted(infp.get_libraries([])) == sorted(["Library1", "Library2"])
    assert sorted(infp.get_libraries(["Common"])) == sorted(["Library1", "Library2"])
    assert sorted(infp.get_libraries(["IA32"])) == sorted(["Library1", "Library2", "Library3", "Library4"])
    assert sorted(infp.get_libraries(["X64"])) == sorted(["Library1", "Library2", "Library4"])

def test_inf_parser_scoped_sources(tmp_path: Path):
    """Test that we accurately detect scoped sources."""
    inf_path = tmp_path / "test.inf"
    inf_path.touch()
    inf_path.write_text(INF_EXAMPLE1)

    infp = InfParser()
    infp.ParseFile(inf_path)

    assert sorted(infp.get_sources([])) == sorted(["File1.c", "File2.c"])
    assert sorted(infp.get_sources(["Common"])) == sorted(["File1.c", "File2.c"])
    assert sorted(infp.get_sources(["IA32"])) == sorted(["File1.c", "File2.c", "File3.c", "File4.c"])
    assert sorted(infp.get_sources(["X64"])) == sorted(["File1.c", "File2.c", "File4.c"])
