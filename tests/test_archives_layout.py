from pathlib import Path


def test_archive_versions_only_keep_expected_top_level_directories():
  archive_root = Path(__file__).resolve().parents[1] / "archives"
  assert archive_root.is_dir(), "archives directory is missing"

  expected = {"assets", "modules", "routes"}

  for version_dir in archive_root.iterdir():
    if not version_dir.is_dir() or not version_dir.name.startswith("v"):
      continue

    names = {child.name for child in version_dir.iterdir()}
    assert names == expected, (
      f"{version_dir.name} must contain only {sorted(expected)}; "
      f"found {sorted(names)}"
    )

    for child in version_dir.iterdir():
      assert child.is_dir(), f"{version_dir.name}/{child.name} must be a directory"
