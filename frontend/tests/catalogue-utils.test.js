const assert = require("node:assert/strict");
const test = require("node:test");

const {
  filterProducts,
  formatPrice,
  hasProductImage
} = require("../catalogue-utils.js");

test("formatPrice formats numeric values as South African rand", () => {
  const formatted = formatPrice("249.99");

  assert.match(formatted, /R/);
  assert.match(formatted, /249/);
});

test("formatPrice gives a readable fallback for non-numeric values", () => {
  assert.equal(formatPrice("price unavailable"), "R price unavailable");
});

test("filterProducts matches names without case sensitivity", () => {
  const products = [
    { id: 1, name: "Amber Oud", description: "Warm woody notes" },
    { id: 2, name: "Rose Musk", description: "Soft floral notes" }
  ];

  assert.deepEqual(filterProducts(products, "AMBER"), [products[0]]);
});

test("filterProducts also searches product descriptions", () => {
  const products = [
    { id: 1, name: "Amber Oud", description: "Warm woody notes" },
    { id: 2, name: "Rose Musk", description: "Soft floral notes" }
  ];

  assert.deepEqual(filterProducts(products, "FLORAL"), [products[1]]);
});

test("filterProducts returns every product for an empty query", () => {
  const products = [{ id: 1, name: "Amber Oud" }, { id: 2, name: "Rose Musk" }];

  assert.deepEqual(filterProducts(products, "   "), products);
});

test("hasProductImage rejects missing and blank image URLs", () => {
  assert.equal(hasProductImage({ image_url: null }), false);
  assert.equal(hasProductImage({ image_url: "   " }), false);
  assert.equal(hasProductImage({}), false);
});

test("hasProductImage accepts a valid image URL", () => {
  assert.equal(hasProductImage({ image_url: "https://cdn.example.test/amber.jpg" }), true);
});
