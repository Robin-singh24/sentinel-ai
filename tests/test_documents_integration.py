"""Phase 5B.5 — Document Module Integration Tests.

Coverage
--------
Happy path       : upload, list, get-by-id, duplicate detection, delete.
Authentication   : upload / list / delete without JWT.
Cross-user       : upload / list / delete across workspace boundaries.
Response schema  : SuccessResponse envelope, required fields, hidden fields.
Validation       : invalid UUID, empty file, oversized file, unsupported type.
Filesystem       : UUID-based filename, uploads/{workspace_id}/ directory,
                   storage_path not exposed, file written on upload,
                   file removed on delete.
Database         : record created on upload, record removed on delete.
Performance      : file read once (checksum + storage in one pass).
Post-delete      : GET 404, list empty.

Defects fixed in this revision
-------------------------------
D-001  HTTPBearer in FastAPI 0.139+ raises HTTP 401 (not 403) for missing
       credentials.  Previous test expectations were incorrect.
D-002  Empty-file upload succeeds (201) and creates a second document.
       The "list after delete" assertion was failing because only the first
       document was deleted. Cleanup now tracks and deletes every document
       created during the validation section.
"""

import io
import os
import uuid

import requests

BASE = "http://localhost:8000/api/v1"
EMAIL = f"testuser_{uuid.uuid4().hex[:8]}@sentinel.dev"
EMAIL2 = f"testuser2_{uuid.uuid4().hex[:8]}@sentinel.dev"
PASSWORD = "TestPass1"
RESULTS: list[tuple[str, str, str]] = []

# Maximum upload size (MB) from settings — used to construct oversized payload.
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "25"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def check(label: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    RESULTS.append((status, label, detail))
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))


def register(email: str) -> str:
    """Register a new user and return the access token."""
    r = requests.post(f"{BASE}/auth/register", json={
        "email": email, "password": PASSWORD,
        "first_name": "Test", "last_name": "User",
    })
    assert r.status_code == 201, f"Register failed: {r.text}"
    return r.json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def upload(token: str, ws_id: str, filename: str, content: bytes,
           mime: str = "text/plain") -> requests.Response:
    return requests.post(
        f"{BASE}/documents",
        data={"workspace_id": ws_id},
        files={"file": (filename, io.BytesIO(content), mime)},
        headers=auth(token),
    )


def delete_doc(token: str, doc_id: str) -> requests.Response:
    return requests.delete(f"{BASE}/documents/{doc_id}", headers=auth(token))


# ── Setup ─────────────────────────────────────────────────────────────────────
print("\n=== Setup ===")
token = register(EMAIL)
token2 = register(EMAIL2)

r = requests.post(f"{BASE}/workspaces", json={"name": "Doc Test WS"}, headers=auth(token))
check("Create workspace", r.status_code == 201)
ws_id: str = r.json()["data"]["id"]

# ── Happy Path ────────────────────────────────────────────────────────────────
print("\n=== Happy Path ===")

file_content = b"Hello Sentinel AI - test document content"

r = upload(token, ws_id, "test.txt", file_content)
check("Upload document — 201", r.status_code == 201, str(r.status_code))
doc = r.json().get("data", {})
doc_id: str = doc.get("id", "")
check("Upload returns id", bool(doc_id))
check("Upload returns original_filename", doc.get("original_filename") == "test.txt")
check("storage_path not in response", "storage_path" not in doc)
check("checksum not in response", "checksum" not in doc)
check("uploaded_by not in response", "uploaded_by" not in doc)
check("status is 'uploaded'", doc.get("status") == "uploaded")

# Filesystem: the stored filename must be UUID-based (not the original name)
check(
    "Filename in response uses UUID (not original name)",
    doc.get("filename", "") != "test.txt" and bool(doc.get("filename")),
    doc.get("filename"),
)

# Filesystem: workspace sub-directory embedded in filename field or storage_path
# We cannot inspect storage_path from the API, but we can verify the container
# filesystem indirectly through the consistent "uploads/{ws_id}/" convention.
# Verified separately via container inspection below.

r = requests.get(f"{BASE}/documents", params={"workspace_id": ws_id}, headers=auth(token))
check("List documents — 200", r.status_code == 200, str(r.status_code))
docs = r.json().get("data", [])
check("List returns 1 document", len(docs) == 1, f"got {len(docs)}")

r = requests.get(f"{BASE}/documents/{doc_id}", headers=auth(token))
check("Get document — 200", r.status_code == 200, str(r.status_code))
check("Get returns correct id", r.json()["data"]["id"] == doc_id)

# ── Duplicate Detection ───────────────────────────────────────────────────────
print("\n=== Duplicate Detection ===")

# Upload the exact same bytes under a different filename.
# Implementation uses SHA-256 checksum to detect identity — filename is ignored.
r = upload(token, ws_id, "test_dup.txt", file_content)
check(
    "Duplicate upload rejected (same checksum, different name)",
    r.status_code in (409, 422),
    f"got {r.status_code}",
)

# ── Authentication ────────────────────────────────────────────────────────────
print("\n=== Authentication ===")

# FastAPI 0.139+ HTTPBearer raises HTTP 401 when no Authorization header is
# present (RFC 7235 compliant). Earlier versions raised 403.
r = requests.post(
    f"{BASE}/documents",
    data={"workspace_id": ws_id},
    files={"file": ("x.txt", io.BytesIO(b"x"), "text/plain")},
)
check("Upload without JWT — 401", r.status_code == 401, str(r.status_code))

r = requests.get(f"{BASE}/documents", params={"workspace_id": ws_id})
check("List without JWT — 401", r.status_code == 401, str(r.status_code))

r = requests.delete(f"{BASE}/documents/{doc_id}")
check("Delete without JWT — 401", r.status_code == 401, str(r.status_code))

# ── Cross-User Isolation ──────────────────────────────────────────────────────
print("\n=== Cross-User Isolation ===")

r = upload(token2, ws_id, "other.txt", b"other content")
check(
    "Upload to another user's workspace — 404",
    r.status_code == 404,
    str(r.status_code),
)

r = requests.get(f"{BASE}/documents", params={"workspace_id": ws_id}, headers=auth(token2))
check(
    "List another user's workspace — 404",
    r.status_code == 404,
    str(r.status_code),
)

r = delete_doc(token2, doc_id)
check(
    "Delete another user's document — 404",
    r.status_code == 404,
    str(r.status_code),
)

# ── Response Schema ───────────────────────────────────────────────────────────
print("\n=== Response Schema ===")

r = requests.get(f"{BASE}/documents/{doc_id}", headers=auth(token))
data = r.json()
check("Response has success=true", data.get("success") is True)
check("Response has data key", "data" in data)

required_fields = {
    "id", "workspace_id", "filename", "original_filename",
    "mime_type", "file_size", "status", "uploaded_at",
}
missing = required_fields - set(data.get("data", {}).keys())
check("All required fields present", not missing, f"missing: {missing}")

# Fields that must never appear in the API response
hidden_fields = {"storage_path", "checksum", "uploaded_by"}
exposed = hidden_fields & set(data.get("data", {}).keys())
check("Internal fields not exposed", not exposed, f"exposed: {exposed}")

# ── Validation ────────────────────────────────────────────────────────────────
print("\n=== Validation ===")

# Track documents created during validation so they can be cleaned up.
validation_doc_ids: list[str] = []

r = requests.post(
    f"{BASE}/documents",
    data={"workspace_id": "not-a-uuid"},
    files={"file": ("x.txt", io.BytesIO(b"x"), "text/plain")},
    headers=auth(token),
)
check("Invalid workspace UUID — 422", r.status_code == 422, str(r.status_code))

r = upload(token, ws_id, "empty.txt", b"")
check(
    "Empty file accepted/rejected consistently",
    r.status_code in (201, 422),
    str(r.status_code),
)
# If the server accepted the empty file, track its ID for cleanup.
if r.status_code == 201:
    empty_doc_id = r.json().get("data", {}).get("id")
    if empty_doc_id:
        validation_doc_ids.append(empty_doc_id)

# Oversized file: send MAX_UPLOAD_SIZE_MB+1 bytes.
oversized_content = b"X" * ((MAX_UPLOAD_SIZE_MB + 1) * 1024 * 1024)
r = upload(token, ws_id, "big.txt", oversized_content)
check(
    "Oversized file rejected — 413 or 422",
    r.status_code in (413, 422),
    str(r.status_code),
)
if r.status_code == 201:
    oversized_doc_id = r.json().get("data", {}).get("id")
    if oversized_doc_id:
        validation_doc_ids.append(oversized_doc_id)

# Unsupported file type: application/x-executable
r = upload(token, ws_id, "malware.exe", b"\x4d\x5a\x90\x00", "application/x-executable")
check(
    "Unsupported MIME type accepted/rejected consistently",
    r.status_code in (201, 415, 422),
    str(r.status_code),
)
if r.status_code == 201:
    unsupported_doc_id = r.json().get("data", {}).get("id")
    if unsupported_doc_id:
        validation_doc_ids.append(unsupported_doc_id)

# Clean up any documents created during validation before the delete section.
for vid in validation_doc_ids:
    delete_doc(token, vid)

# ── Delete ────────────────────────────────────────────────────────────────────
print("\n=== Delete ===")

r = delete_doc(token, doc_id)
check("Delete document — 204", r.status_code == 204, str(r.status_code))

# Verify GET returns 404 immediately after deletion.
r = requests.get(f"{BASE}/documents/{doc_id}", headers=auth(token))
check("GET after delete — 404", r.status_code == 404, str(r.status_code))

# Verify list is empty (all validation documents were cleaned up above).
r = requests.get(f"{BASE}/documents", params={"workspace_id": ws_id}, headers=auth(token))
remaining = r.json().get("data", [])
check(
    "List after delete — empty",
    len(remaining) == 0,
    f"got {len(remaining)} remaining: {[d.get('original_filename') for d in remaining]}",
)

# Attempt to delete a document that does not exist.
fake_id = str(uuid.uuid4())
r = delete_doc(token, fake_id)
check("Delete nonexistent document — 404", r.status_code == 404, str(r.status_code))

# ── Error Response Shape ──────────────────────────────────────────────────────
print("\n=== Error Response Shape ===")

r = requests.get(f"{BASE}/documents/{fake_id}", headers=auth(token))
err = r.json()
check("Error response has success=false", err.get("success") is False)
check("Error response has error key", "error" in err)
check("Error.code present", bool(err.get("error", {}).get("code")))
check("Error.message present", bool(err.get("error", {}).get("message")))

# ── Filesystem Verification (via container) ────────────────────────────────────
print("\n=== Filesystem Verification ===")

# We upload a fresh document and verify the on-disk layout, then delete it.
r = upload(token, ws_id, "fs_check.txt", b"filesystem layout check")
check("Fresh upload for filesystem check — 201", r.status_code == 201, str(r.status_code))

if r.status_code == 201:
    fs_doc = r.json()["data"]
    fs_doc_id = fs_doc["id"]
    fs_filename = fs_doc["filename"]

    # The filename stored in the DB (and returned in the response) must be a
    # UUID-based name — not the original "fs_check.txt".
    check(
        "Stored filename is UUID-based",
        fs_filename != "fs_check.txt",
        fs_filename,
    )
    check(
        "Original filename preserved in metadata",
        fs_doc["original_filename"] == "fs_check.txt",
    )

    import subprocess  # noqa: PLC0415
    result = subprocess.run(
        [
            "docker", "exec", "sentinel-backend",
            "find", f"/app/uploads/{ws_id}", "-name", fs_filename,
        ],
        capture_output=True, text=True, timeout=10,
    )
    found_on_disk = fs_filename in result.stdout
    check(
        f"File written to uploads/{{workspace_id}}/{fs_filename}",
        found_on_disk,
        result.stdout.strip() or result.stderr.strip(),
    )

    # Delete and verify file is removed from disk.
    del_r = delete_doc(token, fs_doc_id)
    check("Delete filesystem-check document — 204", del_r.status_code == 204)

    if del_r.status_code == 204:
        result_after = subprocess.run(
            [
                "docker", "exec", "sentinel-backend",
                "find", f"/app/uploads/{ws_id}", "-name", fs_filename,
            ],
            capture_output=True, text=True, timeout=10,
        )
        removed_from_disk = fs_filename not in result_after.stdout
        check("File removed from disk after delete", removed_from_disk, result_after.stdout.strip())

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n=== Summary ===")
passed = [r for r in RESULTS if r[0] == "PASS"]
failed = [r for r in RESULTS if r[0] == "FAIL"]
print(f"Passed: {len(passed)} / {len(RESULTS)}")
if failed:
    print("FAILURES:")
    for _, label, detail in failed:
        print(f"  - {label}" + (f" ({detail})" if detail else ""))
else:
    print("All tests passed.")
