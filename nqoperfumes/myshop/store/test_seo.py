from django.test import TestCase


class SearchEngineDiscoveryTests(TestCase):
    def test_sitemap_returns_valid_xml_with_canonical_homepage(self):
        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/xml; charset=utf-8")
        self.assertIn(
            "<loc>https://ngqoperfumes.vercel.app/</loc>",
            response.content.decode(),
        )
        self.assertIn(
            'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
            response.content.decode(),
        )
        self.assertNotIn("/api/", response.content.decode())

    def test_robots_txt_allows_public_site_and_points_to_sitemap(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        content = response.content.decode()
        self.assertIn("User-agent: *", content)
        self.assertIn("Allow: /", content)
        self.assertIn("Disallow: /admin/", content)
        self.assertIn("Disallow: /api/", content)
        self.assertIn(
            "Sitemap: https://ngqoperfumes.vercel.app/sitemap.xml",
            content,
        )
