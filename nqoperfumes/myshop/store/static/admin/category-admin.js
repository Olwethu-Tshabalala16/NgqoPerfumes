(() => {
  "use strict";

  const categorySelect = document.querySelector("#id_category");
  const guide = document.querySelector(".nqo-product-guide[data-add-category-url]");
  const dialog = document.querySelector("#nqo-category-dialog");
  const form = document.querySelector("#nqo-category-form");
  const nameInput = document.querySelector("#nqo-category-name");
  const errorMessage = document.querySelector("#nqo-category-error");
  const saveButton = document.querySelector("#nqo-category-save");
  const cancelButton = document.querySelector("#nqo-category-cancel");

  if (!categorySelect || !guide || !dialog || !form) return;

  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "button nqo-add-category";
  addButton.textContent = "+ Add Section";
  addButton.setAttribute("aria-haspopup", "dialog");
  categorySelect.insertAdjacentElement("afterend", addButton);

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.hidden = false;
  }

  function closeDialog() {
    dialog.close();
    form.reset();
    errorMessage.hidden = true;
    errorMessage.textContent = "";
  }

  addButton.addEventListener("click", () => {
    dialog.showModal();
    nameInput.focus();
  });
  cancelButton.addEventListener("click", closeDialog);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = nameInput.value.trim();
    if (!name) {
      showError("Enter a category name.");
      nameInput.focus();
      return;
    }

    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfInput) {
      showError("The security token is missing. Refresh the page and try again.");
      return;
    }

    saveButton.disabled = true;
    saveButton.textContent = "Adding…";
    errorMessage.hidden = true;

    try {
      const response = await fetch(guide.dataset.addCategoryUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
          "X-CSRFToken": csrfInput.value,
          "Accept": "application/json"
        },
        body: new URLSearchParams({ name })
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "The category could not be created.");

      let option = [...categorySelect.options].find((item) => item.value === String(payload.id));
      if (!option) {
        option = new Option(payload.name, payload.id);
        categorySelect.add(option);
      }
      categorySelect.value = String(payload.id);
      categorySelect.dispatchEvent(new Event("change", { bubbles: true }));
      closeDialog();
    } catch (error) {
      showError(error.message || "The category could not be created. Try again.");
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = "Add category";
    }
  });
})();
