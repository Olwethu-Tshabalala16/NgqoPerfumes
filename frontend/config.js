/*
 * The frontend and Django API share one origin in production and when using
 * Django's runserver locally. A build may populate CATALOGUE_JSON_URL to read
 * the published Supabase catalogue snapshot directly.
 */
window.NQO_CONFIG = {
  CATALOGUE_JSON_URL: "",
  API_BASE_URL: ""
};
