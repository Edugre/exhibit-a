"""Builds the HW #4 submission ZIP under Canvas's 50 MB limit, from the committed files, without touching the repo.

usage (from the repo root):  python tools/make_submission.py [out.zip] [--max-side 1024]

What goes in, and what changes on the way (the repository keeps everything at full size):
  * Every file git tracks at HEAD: the Godot project, scripts, scenes, assets, docs and the asset tools.
  * Left out: asset *source* files (.blend and the large images under */source/); the Python tools that
    generate assets stay. The full sources are on GitHub.
  * Left out: textures Godot extracts from a .glb on import ("Extract Textures"). They are copies of images
    already inside the .glb, and Godot writes them again on the first import. (Checked: a fresh import of the
    slimmed project re-extracts all of them, with no errors.)
  * Textures larger than --max-side pixels (default 1024) are scaled down to it, both loose PNG/JPG files and
    the images embedded in .glb files. UI images (ui/) are left exactly as they are: their pixel sizes matter.
  * Images embedded in a .glb with no transparency are stored as JPEG (quality 92) instead of PNG. Godot
    extracts them as .jpg on import and builds the model's materials from them, so nothing else refers to
    them; images with an alpha channel in use stay PNG.
Needs Python 3 with Pillow.
"""
import io
import json
import pathlib
import struct
import subprocess
import sys
import zipfile

from PIL import Image

KEEP_IN_SOURCE = {".py", ".md", ".json", ".txt"}
NO_RESIZE_DIRS = ("ui/",)
LIMIT_MB = 50


def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\n") if f]


def glb_parts(data):
    magic, version, _ = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67, "not a glb"
    offset, gltf, binary = 12, None, b""
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += 8 + length
    return gltf, binary


def embedded_image_names(path):
    gltf, _ = glb_parts(path.read_bytes())
    return [im.get("name", "") for im in gltf.get("images", [])]


def shrink_image_bytes(raw, mime, max_side):
    image = Image.open(io.BytesIO(raw))
    if max(image.size) <= max_side:
        return raw
    scale = max_side / max(image.size)
    image = image.resize((max(1, round(image.size[0] * scale)), max(1, round(image.size[1] * scale))), Image.LANCZOS)
    out = io.BytesIO()
    if mime == "image/jpeg":
        image.convert("RGB").save(out, "JPEG", quality=90)
    else:
        image.save(out, "PNG", optimize=True)
    return out.getvalue()


def opaque_jpeg(raw, max_side):
    """The image as a JPEG, scaled down if needed, or None if it uses transparency."""
    image = Image.open(io.BytesIO(raw))
    if image.mode in ("RGBA", "LA", "P") and image.convert("RGBA").getextrema()[3][0] < 255:
        return None
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((max(1, round(image.size[0] * scale)), max(1, round(image.size[1] * scale))), Image.LANCZOS)
    out = io.BytesIO()
    image.convert("RGB").save(out, "JPEG", quality=92)
    return out.getvalue()


def shrink_glb(data, max_side):
    """Re-packs a .glb with its embedded images scaled down (and opaque ones as JPEG); every buffer view is
    laid out again."""
    gltf, binary = glb_parts(data)
    if not gltf.get("images"):
        return data
    images_by_view = {im["bufferView"]: im for im in gltf["images"] if "bufferView" in im}
    new_bin = bytearray()
    for index, view in enumerate(gltf["bufferViews"]):
        start = view.get("byteOffset", 0)
        chunk = binary[start:start + view["byteLength"]]
        if index in images_by_view:
            image = images_by_view[index]
            jpeg = opaque_jpeg(chunk, max_side)
            if jpeg is not None and len(jpeg) < len(chunk):
                chunk = jpeg
                image["mimeType"] = "image/jpeg"
            else:
                chunk = shrink_image_bytes(chunk, image.get("mimeType", "image/png"), max_side)
        while len(new_bin) % 4:
            new_bin.append(0)
        view["byteOffset"] = len(new_bin)
        view["byteLength"] = len(chunk)
        new_bin += chunk
    while len(new_bin) % 4:
        new_bin.append(0)
    gltf["buffers"][0]["byteLength"] = len(new_bin)
    text = json.dumps(gltf, separators=(",", ":")).encode("utf8")
    text += b" " * (-len(text) % 4)
    body = struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(new_bin), 0x004E4942) + bytes(new_bin)
    return struct.pack("<III", 0x46546C67, 2, 12 + len(body)) + body


def main():
    args = sys.argv[1:]
    max_side = 1024
    if "--max-side" in args:
        i = args.index("--max-side")
        max_side = int(args[i + 1])
        del args[i:i + 2]
    out_path = pathlib.Path(args[0] if args else "CAP4052_HW4_Goncalvez_Waisman_Serrano.zip")
    files = tracked_files()
    tracked = set(files)

    # Textures Godot extracts from each .glb: <glb name>_<image name>.png/.jpg beside it
    extracted = set()
    for f in files:
        if f.endswith(".glb") and "/source/" not in f:
            path = pathlib.Path(f)
            for name in embedded_image_names(path):
                for ext in (".png", ".jpg"):
                    candidate = (path.parent / f"{path.stem}_{name}{ext}").as_posix()
                    if candidate in tracked:
                        extracted.update({candidate, candidate + ".import"})

    skipped, shrunk = [], []
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in files:
            path = pathlib.Path(f)
            if "/source/" in f and path.suffix.lower() not in KEEP_IN_SOURCE:
                skipped.append(f)
                continue
            if f in extracted:
                skipped.append(f)
                continue
            data = path.read_bytes()
            resizable = not f.startswith(NO_RESIZE_DIRS)
            if resizable and path.suffix.lower() == ".glb":
                small = shrink_glb(data, max_side)
                if len(small) < len(data):
                    shrunk.append(f)
                data = small
            elif resizable and path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                mime = "image/jpeg" if path.suffix.lower() != ".png" else "image/png"
                small = shrink_image_bytes(data, mime, max_side)
                if small is not data:
                    shrunk.append(f)
                data = small
            z.writestr(f, data)
    size = out_path.stat().st_size / 2**20
    print(f"wrote {out_path}: {size:.1f} MB ({len(files) - len(skipped)} files; {len(skipped)} left out; {len(shrunk)} textures scaled to {max_side} px)")
    if size > LIMIT_MB:
        print(f"WARNING: over the {LIMIT_MB} MB limit. Try --max-side 512.")


if __name__ == "__main__":
    main()
