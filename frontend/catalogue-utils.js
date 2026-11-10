(function attachCatalogueUtils(root) {
  "use strict";

  function formatPrice(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount)) return `R ${value}`;

    return new Intl.NumberFormat("en-ZA", {
      style: "currency",
      currency: "ZAR"
    }).format(amount);
  }

  function filterProducts(products, query) {
    const normalizedQuery = String(query ?? "").trim().toLocaleLowerCase();

    return products.filter((product) => {
      const searchable = `${product.name || ""} ${product.description || ""}`.toLocaleLowerCase();
      return searchable.includes(normalizedQuery);
    });
  }

  function hasProductImage(product) {
    return typeof product?.image_url === "string" && product.image_url.trim().length > 0;
  }

  const utilities = Object.freeze({
    formatPrice,
    filterProducts,
    hasProductImage
  });

  if (root) root.NGQO_CATALOGUE_UTILS = utilities;
  if (typeof module !== "undefined" && module.exports) module.exports = utilities;
})(typeof window !== "undefined" ? window : null);
