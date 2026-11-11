"""Search-engine discovery endpoints for the public Ngqo Enterprises site."""

from django.http import HttpResponse

SITE_URL = "https://ngqoperfumes.vercel.app"


def sitemap_xml(request):
    """Publish the canonical public homepage in the XML sitemap.

    Product detail pages are not currently addressable by unique URLs: the
    catalogue and product detail dialog are rendered by the homepage JavaScript.
    Therefore, do not publish API endpoints or fabricated product URLs here.
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{SITE_URL}/</loc>
  </url>
</urlset>
"""
    response = HttpResponse(xml, content_type="application/xml; charset=utf-8")
    response["Cache-Control"] = "public, max-age=3600"
    return response


def robots_txt(request):
    """Allow public pages and catalogue data while keeping admin/API paths private."""
    content = f"""User-agent: *
Allow: /
Allow: /api/products/
Disallow: /admin/
Disallow: /api/

Sitemap: {SITE_URL}/sitemap.xml
"""
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Cache-Control"] = "public, max-age=3600"
    return response
