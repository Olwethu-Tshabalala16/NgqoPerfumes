(() => {
  "use strict";

  function addPasswordToggle() {
    const passwordInput = document.querySelector(
      'body.login input[type="password"], #login-form input[name="password"]'
    );

    if (!passwordInput || passwordInput.dataset.visibilityToggleAdded === "true") {
      return;
    }

    passwordInput.dataset.visibilityToggleAdded = "true";

    const wrapper = document.createElement("div");
    wrapper.className = "nqo-password-field";
    passwordInput.parentNode.insertBefore(wrapper, passwordInput);
    wrapper.appendChild(passwordInput);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "nqo-password-toggle";
    toggle.setAttribute("aria-label", "Show password");
    toggle.setAttribute("aria-pressed", "false");
    toggle.setAttribute("aria-controls", passwordInput.id || "id_password");
    toggle.innerHTML = '<span aria-hidden="true">👁</span>';
    wrapper.appendChild(toggle);

    toggle.addEventListener("click", () => {
      const shouldShow = passwordInput.type === "password";
      passwordInput.type = shouldShow ? "text" : "password";
      toggle.setAttribute("aria-label", shouldShow ? "Hide password" : "Show password");
      toggle.setAttribute("aria-pressed", String(shouldShow));
      toggle.innerHTML = shouldShow
        ? '<span aria-hidden="true">🙈</span>'
        : '<span aria-hidden="true">👁</span>';
      passwordInput.focus({ preventScroll: true });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", addPasswordToggle, { once: true });
  } else {
    addPasswordToggle();
  }
})();
