#!/usr/bin/env python3
"""Write one original fortune-cookie line for a software developer.

The program writes exactly one line (no trailing newline) to
/output/entry.txt, then verifies what it wrote: one line, at most
120 characters, mode 0644 so the grader can read it as another user.

Standard library only. It never touches the permissions of the
/output directory itself (that directory is root-owned and merely
writable -- chmod on it raises PermissionError); it only chmods the
file it created.
"""

import os
import sys
import tempfile
from pathlib import Path

# One original fortune-cookie line for a developer. The twist: the bug
# you cannot reproduce is already in production, watching you.
LINE = "You will fix the bug you cannot reproduce \u2014 it is already in production, watching you."

MAX_CHARS = 120


def entry_path() -> Path:
    """Output file: /output/entry.txt, overridable for local testing."""
    out_dir = Path(os.environ.get("OUTPUT_DIR", "/output"))
    return out_dir / "entry.txt"


def write_entry(path: Path) -> None:
    """Write the line atomically, with no trailing newline, mode 0644.

    The line goes to a temp file in the same directory first, then
    os.replace moves it into place, so a crash can never leave a
    half-written entry behind. The temp file is chmodded 0644 before
    the move (tempfile-made files start 0600 whatever the umask).
    Only the FILE is chmodded -- never the /output directory.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".entry-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(LINE)
        # The file must be readable by the grader (uid 65534). chmod the
        # FILE only -- never the /output directory.
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def verify(path: Path) -> None:
    """Read the file back and prove it is exactly the entry, one line."""
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    assert text == LINE, "written text differs from the entry line"
    assert "\n" not in text and "\r" not in text, "entry must be one line"
    assert len(text) <= MAX_CHARS, f"entry is {len(text)} chars, over {MAX_CHARS}"
    assert len(raw) == len(LINE.encode("utf-8")), "byte count mismatch"
    assert (os.stat(path).st_mode & 0o777) == 0o644, "entry file must be mode 0644"


def main() -> int:
    os.umask(0o022)
    assert len(LINE) <= MAX_CHARS, f"entry is {len(LINE)} chars, over {MAX_CHARS}"
    assert "\n" not in LINE and "\r" not in LINE, "entry must be one line"
    assert LINE == LINE.strip(), "entry must have no leading/trailing whitespace"
    path = entry_path()
    write_entry(path)
    verify(path)
    print(f"wrote {path} ({len(LINE)} chars, {len(LINE.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
