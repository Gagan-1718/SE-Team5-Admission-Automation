"""HTTPS support for the lab demonstration (SEC-F-004, SAD assumption A-16).

Flask's built-in development server is not an acceptable HTTPS setup, so the app is
served by Cheroot (a production grade WSGI server) with a locally generated,
self-signed certificate. Nothing here is imported by the normal app: it needs the
extra packages in requirements-https.txt and is only used by scripts/serve_https.py.

The private key lives in the git-ignored instance/ folder and must never be committed.
"""
import datetime
import ipaddress
import ssl
from pathlib import Path
from urllib.parse import quote


def make_dev_certificate(directory, hosts=("localhost", "127.0.0.1")):
    """Create (or reuse) a self-signed certificate and key. Returns (cert_path, key_path)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cert_path = directory / "dev-cert.pem"
    key_path = directory / "dev-key.pem"
    if cert_path.exists() and key_path.exists():
        return cert_path, key_path

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    alt_names = []
    for host in hosts:
        try:
            alt_names.append(x509.IPAddress(ipaddress.ip_address(host)))
        except ValueError:
            alt_names.append(x509.DNSName(host))
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    return cert_path, key_path


def build_https_server(wsgi_app, cert_path, key_path, host="127.0.0.1", port=8443):
    """A Cheroot server that only accepts TLS 1.2 or newer."""
    from cheroot.ssl.builtin import BuiltinSSLAdapter
    from cheroot.wsgi import Server

    adapter = BuiltinSSLAdapter(str(cert_path), str(key_path))
    adapter.context.minimum_version = ssl.TLSVersion.TLSv1_2
    server = Server((host, port), wsgi_app)
    server.ssl_adapter = adapter
    return server


def build_http_server(wsgi_app, host="127.0.0.1", port=8080):
    """A plain HTTP server (used for the redirect, and as a control in tests)."""
    from cheroot.wsgi import Server

    return Server((host, port), wsgi_app)


def redirect_app(https_port, host="localhost"):
    """A tiny WSGI app that sends every plain HTTP request to the same path on HTTPS."""

    def app(environ, start_response):
        path = quote(environ.get("PATH_INFO", "/") or "/")
        query = environ.get("QUERY_STRING", "")
        target = f"https://{host}:{https_port}{path}" + (f"?{query}" if query else "")
        start_response(
            "301 Moved Permanently",
            [("Location", target), ("Content-Type", "text/plain"), ("Content-Length", "0")],
        )
        return [b""]

    return app
