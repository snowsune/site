from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.comics.models import ComicPage

User = get_user_model()


class Command(BaseCommand):
    help = "Create blog posts for existing comic pages that don't have them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            type=str,
            help="Username of the user to create blog posts as",
        )

    def handle(self, *args, **options):
        # Get or create a user to create blog posts as
        if options["user"]:
            try:
                user = User.objects.get(username=options["user"])
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{options["user"]}" does not exist')
                )
                return
        else:
            # Use the first superuser, or create a default user
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
                if not user:
                    self.stdout.write(self.style.ERROR("No users found in the system"))
                    return

        # Find comic pages without blog posts
        pages_without_posts = ComicPage.objects.filter(blog_post__isnull=True)

        if not pages_without_posts.exists():
            self.stdout.write(
                self.style.SUCCESS("All comic pages already have blog posts!")
            )
            return

        self.stdout.write(
            f"Creating blog posts for {pages_without_posts.count()} comic pages..."
        )

        created_count = 0
        for page in pages_without_posts:
            try:
                blog_post = page.create_blog_post(user)
                self.stdout.write(
                    f'Created blog post "{blog_post.title}" for page {page.page_number}'
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to create blog post for page {page.page_number}: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} blog posts!")
        )
