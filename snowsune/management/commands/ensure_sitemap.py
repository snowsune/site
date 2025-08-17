from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
from apps.blog.models import BlogPost
from apps.comics.models import ComicPage

import os


class Command(BaseCommand):
    help = "Generate XML sitemap for SEO"

    def handle(self, *args, **options):
        sitemap_path = "static/sitemap.xml"

        # Check if sitemap exists and is fresh
        if os.path.exists(sitemap_path):
            file_time = os.path.getmtime(sitemap_path)
            file_age = timezone.now() - timezone.datetime.fromtimestamp(
                file_time, tz=dt_timezone.utc
            )

            if file_age < timedelta(hours=24):
                self.stdout.write(
                    self.style.SUCCESS("Sitemap is fresh (less than 24 hours old)")
                )
                return

        # Generate fresh sitemap
        self.stdout.write("Generating fresh sitemap...")

        try:
            # Hardcode domain since we don't have Sites framework
            domain = "snowsune.net"

            # Build sitemap content
            sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <!-- Home page -->
    <url>
        <loc>https://{domain}/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    
    <!-- Tools page -->
    <url>
        <loc>https://{domain}/tools/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <!-- Blog landing -->
    <url>
        <loc>https://{domain}/blog/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    
    <!-- Comics home -->
    <url>
        <loc>https://{domain}/comics/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <!-- Characters -->
    <url>
        <loc>https://{domain}/characters/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.7</priority>
    </url>
    
    <!-- Character pages -->
    <url>
        <loc>https://{domain}/characters/vixi-argorrok/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
    
    <url>
        <loc>https://{domain}/characters/rhettan/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>"""

            # Add blog posts
            for post in BlogPost.objects.filter(status="published"):
                sitemap_content += f"""
    <url>
        <loc>https://{domain}{post.get_absolute_url()}</loc>
        <lastmod>{post.updated_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>"""

            # Add comic pages
            for page in ComicPage.objects.all():
                sitemap_content += f"""
    <url>
        <loc>https://{domain}{page.get_absolute_url()}</loc>
        <lastmod>{page.updated_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>"""

            # Close the sitemap
            sitemap_content += """
</urlset>"""

            # Write to static directory
            static_dir = "static"
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)

            with open(sitemap_path, "w", encoding="utf-8") as f:
                f.write(sitemap_content)

            self.stdout.write(
                self.style.SUCCESS(f"Successfully generated sitemap at {sitemap_path}")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to generate sitemap: {e}"))
