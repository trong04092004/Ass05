from django.core.management.base import BaseCommand
from urllib.parse import quote_plus

from app.models import Book


def cover_url_from_isbn(isbn: str, size: str = "L") -> str:
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg"


def cover_url_from_title(title: str) -> str:
    encoded_title = quote_plus(title)
    return f"https://placehold.co/600x900/0f172a/f8fafc?text={encoded_title}"


class Command(BaseCommand):
    help = "Backfill image_url for books using Open Library covers by ISBN."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing image_url values.",
        )
        parser.add_argument(
            "--size",
            default="L",
            choices=["S", "M", "L"],
            help="Open Library cover size: S, M, or L.",
        )
        parser.add_argument(
            "--provider",
            default="titlecard",
            choices=["titlecard", "openlibrary"],
            help="Cover source provider: titlecard (recommended) or openlibrary.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        size = options["size"]
        provider = options["provider"]

        scanned = 0
        updated = 0
        skipped_no_isbn = 0
        skipped_existing = 0

        for book in Book.objects.all().iterator():
            scanned += 1
            isbn = (book.isbn or "").strip()
            if provider == "openlibrary":
                if not isbn:
                    skipped_no_isbn += 1
                    continue
                new_url = cover_url_from_isbn(isbn, size=size)
            else:
                new_url = cover_url_from_title(book.title)

            if book.image_url and not force:
                skipped_existing += 1
                continue

            if book.image_url == new_url:
                skipped_existing += 1
                continue

            book.image_url = new_url
            book.save(update_fields=["image_url"])
            updated += 1

        self.stdout.write(self.style.SUCCESS("Backfill completed."))
        self.stdout.write(f"Scanned: {scanned}")
        self.stdout.write(f"Updated: {updated}")
        self.stdout.write(f"Skipped (no ISBN): {skipped_no_isbn}")
        self.stdout.write(f"Skipped (already has image): {skipped_existing}")
