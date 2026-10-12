(() => {
  "use strict";

  const config = window.NQO_CONFIG || {};
  const apiBaseUrl = (config.API_BASE_URL || "").replace(/\/+$/, "");
  const productsEndpoint = `${apiBaseUrl}/api/products/`;
  const catalogueJsonUrl = (config.CATALOGUE_JSON_URL || "").trim();

  const grid = document.querySelector("#product-grid");
  const status = document.querySelector("#catalogue-status");
  const searchInput = document.querySelector("#product-search");
  const year = document.querySelector("#current-year");
  let products = [];

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
    body.append(name, description, footer);
    card.append(imageFrame, body);
    return card;
  }

  function renderProducts(items) {
    grid.replaceChildren();

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
      grid.append(empty);
      return;
    }

    const fragment = document.createDocumentFragment();
    items.forEach((product) => fragment.append(makeProductCard(product)));
    grid.append(fragment);
  }

  function filterProducts() {
    const query = searchInput.value.trim().toLocaleLowerCase();
    const filtered = products.filter((product) => {
      const searchable = `${product.name || ""} ${product.description || ""}`.toLocaleLowerCase();
      return searchable.includes(query);
    });
    renderProducts(filtered);
    if (query) status.textContent = `${filtered.length} matching fragrance${filtered.length === 1 ? "" : "s"}.`;
    else status.textContent = `${products.length} fragrance${products.length === 1 ? "" : "s"} in the collection.`;
  }

  async function loadProducts() {
    status.textContent = "Loading fragrances…";
    grid.replaceChildren();

    try {
      // In production, read the persistent JSON snapshot directly from Supabase.
      // The Django API remains a convenient fallback for local development.
      const response = await fetch(catalogueJsonUrl || productsEndpoint, {
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(`The catalogue service returned HTTP ${response.status}.`);
      }

      const payload = await response.json();
      products = Array.isArray(payload.products)
        ? payload.products
        : (Array.isArray(payload.results) ? payload.results : []);
      filterProducts();
    } catch (error) {
      console.error("Unable to load the product catalogue:", error);
      status.textContent = "The catalogue could not be loaded.";
      const retry = element("button", "retry-button", "Try again");
      retry.type = "button";
      retry.addEventListener("click", loadProducts);
      grid.replaceChildren(
        element("p", "error-message", "Check your connection and the catalogue API configuration, then try again."),
        retry
      );
    }
  }

  searchInput.addEventListener("input", filterProducts);
  loadProducts();
})();
