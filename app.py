import re
import urllib.error
import urllib.parse
import urllib.request

from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)

# TP's existing Google Form. Website bookings are passed straight into it,
# so responses keep arriving in the same place (Google Forms / Sheets).
GOOGLE_FORM_URL = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdY4iMSVjPhfRr5Q740UFEqvqDGJLQX9Ir_fJTYiijJUV1Y7g/formResponse"
)

# website field -> (Google Form entry, required, max length)
FIELDS = {
    "name": ("entry.2005620554", True, 120),
    "email": ("emailAddress", True, 200),
    "phone": ("entry.1166974658", False, 40),
    "zip": ("entry.1454259889", True, 20),
    "style": ("entry.608793142", True, 2000),
    "budget": ("entry.1868820442", False, 120),
    "event": ("entry.1642305154", False, 2000),
    "requests": ("entry.811919199", False, 2000),
    "comments": ("entry.839337160", False, 2000),
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@app.route("/")
def index():
    return render_template("index.html")


SITE_URL = "https://presidentialstyles.shop"


@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}/</loc></url>\n"
        "</urlset>\n"
    )
    return Response(body, mimetype="application/xml")


@app.route("/book", methods=["POST"])
def book():
    data = request.get_json(silent=True) or request.form

    # Spam trap: real visitors never see or fill this field.
    if (data.get("website") or "").strip():
        return jsonify(ok=True)

    payload, errors = {}, {}
    for key, (entry, required, limit) in FIELDS.items():
        value = (data.get(key) or "").strip()[:limit]
        if required and not value:
            errors[key] = "Required"
        elif value:
            payload[entry] = value
    email = (data.get("email") or "").strip()
    if email and not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email"
    if errors:
        return jsonify(ok=False, errors=errors), 400

    body = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        GOOGLE_FORM_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "PresidentialStylesSite/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
    except urllib.error.URLError:
        ok = False

    if not ok:
        return jsonify(ok=False, error="send_failed"), 502
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(debug=True)
