# QR_IMPORT_FORMAT.md

Wire format for transferring a `.l5r` character save from the **desktop app** (writer /
generator) to the **Android companion app** (reader / scanner) as a sequence of
**animated multi-frame QR codes**.

This is a **contract**: both implementations MUST follow it byte-for-byte. The
[test vector](#7-golden-test-vector) at the end is authoritative — if your implementation
reproduces it, it is correct.

- **Writer**: desktop L5RCM (Python). Renders an animated loop of QR codes on screen.
- **Reader**: Android companion (Kotlin). Scans the loop with the camera until it has
  collected every frame, reassembles, and feeds the JSON to its existing `.l5r` parser.

A `.l5r` save is plain JSON, typically **7–11 KB** — far larger than a single QR code can
hold reliably (~2–3 KB). So the payload is **compressed, then split across N frames**, each
frame a self-describing QR code. The reader collects frames in any order until complete.

---

## 1. Terminology

| Term        | Meaning                                                                 |
|-------------|-------------------------------------------------------------------------|
| **payload** | The original `.l5r` file content, a UTF-8 JSON string.                  |
| **blob**    | The gzip-compressed payload (raw bytes).                                |
| **b64**     | Standard Base64 (RFC 4648) text encoding of the blob.                   |
| **frame**   | One QR code = one text line carrying a header + a slice of `b64`.       |
| **transfer**| One complete set of frames sharing the same `id`.                       |

---

## 2. Encoding pipeline (writer)

```
payload (UTF-8 JSON string)
   │  1. encode UTF-8
   ▼
payload bytes
   │  2. gzip  (RFC 1952)
   ▼
blob (compressed bytes)          ── crc32 ──►  CRC = CRC32(blob)
   │  3. Base64 (standard alphabet, WITH padding)
   ▼
b64 (ASCII string)
   │  4. split into fixed-size character chunks
   ▼
chunk[0], chunk[1], … chunk[total-1]
   │  5. wrap each chunk in a frame header
   ▼
frame[0..total-1]  ── render each as a QR code, display in an animated loop ──►
```

Notes:

1. **UTF-8** without BOM.
2. **gzip** = the gzip *container* (RFC 1952: `1f 8b` magic, deflate, trailer), not raw
   deflate. `gzip.compress()` in Python and `GZIPOutputStream` in Java both produce this.
   Compression level is free to choose; it does not affect the contract (the reader only
   decompresses). Use `mtime=0` if you want reproducible bytes.
3. **Base64**: standard alphabet `A–Z a–z 0–9 + /` **with** `=` padding (RFC 4648 §4). Do
   **not** use the URL-safe alphabet.
4. **Split on the `b64` *string*** (not on blob bytes). Chunk size is the writer's choice; a
   chunk need NOT be a multiple of 4 — the reader concatenates all chunks first and decodes
   the whole `b64` once. See [§5](#5-qr-rendering--animation) for sizing.
5. The `CRC` (a single value for the whole transfer) is embedded **identically in every
   frame** so the reader can verify integrity after reassembly.

---

## 3. Frame grammar

Each frame is a single line of ASCII text (no trailing newline required), six fields joined
by a pipe `|` (`0x7C`):

```
L5RQR1|<id>|<seq>|<total>|<crc>|<data>
```

ABNF:

```abnf
frame   = magic "|" id "|" seq "|" total "|" crc "|" data
magic   = "L5RQR1"                  ; literal: tag "L5RQR" + format version "1"
id      = 1*16 idchar               ; transfer id, stable across all frames of one transfer
idchar  = ALPHA / DIGIT / "-" / "_"
seq     = 1*DIGIT                   ; 0-based frame index, decimal, no leading zeros
total   = 1*DIGIT                   ; total number of frames, >= 1
crc     = 8HEXDIG                   ; CRC32 of the blob, lowercase hex, zero-padded to 8
data    = *b64char                  ; one chunk of the Base64 string
b64char = ALPHA / DIGIT / "+" / "/" / "="
```

Why `|` is a safe delimiter: it appears in none of the other fields. The Base64 alphabet
(`A–Z a–z 0–9 + / =`) does not contain `|`, so `data` is unambiguous. Implementations
SHOULD nonetheless split with a field limit of 6 (`str.split("|", 5)` in Python /
`split("|", limit = 6)` in Kotlin) so a stray `|` could never corrupt `data`.

### Field details

- **`magic` / version** — `L5RQR1`. The trailing `1` is the format version. A reader MUST
  reject any frame whose magic is not exactly `L5RQR1` (forward-compat: unknown version ⇒
  ignore frame, surface "unsupported QR format").
- **`id`** — identifies one transfer (one character export). Generate a fresh short random
  id per export (e.g. 4–8 chars). It lets the reader detect when the user starts scanning a
  *different* character mid-session. Recommended: 6 uppercase base36 chars.
- **`seq`** — `0 <= seq < total`.
- **`total`** — `>= 1`. `total = 1` is valid (tiny payload fits in one frame); same format.
- **`crc`** — `CRC32(blob)`, the standard IEEE CRC32 (same polynomial as zlib / `java.util.zip.CRC32`),
  formatted as **lowercase**, **8 hex digits, zero-padded**. Identical in every frame.
- **`data`** — the `seq`-th chunk of `b64`. May be empty only if the whole `b64` is empty
  (never, in practice).

---

## 4. Decoding algorithm (reader)

State per in-progress transfer: `id`, `total`, `crc`, and a sparse map `seq → data`.

```
on QR text T:
    if T does not start with "L5RQR1|":            ignore (not our QR)
    parse fields; on malformed:                    ignore frame
    if active transfer exists and frame.id != active.id:
        reset state; start new transfer with frame.id      # user switched character
    if no active transfer:
        active = { id, total, crc, chunks: {} }
    if frame.total != active.total or frame.crc != active.crc:
        ignore frame                               # inconsistent; likely a stale frame
    active.chunks[seq] = data                       # idempotent; duplicates are harmless
    update progress UI: collected = count(active.chunks), of active.total

    if count(active.chunks) == active.total:        # all frames present
        b64  = concat(active.chunks[0..total-1])    # in seq order
        blob = base64_decode(b64)                   # standard alphabet, with padding
        if crc32(blob) != active.crc:               # integrity check
            error "QR integrity check failed"; reset; ask user to rescan
        payload = gunzip(blob).decode("utf-8")
        hand `payload` to the existing .l5r JSON parser
```

Reader requirements:

- **Order-independent**: frames arrive in whatever order the camera catches them; the loop
  repeats, so missed frames come around again. Keying by `seq` makes this naturally robust.
- **Duplicate-tolerant**: re-seeing a frame is a no-op.
- **Complete only when every slot `0..total-1` is filled.** Do not assume the loop’s start.
- **Verify `crc`** before decompressing. A mismatch means a corrupted/garbled capture →
  discard and rescan (do not partially import).
- **Decompress with gzip** (`GZIPInputStream`). Note: the reader never re-compresses, so
  gzip header differences between Python and Java (OS byte, XFL, mtime) are irrelevant — the
  writer’s exact blob bytes travel over the wire and are what the `crc` covers.

---

## 5. QR rendering & animation

These are **recommendations** for the writer (not part of the parse contract — the reader is
agnostic to QR version/ECC/timing):

- **QR mode**: byte mode (forced by the Base64 alphabet containing `+ / =` and lowercase).
- **Error correction**: level **M** is a good balance for on-screen scanning. Let the QR
  library auto-select the smallest version that fits each frame.
- **Chunk size**: keep frames small so QR symbols stay low-version and easy to scan from a
  laptop screen with a phone. **Recommended ~512–1024 Base64 chars per frame.** Smaller =
  more frames but faster, more reliable individual scans. With ~768 chars/frame an 11 KB
  character (≈3 KB gzip ≈4 KB b64) needs ~6 frames.
- **Animation**: display frames in a repeating loop at **~4–8 fps** (≈125–250 ms/frame).
  Loop forever; the reader stops you once it has everything. Show `seq+1/total` under each
  QR so a human can see progress too.
- **Quiet zone**: keep the standard ≥4-module margin; render large and high-contrast.

---

## 6. Error handling summary

| Condition (reader)                          | Action                                       |
|---------------------------------------------|----------------------------------------------|
| Text not starting `L5RQR1\|`                | Ignore (foreign QR).                         |
| Malformed header / non-numeric seq/total    | Ignore that frame.                           |
| Magic present but version ≠ `1`             | Surface "unsupported QR format version".     |
| `id` differs from active transfer           | Reset and start the new transfer.            |
| `total`/`crc` inconsistent within an `id`   | Ignore the inconsistent frame.               |
| All frames collected, CRC mismatch          | Error "integrity check failed"; rescan.      |
| gunzip fails / not valid UTF-8 / bad JSON   | Error "invalid character data"; rescan.      |

---

## 7. Golden test vector

Reproducible (`gzip mtime=0`, level 9, chunk size 32 chars, `id = 7F3A`). Both
implementations SHOULD ship a unit test that decodes these four frames back to the exact
payload, and the Python writer SHOULD regenerate these exact frames from the payload.

**Payload (UTF-8 JSON, 72 bytes):**

```json
{"version":"4.0","char":{"name":"Doji Test","clan":"crane"},"advans":[]}
```

**blob — gzip bytes (86 bytes, hex):**

```
1f8b080000000000020aab562a4b2d2acecccf53b25232d13350d2514ace482c52b2aa56ca4b
cc4d050abae467652a84a4169780a4721241ea928b12f352956a75941253ca12f38a95aca263
6b012e52ebe348000000
```

**b64 (116 chars):**

```
H4sIAAAAAAACCqtWKkstKs7Mz1OyUjLRM1DSUUrOSCxSsqpWykvMTQUKuuRnZSqEpBaXgKRyEkHqkosS81KVanWUElPKEvOKlayiY2sBLlLr40gAAAA=
```

**crc** = `CRC32(blob)` = `97dae91d`

**Frames** (4 frames, chunk size 32):

```
L5RQR1|7F3A|0|4|97dae91d|H4sIAAAAAAACCqtWKkstKs7Mz1OyUjLR
L5RQR1|7F3A|1|4|97dae91d|M1DSUUrOSCxSsqpWykvMTQUKuuRnZSqE
L5RQR1|7F3A|2|4|97dae91d|pBaXgKRyEkHqkosS81KVanWUElPKEvOK
L5RQR1|7F3A|3|4|97dae91d|layiY2sBLlLr40gAAAA=
```

Concatenating the four `data` fields in `seq` order reproduces the b64 above.

> The real export uses a much larger chunk size (~512–1024) so a full character is only a
> handful of frames; 32 here just forces multiple frames into a compact example.

---

## 8. Reference snippets

### Writer (Python) — desktop app

> **Production implementation:** `l5r/exporters/qr_transfer.py` (`make_frames` /
> `character_frames`), rendered to animated QR codes by
> `l5r/qmlui/proxies/qr_image_provider.py` and shown in the QML
> `QrShareDialog` (File ▸ *Share via QR code*). The golden test vector below is
> asserted by `l5r/exporters/tests/test_qr_transfer.py`.

```python
import gzip, base64, zlib, secrets, string

def make_qr_frames(json_text: str, chunk_chars: int = 768, transfer_id: str | None = None) -> list[str]:
    blob = gzip.compress(json_text.encode("utf-8"), compresslevel=9, mtime=0)
    b64 = base64.b64encode(blob).decode("ascii")
    crc = format(zlib.crc32(blob) & 0xFFFFFFFF, "08x")
    tid = transfer_id or "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    chunks = [b64[i:i + chunk_chars] for i in range(0, len(b64), chunk_chars)] or [""]
    total = len(chunks)
    return [f"L5RQR1|{tid}|{seq}|{total}|{crc}|{c}" for seq, c in enumerate(chunks)]

# Render each string with e.g. `qrcode` / `segno` at ECC level M and animate at ~5 fps.
```

### Reader (Kotlin) — Android companion (pure JVM, testable)

```kotlin
import java.util.Base64
import java.util.zip.CRC32
import java.util.zip.GZIPInputStream

class QrTransferError(msg: String) : Exception(msg)

class QrChunkAssembler {
    private var id: String? = null
    private var total: Int = 0
    private var crc: String = ""
    private val chunks = HashMap<Int, String>()

    val progress: Pair<Int, Int> get() = chunks.size to total   // collected, total

    /** @return decoded JSON when the transfer is complete, else null. */
    fun offer(text: String): String? {
        if (!text.startsWith("L5RQR1|")) return null
        val f = text.split("|", limit = 6)
        if (f.size != 6) return null
        if (f[0] != "L5RQR1") throw QrTransferError("unsupported QR format")
        val fid = f[1]
        val seq = f[2].toIntOrNull() ?: return null
        val tot = f[3].toIntOrNull() ?: return null
        val fcrc = f[4]
        val data = f[5]

        if (id != null && fid != id) reset()
        if (id == null) { id = fid; total = tot; crc = fcrc }
        if (tot != total || fcrc != crc) return null            // inconsistent frame

        chunks[seq] = data
        if (chunks.size != total) return null

        val b64 = StringBuilder().apply { for (i in 0 until total) append(chunks[i] ?: return null) }
        val blob = Base64.getDecoder().decode(b64.toString())
        val got = CRC32().apply { update(blob) }.value
        if (got.toString(16).padStart(8, '0') != crc) throw QrTransferError("integrity check failed")
        return GZIPInputStream(blob.inputStream()).readBytes().toString(Charsets.UTF_8)
    }

    fun reset() { id = null; total = 0; crc = ""; chunks.clear() }
}
```

---

## 9. Versioning

The format version lives in the magic token (`L5RQR**1**`). Any breaking change bumps it to
`L5RQR2`, etc. Readers MUST reject magics they do not recognise rather than guessing. Adding
strictly-optional trailing fields is still a breaking change under this rule (the grammar is
fixed at six fields for v1), so prefer a version bump.
