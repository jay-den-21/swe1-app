from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from polls.models import Question


class Command(BaseCommand):
    help = "Create example polls without resetting existing questions or votes."

    @transaction.atomic
    def handle(self, *args, **options):
        examples = [
            (
                "What's your favorite programming language?",
                ["Python", "Java", "JavaScript", "C++"],
            ),
            (
                "Which part of building a web app do you enjoy most?",
                ["Writing code", "Designing the interface", "Testing", "Deployment"],
            ),
        ]
        created_questions = 0
        created_choices = 0
        for question_text, choices in examples:
            question, created = Question.objects.get_or_create(
                question_text=question_text,
                defaults={"pub_date": timezone.now() - timedelta(days=1)},
            )
            created_questions += created
            for choice_text in choices:
                _, created = question.choice_set.get_or_create(choice_text=choice_text)
                created_choices += created

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_questions} questions and {created_choices} choices. "
                "Existing votes were preserved."
            )
        )
