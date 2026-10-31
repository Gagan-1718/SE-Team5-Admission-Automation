(function () {
  "use strict";

  const root = document.querySelector(".choices-page");
  if (!root) return;

  const state = { choices: [], locked: false, loading: true, busy: false };
  const eligible = root.dataset.eligible === "true";
  const list = document.getElementById("choice-list");
  const feedback = document.getElementById("choices-feedback");
  const error = document.getElementById("choices-error");
  const lockStatus = document.getElementById("choice-lock-status");
  const lockButton = document.getElementById("lock-choices");
  const dialog = document.getElementById("lock-dialog");
  const confirmLock = document.getElementById("confirm-lock");

  function showFeedback(message) {
    feedback.textContent = message || "";
    error.hidden = true;
    error.textContent = "";
  }

  function showError(message) {
    error.textContent = message || "The request could not be completed.";
    error.hidden = false;
    feedback.textContent = "";
  }

  async function request(url, options) {
    let response;
    try {
      response = await fetch(url, options);
    } catch (networkError) {
      throw new Error("Network error. Check your connection and try again.");
    }
    let payload = {};
    try {
      payload = await response.json();
    } catch (parseError) {
      payload = {};
    }
    if (!response.ok) {
      if (response.status === 401) throw new Error("Your session has expired. Please log in again.");
      throw new Error(payload.message || "The request could not be completed.");
    }
    return payload;
  }

  function setLockStatus() {
    lockStatus.className = "pill " + (state.locked ? "ok" : "info");
    lockStatus.textContent = state.locked ? "Locked" : "List open";
    lockButton.disabled = !eligible || state.locked || state.busy || state.choices.length === 0;
    lockButton.textContent = state.locked ? "Choices locked" : "Lock choices";
  }

  function setAddButtons() {
    document.querySelectorAll("[data-choice-add]").forEach(function (button) {
      button.disabled = !eligible || state.locked || state.busy;
    });
  }

  function announce(message) {
    showFeedback(message);
  }

  function renderChoices() {
    list.setAttribute("aria-busy", state.loading ? "true" : "false");
    if (state.loading) {
      list.innerHTML = '<p class="loading-state">Loading your saved choices…</p>';
      setLockStatus();
      setAddButtons();
      return;
    }
    if (!state.choices.length) {
      list.innerHTML = '<p class="empty-state">No choices saved yet. Add a branch from the catalogue.</p>';
      setLockStatus();
      setAddButtons();
      return;
    }
    const items = state.choices.map(function (choice, index) {
      const upDisabled = state.locked || state.busy || index === 0;
      const downDisabled = state.locked || state.busy || index === state.choices.length - 1;
      return '<li class="saved-choice" data-choice-id="' + choice.id + '">' +
        '<span class="choice-priority" aria-label="Priority ' + choice.priority + '">' + choice.priority + '</span>' +
        '<div class="choice-details"><strong>' + escapeHtml(choice.branch) + '</strong>' +
        '<span>' + escapeHtml(choice.college) + ' · ' + escapeHtml(choice.city || "City not provided") + '</span>' +
        '<span>' + choice.seatsAvailable + ' ' + escapeHtml(choice.category || "category") + ' seats left</span></div>' +
        '<div class="choice-actions">' +
        '<button class="btn ghost sm" type="button" data-move="up" aria-label="Move ' + escapeHtml(choice.branch) + ' up" ' + (upDisabled ? "disabled" : "") + '>Up</button>' +
        '<button class="btn ghost sm" type="button" data-move="down" aria-label="Move ' + escapeHtml(choice.branch) + ' down" ' + (downDisabled ? "disabled" : "") + '>Down</button>' +
        '<button class="btn danger sm" type="button" data-remove aria-label="Remove ' + escapeHtml(choice.branch) + '" ' + (state.locked || state.busy ? "disabled" : "") + '>Remove</button>' +
        '</div></li>';
    }).join("");
    list.innerHTML = '<ol class="choice-list">' + items + '</ol>';
    list.querySelectorAll("[data-move]").forEach(function (button, index) {
      button.addEventListener("click", function () {
        const row = button.closest(".saved-choice");
        moveChoice(Number(row.dataset.choiceId), button.dataset.move === "up" ? -1 : 1);
      });
    });
    list.querySelectorAll("[data-remove]").forEach(function (button) {
      button.addEventListener("click", function () {
        removeChoice(Number(button.closest(".saved-choice").dataset.choiceId));
      });
    });
    setLockStatus();
    setAddButtons();
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character];
    });
  }

  async function loadChoices() {
    state.loading = true;
    renderChoices();
    try {
      const payload = await request(root.dataset.listUrl);
      state.choices = payload.choices || [];
      state.locked = Boolean(payload.locked);
      state.loading = false;
      renderChoices();
    } catch (requestError) {
      state.loading = false;
      list.innerHTML = '<p class="empty-state">Your choices could not be loaded.</p>';
      showError(requestError.message);
      setLockStatus();
      setAddButtons();
    }
  }

  async function addChoice(button) {
    state.busy = true;
    setAddButtons();
    try {
      await request(root.dataset.addUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collegeId: Number(button.dataset.collegeId),
          branchId: Number(button.dataset.branchId)
        })
      });
      showFeedback("Choice added to your list.");
      await loadChoices();
    } catch (requestError) {
      showError(requestError.message);
    } finally {
      state.busy = false;
      renderChoices();
    }
  }

  async function removeChoice(choiceId) {
    state.busy = true;
    renderChoices();
    try {
      await request("/api/v1/choices/" + choiceId, { method: "DELETE" });
      showFeedback("Choice removed. Your priorities were updated.");
      await loadChoices();
    } catch (requestError) {
      showError(requestError.message);
    } finally {
      state.busy = false;
      renderChoices();
    }
  }

  async function moveChoice(choiceId, offset) {
    const index = state.choices.findIndex(function (choice) { return choice.id === choiceId; });
    const target = index + offset;
    if (index < 0 || target < 0 || target >= state.choices.length || state.locked || state.busy) return;
    const previous = state.choices.slice();
    const next = state.choices.slice();
    const moved = next.splice(index, 1)[0];
    next.splice(target, 0, moved);
    next.forEach(function (choice, position) { choice.priority = position + 1; });
    state.choices = next;
    state.busy = true;
    renderChoices();
    announce("Moved " + moved.branch + " to position " + (target + 1) + ".");
    try {
      await request("/api/v1/choices/order", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orderedChoiceIds: next.map(function (choice) { return choice.id; }) })
      });
      showFeedback("Choice order saved.");
    } catch (requestError) {
      state.choices = previous;
      renderChoices();
      showError(requestError.message);
    } finally {
      state.busy = false;
      renderChoices();
    }
  }

  async function confirmLockRequest() {
    confirmLock.disabled = true;
    state.busy = true;
    try {
      const payload = await request(root.dataset.lockUrl, { method: "POST" });
      state.locked = true;
      dialog.close();
      showFeedback("Choices locked on " + new Date(payload.lockedAt).toLocaleString() + ". This order is final.");
      renderChoices();
    } catch (requestError) {
      showError(requestError.message);
    } finally {
      state.busy = false;
      confirmLock.disabled = false;
      renderChoices();
    }
  }

  document.querySelectorAll("[data-choice-add]").forEach(function (button) {
    button.addEventListener("click", function () { addChoice(button); });
  });
  lockButton.addEventListener("click", function () { dialog.showModal(); });
  confirmLock.addEventListener("click", confirmLockRequest);
  document.querySelector("[data-close-lock]").addEventListener("click", function () { dialog.close(); });
  loadChoices();
}());
