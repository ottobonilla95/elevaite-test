import os as _os

# Make this nested package proxy to the project root so imports like
# `elevaite_ingestion.parsers` resolve to the existing modules located
# directly under the project root (../parsers, ../utils, ../db.py, ...).
# This avoids a large file move while enabling proper packaging.
# _parent_dir = _os.path.dirname(_os.path.dirname(__file__))
# if _parent_dir not in __path__:
#     __path__.append(_parent_dir)
