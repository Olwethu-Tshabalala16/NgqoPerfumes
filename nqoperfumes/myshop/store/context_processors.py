import os


VALID_THEMES = {"light", "dark"}


def theme(request):
    owner_theme = os.getenv("SITE_THEME", "").strip().lower()
    if owner_theme not in VALID_THEMES:
        owner_theme = None

    locked = owner_theme is not None and os.getenv("SITE_THEME_LOCK") == "1"
    visitor_theme = request.COOKIES.get("theme", "")

    if locked:
        selected_theme = owner_theme
    elif visitor_theme == "system":
        selected_theme = None
    elif visitor_theme in VALID_THEMES:
        selected_theme = visitor_theme
    else:
        selected_theme = owner_theme

    return {
        "site_theme": selected_theme,
        "site_theme_locked": locked,
    }
