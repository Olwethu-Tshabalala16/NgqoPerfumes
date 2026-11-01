(() => {
  "use strict";

  const storageKey = "theme";
  const root = document.documentElement;
  const toggle = document.querySelectorAll("[data-theme-toggle]");
  const reset = document.querySelectorAll("[data-theme-reset]");
  const systemQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const locked = Array.from(toggle).some(
    (button) => button.dataset.themeLocked === "true"
  );

  function getSavedTheme() {
    try {
      const value = localStorage.getItem(storageKey);
      return ["light", "dark", "system"].includes(value) ? value : null;
    } catch {
      return null;
    }
  }

  function saveTheme(value) {
    try {
      if (value) localStorage.setItem(storageKey, value);
      else localStorage.removeItem(storageKey);
    } catch {
      // The cookie still keeps the preference available to the server.
    }

    document.cookie = value
      ? `theme=${value}; path=/; max-age=31536000; SameSite=Lax`
      : "theme=; path=/; max-age=0; SameSite=Lax";
  }

  function resolvedTheme() {
    if (locked && root.dataset.theme) return root.dataset.theme;
    const saved = getSavedTheme();
    if (saved === "light" || saved === "dark") return saved;
    if (saved === "system" || !root.dataset.theme) {
      return systemQuery.matches ? "dark" : "light";
    }
    return root.dataset.theme;
  }

  function render() {
    const saved = getSavedTheme();
    if (!locked && saved === "system") {
      root.removeAttribute("data-theme");
    } else if (!locked && (saved === "light" || saved === "dark")) {
      root.dataset.theme = saved;
    }

    const isDark = resolvedTheme() === "dark";
    toggle.forEach((button) => {
      button.setAttribute("aria-pressed", String(isDark));
      button.setAttribute(
        "aria-label",
        isDark ? "Switch to light mode" : "Switch to dark mode"
      );
      const icon = button.querySelector("[data-theme-icon]");
      if (icon) icon.textContent = isDark ? "☼" : "☾";
    });
    reset.forEach((button) => {
      button.hidden = locked || !saved || saved === "system";
    });
  }

  function setTheme(value, origin) {
    if (locked) return;

    const apply = () => {
      saveTheme(value);
      render();
    };

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    if (!document.startViewTransition || reduceMotion) {
      apply();
      return;
    }

    const button = origin || toggle[0];
    if (!button) {
      apply();
      return;
    }

    const rect = button.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    const radius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    );
    const transition = document.startViewTransition(apply);
    transition.ready.then(() => {
      root.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${radius}px at ${x}px ${y}px)`
          ]
        },
        {
          duration: 500,
          easing: "ease-in-out",
          pseudoElement: "::view-transition-new(root)"
        }
      );
    });
  }

  toggle.forEach((button) => {
    button.addEventListener("click", () => {
      setTheme(resolvedTheme() === "dark" ? "light" : "dark", button);
    });
  });
  reset.forEach((button) => {
    button.addEventListener("click", () => setTheme("system", button));
  });

  const onSystemChange = () => {
    if (!getSavedTheme() || getSavedTheme() === "system") render();
  };
  if (systemQuery.addEventListener) {
    systemQuery.addEventListener("change", onSystemChange);
  } else {
    systemQuery.addListener(onSystemChange);
  }

  window.addEventListener("storage", (event) => {
    if (event.key === storageKey) render();
  });

  render();
  requestAnimationFrame(() => {
    requestAnimationFrame(() => root.classList.add("theme-ready"));
  });
})();
