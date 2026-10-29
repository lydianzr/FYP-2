# Must be the first import. On Windows, paddle's DLLs clash with torch's
# if paddle loads first (WinError 127, shm.dll). Loading torch first avoids it.
import torch  # noqa: F401