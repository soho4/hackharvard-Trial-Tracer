"""Byte-level provenance only; reading a PDF is not source interpretation approval."""

import hashlib

from .errors import InputError


def hash_source_pdf(path):
    with path.open("rb") as stream:
        prefix = stream.read(5)
        if prefix != b"%PDF-":
            raise InputError("SOURCE_PDF", "Source file does not begin with a PDF header")
        sha = hashlib.sha256(prefix)
        for block in iter(lambda: stream.read(65_536), b""):
            sha.update(block)
    return {"pdf_sha256": sha.hexdigest(), "retrieval_status": "LOCAL_PDF_BYTES_HASHED_IDENTITY_NOT_CHECKED_BY_RUNTIME"}
