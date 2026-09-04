import os
import uuid
import io
from datetime import datetime, timedelta

from flask import (
    Flask, request, render_template, redirect, url_for,
    send_from_directory, abort, jsonify
)
from werkzeug.utils import secure_filename
import qrcode

# ---------------- Configuration ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# Set this to your deployed Render URL, e.g. https://your-app.onrender.com
# Falls back to request.host_url automatically if not set.
BASE_URL = os.environ.get("BASE_URL", "").rstrip("/")

MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB total per upload batch
EXPIRE_HOURS = int(os.environ.get("EXPIRE_HOURS", "72"))  # links expire after N hours (0 = never)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# In-memory metadata store: {batch_id: {"created": datetime, "files": [filenames]}}
# For production with multiple workers, replace with a small SQLite table.
BATCHES = {}


def get_base_url():
    return BASE_URL if BASE_URL else request.host_url.rstrip("/")


def batch_dir(batch_id):
    return os.path.join(UPLOAD_ROOT, batch_id)


def is_expired(batch_id):
    if EXPIRE_HOURS <= 0:
        return False
    meta = BATCHES.get(batch_id)
    if not meta:
        return True
    return datetime.utcnow() > meta["created"] + timedelta(hours=EXPIRE_HOURS)


# ---------------- Routes ----------------

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    files = [f for f in files if f and f.filename]
    if not files:
        return render_template("index.html", error="សូមជ្រើសរើសឯកសារយ៉ាងតិចមួយ")

    batch_id = uuid.uuid4().hex[:10]
    dest = batch_dir(batch_id)
    os.makedirs(dest, exist_ok=True)

    saved_names = []
    for f in files:
        filename = secure_filename(f.filename)
        if not filename:
            continue
        # avoid collisions within the same batch
        target = os.path.join(dest, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(target):
            filename = f"{base}_{counter}{ext}"
            target = os.path.join(dest, filename)
            counter += 1
        f.save(target)
        saved_names.append(filename)

    BATCHES[batch_id] = {"created": datetime.utcnow(), "files": saved_names}

    download_url = f"{get_base_url()}/d/{batch_id}"
    return render_template(
        "qr.html",
        batch_id=batch_id,
        download_url=download_url,
        files=saved_names,
        expire_hours=EXPIRE_HOURS,
    )


@app.route("/qr/<batch_id>.png")
def qr_image(batch_id):
    if batch_id not in BATCHES:
        abort(404)
    download_url = f"{get_base_url()}/d/{batch_id}"
    img = qrcode.make(download_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return app.response_class(buf.getvalue(), mimetype="image/png")


@app.route("/d/<batch_id>")
def download_page(batch_id):
    if batch_id not in BATCHES or is_expired(batch_id):
        return render_template("expired.html"), 404
    meta = BATCHES[batch_id]
    return render_template("download.html", batch_id=batch_id, files=meta["files"])


@app.route("/download/<batch_id>/<path:filename>")
def download_file(batch_id, filename):
    if batch_id not in BATCHES or is_expired(batch_id):
        abort(404)
    dest = batch_dir(batch_id)
    return send_from_directory(dest, filename, as_attachment=True)


@app.route("/download-all/<batch_id>")
def download_all(batch_id):
    import zipfile
    if batch_id not in BATCHES or is_expired(batch_id):
        abort(404)
    dest = batch_dir(batch_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in BATCHES[batch_id]["files"]:
            zf.write(os.path.join(dest, fname), arcname=fname)
    buf.seek(0)
    return app.response_class(
        buf.getvalue(),
        mimetype="application/zip",
        headers={"Content-Disposition": f"attachment; filename={batch_id}.zip"},
    )


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
