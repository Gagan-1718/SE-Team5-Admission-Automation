"""HTTPS acceptance checks (issue #4 / SEC-F-004 / TC-024). Fictional data only.

These start the real Cheroot server with a freshly generated self-signed certificate
and talk to it over real sockets. One test records the bytes that cross the network
and proves a password never appears in them; a plain HTTP control proves the recorder
really would see it if the connection were not encrypted.
"""
import datetime
import http.client
import json
import socket
import ssl
import threading
import time

import pytest

pytest.importorskip("cheroot", reason="install requirements-https.txt to run the HTTPS tests")
pytest.importorskip("cryptography", reason="install requirements-https.txt to run the HTTPS tests")

from cryptography import x509  # noqa: E402

from app.tls import (  # noqa: E402
    build_http_server,
    build_https_server,
    make_dev_certificate,
    redirect_app,
)

PASSWORD = "wire-test-secret-4821"
EMAIL = "wire-test@example.test"
REGISTER = {"name": "Wire Test", "email": EMAIL, "mobile": "9123456789", "password": PASSWORD}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Running:
    """A Cheroot server running in a background thread."""

    def __init__(self, server):
        self.server = server
        self.thread = threading.Thread(target=server.safe_start, daemon=True)
        self.thread.start()
        deadline = time.time() + 10
        while not server.ready and time.time() < deadline:
            time.sleep(0.02)
        assert server.ready, "test server did not start"

    def stop(self):
        self.server.stop()
        self.thread.join(timeout=5)


class Recorder:
    """A TCP relay that forwards bytes untouched and keeps a copy: our 'network capture'."""

    def __init__(self, target_port):
        self.target_port = target_port
        self.captured = bytearray()
        self._lock = threading.Lock()
        self._listener = socket.socket()
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(5)
        self.port = self._listener.getsockname()[1]
        self._stopped = False
        threading.Thread(target=self._accept, daemon=True).start()

    def _record(self, data):
        with self._lock:
            self.captured.extend(data)

    def _pump(self, source, destination):
        try:
            while True:
                data = source.recv(65536)
                if not data:
                    break
                self._record(data)
                destination.sendall(data)
        except OSError:
            pass
        finally:
            for sock in (source, destination):
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

    def _accept(self):
        while not self._stopped:
            try:
                client, _ = self._listener.accept()
            except OSError:
                return
            upstream = socket.create_connection(("127.0.0.1", self.target_port))
            threading.Thread(target=self._pump, args=(client, upstream), daemon=True).start()
            threading.Thread(target=self._pump, args=(upstream, client), daemon=True).start()

    def stop(self):
        self._stopped = True
        self._listener.close()

    @property
    def bytes_seen(self):
        with self._lock:
            return bytes(self.captured)


@pytest.fixture(scope="module")
def tls_files(tmp_path_factory):
    return make_dev_certificate(tmp_path_factory.mktemp("certs"))


@pytest.fixture
def https_server(app, tls_files):
    cert, key = tls_files
    port = free_port()
    running = Running(build_https_server(app, cert, key, "127.0.0.1", port))
    yield port
    running.stop()


@pytest.fixture
def http_server(app):
    port = free_port()
    running = Running(build_http_server(app, "127.0.0.1", port))
    yield port
    running.stop()


@pytest.fixture
def trusted_context(tls_files):
    return ssl.create_default_context(cafile=str(tls_files[0]))


def post_json(connection, path, payload):
    body = json.dumps(payload)
    connection.request("POST", path, body=body, headers={"Content-Type": "application/json"})
    response = connection.getresponse()
    response.read()
    return response


# ------------------------------------------------------------------ certificate

def test_certificate_is_created_once_and_reused(tmp_path):
    first = make_dev_certificate(tmp_path)
    contents = first[0].read_bytes()
    second = make_dev_certificate(tmp_path)
    assert second == first
    assert second[0].read_bytes() == contents
    assert first[1].read_bytes().startswith(b"-----BEGIN PRIVATE KEY-----")


def test_certificate_names_localhost_and_is_currently_valid(tls_files):
    certificate = x509.load_pem_x509_certificate(tls_files[0].read_bytes())
    alt_names = certificate.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert "localhost" in alt_names.get_values_for_type(x509.DNSName)
    assert [str(ip) for ip in alt_names.get_values_for_type(x509.IPAddress)] == ["127.0.0.1"]
    now = datetime.datetime.now(datetime.timezone.utc)
    assert certificate.not_valid_before_utc < now < certificate.not_valid_after_utc


# ------------------------------------------------------------------ the server

def test_pages_are_served_over_tls_1_2_or_newer(https_server, trusted_context):
    connection = http.client.HTTPSConnection("localhost", https_server, context=trusted_context)
    connection.request("GET", "/health")
    response = connection.getresponse()
    assert response.status == 200
    assert json.loads(response.read()) == {"status": "ok", "database": "ok"}
    assert connection.sock.version() in ("TLSv1.2", "TLSv1.3")
    assert connection.sock.cipher()[0]  # a negotiated cipher suite
    connection.close()


def test_security_headers_arrive_over_https(https_server, trusted_context):
    connection = http.client.HTTPSConnection("localhost", https_server, context=trusted_context)
    connection.request("GET", "/health")
    response = connection.getresponse()
    response.read()
    assert response.getheader("Strict-Transport-Security").startswith("max-age=")
    assert response.getheader("X-Content-Type-Options") == "nosniff"
    connection.close()


def test_client_that_does_not_trust_the_certificate_is_refused(https_server):
    default_context = ssl.create_default_context()  # does not know our self-signed certificate
    connection = http.client.HTTPSConnection("localhost", https_server, context=default_context)
    with pytest.raises(ssl.SSLCertVerificationError):
        connection.request("GET", "/health")


def test_plain_http_to_the_tls_port_does_not_serve_pages(https_server):
    with socket.create_connection(("127.0.0.1", https_server), timeout=5) as sock:
        sock.sendall(b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        sock.settimeout(5)
        try:
            data = sock.recv(65536)
        except (ConnectionResetError, socket.timeout):
            data = b""
    assert b'"database"' not in data
    assert b"200 OK" not in data


def test_plain_http_requests_are_redirected_to_https(https_server):
    redirect_port = free_port()
    running = Running(build_http_server(redirect_app(https_server), "127.0.0.1", redirect_port))
    try:
        connection = http.client.HTTPConnection("127.0.0.1", redirect_port)
        connection.request("GET", "/application?next=1")
        response = connection.getresponse()
        response.read()
        assert response.status == 301
        assert response.getheader("Location") == f"https://localhost:{https_server}/application?next=1"
    finally:
        running.stop()


def test_login_cookie_is_secure_over_https(https_server, trusted_context):
    connection = http.client.HTTPSConnection("localhost", https_server, context=trusted_context)
    assert post_json(connection, "/accounts/register", REGISTER).status == 201
    response = post_json(
        connection, "/accounts/login", {"identifier": EMAIL, "password": PASSWORD}
    )
    assert response.status == 200
    cookie = response.getheader("Set-Cookie")
    assert "Secure" in cookie and "HttpOnly" in cookie
    connection.close()


# ----------------------------------------------- the 'network capture' (TC-024)

def test_password_and_email_never_appear_in_the_captured_bytes_over_https(
    https_server, trusted_context
):
    recorder = Recorder(https_server)
    try:
        connection = http.client.HTTPSConnection("localhost", recorder.port, context=trusted_context)
        assert post_json(connection, "/accounts/register", REGISTER).status == 201
        assert post_json(
            connection, "/accounts/login", {"identifier": EMAIL, "password": PASSWORD}
        ).status == 200
        connection.close()
        time.sleep(0.3)
    finally:
        recorder.stop()

    captured = recorder.bytes_seen
    assert len(captured) > 500, "the recorder captured nothing, so this test would prove nothing"
    assert PASSWORD.encode() not in captured
    assert EMAIL.encode() not in captured
    assert b"Set-Cookie" not in captured
    assert b"team5_session" not in captured


def test_control_the_same_capture_does_see_the_password_over_plain_http(http_server):
    """Without TLS the recorder reads the password: this proves the HTTPS test above is meaningful."""
    recorder = Recorder(http_server)
    try:
        connection = http.client.HTTPConnection("127.0.0.1", recorder.port)
        assert post_json(connection, "/accounts/register", REGISTER).status == 201
        connection.close()
        time.sleep(0.3)
    finally:
        recorder.stop()

    captured = recorder.bytes_seen
    assert PASSWORD.encode() in captured
    assert EMAIL.encode() in captured
