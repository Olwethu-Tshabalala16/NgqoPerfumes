(() => {
  "use strict";

  const config = window.NGQO_CONFIG || {};
  const apiBaseUrl = (config.API_BASE_URL || "").replace(/\/+$/, "");
  const productsEndpoint = `${apiBaseUrl}/api/products/`;
  const versionEndpoint = `${apiBaseUrl}/api/products/version/`;
  const catalogueJsonUrl = (config.CATALOGUE_JSON_URL || "").trim();
  const refreshIntervalMs = 15000;

  const grid = document.querySelector("#product-grid");
  const status = document.querySelector("#catalogue-status");
  const searchInput = document.querySelector("#product-search");
  const year = document.querySelector("#current-year");
  const productDialog = document.querySelector("#product-dialog");
  const dialogImage = document.querySelector("#dialog-product-image");
  const dialogName = document.querySelector("#dialog-product-name");
  const dialogDescription = document.querySelector("#dialog-product-description");
  const dialogPrice = document.querySelector("#dialog-product-price");
  const dialogStock = document.querySelector("#dialog-product-stock");
  const dialogClose = document.querySelector("#dialog-close");
  let products = [];
  let catalogueVersion = null;
  let checkingForUpdates = false;

  year.textContent = new Date().getFullYear();

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function formatPrice(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount)) return `R ${value}`;
    return new Intl.NumberFormat("en-ZA", {
      style: "currency",
      currency: "ZAR"
    }).format(amount);
  }

  function makeProductCard(product) {
    const card = element("article", "product-card");
    card.dataset.productId = String(product.id);
    card.dataset.productSignature = JSON.stringify(product);
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-haspopup", "dialog");
    card.setAttribute("aria-label", `View full details for ${product.name || "this fragrance"}`);
    card.addEventListener("click", () => openProductDetails(product));
    card.addEventListener("keydown", (event) => {
      if (event.target !== card) return;
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openProductDetails(product);
      }
    });

    const imageFrame = element("div", "product-image");
    const placeholder = element("span", "image-placeholder", "✳");
    placeholder.setAttribute("aria-hidden", "true");
    imageFrame.append(placeholder);

    if (product.image_url) {
      const image = element("img", "product-photo");
      image.src = product.image_url;
      image.alt = product.name ? `${product.name} fragrance` : "Fragrance product";
      image.loading = "lazy";
      image.decoding = "async";
      image.addEventListener("error", () => {
        image.remove();
        placeholder.hidden = false;
      }, { once: true });
      placeholder.hidden = true;
      imageFrame.append(image);
    }

    const body = element("div", "product-body");
    const name = element("h3", "product-name", product.name || "Untitled fragrance");
    const description = element(
      "p",
      "product-description",
      product.description || "Contact us for more information about this fragrance."
    );
    const footer = element("div", "product-card-footer");
    const price = element("p", "product-price", formatPrice(product.price));
    const available = Boolean(product.is_in_stock);
    const stock = element(
      "span",
      available ? "stock-status in-stock" : "stock-status out-of-stock",
      available ? `In stock · ${product.stock}` : "Out of stock"
    );

    footer.append(price, stock);
    const detailsHint = element("span", "product-details-hint", "Tap to read full description ↗");
    body.append(name, description, detailsHint, footer);
    card.append(imageFrame, body);
    return card;
  }

  function openProductDetails(product) {
    productDialog.dataset.productId = String(product.id);
    dialogName.textContent = product.name || "Untitled fragrance";
    dialogDescription.textContent = product.description || "Contact us for more information about this fragrance.";
    dialogPrice.textContent = formatPrice(product.price);

    const available = Boolean(product.is_in_stock);
    dialogStock.textContent = available ? `In stock · ${product.stock}` : "Out of stock";
    dialogStock.className = available ? "stock-status in-stock" : "stock-status out-of-stock";

    const imagePlaceholder = productDialog.querySelector(".dialog-image-placeholder");
    if (product.image_url) {
      dialogImage.src = product.image_url;
      dialogImage.alt = product.name ? `${product.name} fragrance` : "Fragrance product";
      dialogImage.hidden = false;
      if (imagePlaceholder) imagePlaceholder.hidden = true;
    } else {
      dialogImage.removeAttribute("src");
      dialogImage.alt = "";
      dialogImage.hidden = true;
      if (imagePlaceholder) imagePlaceholder.hidden = false;
    }

    if (!productDialog.open) productDialog.showModal();
  }

  function refreshOpenProductDetails() {
    if (!productDialog.open) return;
    const productId = productDialog.dataset.productId;
    const latestProduct = products.find((product) => String(product.id) === productId);

    if (latestProduct) {
      openProductDetails(latestProduct);
    } else {
      dialogDescription.textContent = "This fragrance is no longer listed in the catalogue.";
      dialogStock.textContent = "No longer listed";
      dialogStock.className = "stock-status out-of-stock";
    }
  }

  dialogClose.addEventListener("click", () => productDialog.close());
  productDialog.addEventListener("click", (event) => {
    if (event.target === productDialog) productDialog.close();
  });

  function renderProducts(items) {
    if (!items.length) {
      const empty = element("div", "empty-state");
      empty.append(
        element("span", "empty-symbol", "✳"),
        element("h3", "", products.length ? "No matching fragrances" : "The collection is being prepared"),
        element(
          "p",
          "",
          products.length
            ? "Try a different search term."
            : "Please check back soon for the latest collection."
        )
      );
      grid.replaceChildren(empty);
      return;
    }

    grid.querySelectorAll(".empty-state, .error-message, .retry-button").forEach((node) => node.remove());
    const existingCards = new Map(
      [...grid.querySelectorAll(".product-card[data-product-id]")]
        .map((card) => [card.dataset.productId, card])
    );

    items.forEach((product, index) => {
      const productId = String(product.id);
      const signature = JSON.stringify(product);
      let card = existingCards.get(productId);

      if (!card || card.dataset.productSignature !== signature) {
        const replacement = makeProductCard(product);
        const hadFocus = card === document.activeElement;

        if (card) {
          card.replaceWith(replacement);
        } else {
          grid.insertBefore(replacement, grid.children[index] || null);
        }

        if (hadFocus) replacement.focus({ preventScroll: true });
        card = replacement;
      }

      existingCards.delete(productId);
      const currentAtIndex = grid.children[index];
      if (currentAtIndex !== card) {
        grid.insertBefore(card, currentAtIndex || null);
      }
    });

    existingCards.forEach((staleCard) => staleCard.remove());
  }

  function filterProducts() {
    const query = searchInput.value.trim().toLocaleLowerCase();
    const filtered = products.filter((product) => {
      const searchable = `${product.name || ""} ${product.description || ""}`.toLocaleLowerCase();
      return searchable.includes(query);
    });

    renderProducts(filtered);
    if (query) {
      status.textContent = `${filtered.length} matching fragrance${filtered.length === 1 ? "" : "s"}.`;
    } else {
      status.textContent = `${products.length} fragrance${products.length === 1 ? "" : "s"} in the collection.`;
    }
  }

  async function fetchCatalogueVersion() {
    const url = new URL(versionEndpoint, window.location.href);
    url.searchParams.set("v", String(Date.now()));
    const response = await fetch(url.toString(), {
      headers: { Accept: "application/json" },
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`The catalogue version service returned HTTP ${response.status}.`);
    }

    const payload = await response.json();
    if (typeof payload.version !== "string") {
      throw new Error("The catalogue version response has an unexpected format.");
    }
    return payload.version;
  }

  async function loadProducts({ silent = false } = {}) {
    if (!silent && products.length === 0) status.textContent = "Loading fragrances…";

    const sources = catalogueJsonUrl
      ? [catalogueJsonUrl, productsEndpoint]
      : [productsEndpoint];
    let lastError = null;

    for (const source of sources) {
      try {
        const catalogueRequestUrl = new URL(source, window.location.href);
        catalogueRequestUrl.searchParams.set("v", String(Date.now()));
        const response = await fetch(catalogueRequestUrl.toString(), {
          headers: { Accept: "application/json" },
          cache: "no-store"
        });

        if (!response.ok) {
          throw new Error(`The catalogue service returned HTTP ${response.status}.`);
        }

        const payload = await response.json();
        const items = Array.isArray(payload.products)
          ? payload.products
          : (Array.isArray(payload.results) ? payload.results : null);

        if (!items) {
          throw new Error("The catalogue response has an unexpected format.");
        }

        products = items;
        filterProducts();
        refreshOpenProductDetails();
        return true;
      } catch (error) {
        lastError = error;
        console.warn(`Catalogue source failed (${source}); trying the next source if available.`, error);
      }
    }

    console.error("Unable to load the product catalogue:", lastError);
    if (!silent && products.length === 0) {
      status.textContent = "The catalogue could not be loaded.";
      const retry = element("button", "retry-button", "Try again");
      retry.type = "button";
      retry.addEventListener("click", () => loadProducts());
      grid.replaceChildren(
        element("p", "error-message", "Check your connection and the catalogue configuration, then try again."),
        retry
      );
    }
    return false;
  }

  async function checkForCatalogueUpdates() {
    if (checkingForUpdates || document.hidden) return;
    checkingForUpdates = true;

    try {
      const latestVersion = await fetchCatalogueVersion();
      if (catalogueVersion === null) {
        catalogueVersion = latestVersion;
      } else if (latestVersion !== catalogueVersion) {
        const refreshed = await loadProducts({ silent: true });
        if (refreshed) catalogueVersion = latestVersion;
      }
    } catch (error) {
      // Keep the last good catalogue visible and retry on the next interval.
      console.warn("Catalogue update check failed; the current catalogue remains available.", error);
    } finally {
      checkingForUpdates = false;
    }
  }

  searchInput.addEventListener("input", filterProducts);

  async function startCatalogue() {
    try {
      catalogueVersion = await fetchCatalogueVersion();
    } catch (error) {
      console.warn("Initial catalogue version check failed; background checks will retry.", error);
    }

    await loadProducts();
    if (catalogueVersion === null) {
      try {
        catalogueVersion = await fetchCatalogueVersion();
      } catch (error) {
        console.warn("Catalogue version is not available yet.", error);
      }
    }
  }

  startCatalogue();
  window.setInterval(checkForCatalogueUpdates, refreshIntervalMs);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) checkForCatalogueUpdates();
  });
})();
