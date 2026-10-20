"""Serve the app over HTTPS with a local self-signed certificate (issue #4, SEC-F-004).

    python scripts/serve_https.py                 # https://localhost:8443  (http://localhost:8080 redirects)
    python scripts/serve_https.py --https-port 9443 --http-port 9080

The certificate and private key are created in instance/certs/ (ignored by Git).
Your browser will warn that the certificate is self-signed: that is expected in the lab.
"""
import argparse
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.tls import build_http_server, build_https_server, make_dev_certificate, redirect_app  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--https-port", type=int, default=8443)
    parser.add_argument("--http-port", type=int, default=8080, help="plain HTTP port that only redirects to HTTPS")
    args = parser.parse_args()

    app = create_app()
    cert, key = make_dev_certificate(ROOT / "instance" / "certs")
    https_server = build_https_server(app, cert, key, args.host, args.https_port)
    http_server = build_http_server(redirect_app(args.https_port), args.host, args.http_port)

    threading.Thread(target=http_server.safe_start, daemon=True).start()
    print(f"HTTPS: https://localhost:{args.https_port}/   (TLS 1.2 or newer)")
    print(f"HTTP : http://localhost:{args.http_port}/   redirects to HTTPS")
    print("Press Ctrl+C to stop.")
    try:
        https_server.safe_start()
    except KeyboardInterrupt:
        pass
    finally:
        https_server.stop()
        http_server.stop()


if __name__ == "__main__":
    main()
