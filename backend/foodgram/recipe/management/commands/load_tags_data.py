from csv import DictReader

from django.core.management import BaseCommand
from recipe.models import Tag


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open(
            'data/tags.csv', 'r', encoding='utf-8'
        ) as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                tag = Tag(name=row['name'], color=row['color'],
                          slug=row['slug'])
                tag.save()
