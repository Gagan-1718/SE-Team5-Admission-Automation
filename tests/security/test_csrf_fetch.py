"""Execute the fetch wrapper against browser-like Request/Headers objects."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_fetch_wrapper_keeps_tokens_on_same_origin_writes_only():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required only for the JavaScript runtime regression check")
    wrapper = Path("static/js/csrf.js").resolve()
    script = r"""
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const calls = [];
const window = {
    location: {origin: "https://admission.test"},
    fetch(input, options) { calls.push({input, options}); return Promise.resolve({ok: true}); },
};
const document = {
    baseURI: "https://admission.test/accounts/profile-page",
    querySelector() { return {content: "session-token"}; },
};
vm.runInNewContext(fs.readFileSync(process.argv[1], "utf8"), {window, document, URL, Request, Headers});
for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    window.fetch("/api/test", {method, headers: {"Content-Type": "application/json"}, body: "{}"});
    const call = calls.pop();
    assert.equal(call.options.headers.get("X-CSRF-Token"), "session-token");
    assert.equal(call.options.headers.get("Content-Type"), "application/json");
    assert.equal(call.options.body, "{}");
}
for (const method of ["GET", "HEAD"]) {
    const options = {method};
    window.fetch("/api/test", options);
    assert.equal(calls.pop().options, options);
}
const crossOrigin = {method: "POST", headers: {"X-Test": "external"}};
window.fetch("https://another.test/collect", crossOrigin);
assert.equal(calls.pop().options, crossOrigin);
const request = new Request("https://admission.test/api/test", {
    method: "POST", headers: {"X-Test": "preserved"}, body: "content",
});
window.fetch(request);
const call = calls.pop();
assert.equal(call.input, request);
assert.equal(call.options.headers.get("X-Test"), "preserved");
assert.equal(call.options.headers.get("X-CSRF-Token"), "session-token");
window.fetch(new Request("https://admission.test/api/test"), {method: "DELETE"});
assert.equal(calls.pop().options.headers.get("X-CSRF-Token"), "session-token");
"""
    result = subprocess.run([node, "-e", script, str(wrapper)], capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
