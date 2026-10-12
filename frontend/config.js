/*
 * Set CATALOGUE_JSON_URL to the public URL of catalogue/products.json in your
 * Supabase Storage bucket for deployments. Leave it empty only for local
 * development, where the frontend falls back to the Django JSON API.
 */
window.NQO_CONFIG = {
  CATALOGUE_JSON_URL: "",
  API_BASE_URL: "http://127.0.0.1:8000"
};
