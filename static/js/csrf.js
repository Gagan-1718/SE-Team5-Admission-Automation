/* Load before page scripts. Only attach our token to same-origin writes. */
(() => {
  "use strict";
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const request = input instanceof Request ? input : null;
    const url = new URL(request ? request.url : input, document.baseURI);
    const method = String(init.method || (request && request.method) || "GET").toUpperCase();
    if (url.origin !== window.location.origin || !["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      return originalFetch(input, init);
    }
    const token = document.querySelector('meta[name="csrf-token"]');
    const headers = new Headers(init.headers !== undefined ? init.headers : request ? request.headers : undefined);
    if (token && token.content) headers.set("X-CSRF-Token", token.content);
    return originalFetch(input, {...init, headers});
  };
})();
