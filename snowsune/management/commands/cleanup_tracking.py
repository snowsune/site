from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection
from datetime import timedelta
from tracking.models import Visitor


class Command(BaseCommand):
    help = "Clean up old tracking data, keeping only the past 2 days"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=2,
            help="Number of days to keep (default: 2)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        days_to_keep = options["days"]

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Get count of records to be deleted
        old_visitors = Visitor.objects.filter(start_time__lt=cutoff_date)
        count_to_delete = old_visitors.count()

        if count_to_delete == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No visitor records older than {days_to_keep} days found."
                )
            )
            return

        # Show what would be deleted
        self.stdout.write(
            f"Found {count_to_delete} visitor records older than {days_to_keep} days "
            f"(before {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN - No records will be deleted. "
                    "Use --dry-run=False to actually delete records."
                )
            )

            # Show some sample old records
            sample_old = old_visitors.order_by("-start_time")[:5]
            self.stdout.write("\nSample old records that would be deleted:")
            for visitor in sample_old:
                self.stdout.write(
                    f"  - {visitor.ip_address} at {visitor.start_time} "
                    f"(Session: {visitor.session_key[:20]}...)"
                )

            return

        # Confirm deletion
        confirm = input(
            f"\nAre you sure you want to delete {count_to_delete} visitor records? "
            f"This action cannot be undone. Type 'yes' to confirm: "
        )

        if confirm.lower() != "yes":
            self.stdout.write(self.style.WARNING("Operation cancelled."))
            return

        # Perform deletion
        try:
            deleted_count = old_visitors.count()
            old_visitors.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {deleted_count} old visitor records."
                )
            )

            # Show remaining stats
            total_remaining = Visitor.objects.count()
            recent_remaining = Visitor.objects.filter(
                start_time__gte=cutoff_date
            ).count()

            self.stdout.write(
                f"Remaining records: {total_remaining} total, "
                f"{recent_remaining} within {days_to_keep} days"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during deletion: {e}"))
            return

        # Show cleanup recommendations
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("CLEANUP RECOMMENDATIONS:")
        self.stdout.write("=" * 50)
        self.stdout.write("• Consider running this command daily via cron job")
        self.stdout.write("• Monitor database size and performance after cleanup")
        self.stdout.write("• Adjust --days parameter based on your storage needs")
        self.stdout.write("• Consider archiving old data instead of deletion if needed")
