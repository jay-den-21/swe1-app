from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Choice, Question


class PollsViewTests(TestCase):
    def setUp(self):
        self.question = Question.objects.create(
            question_text="Which language?", pub_date=timezone.now() - timedelta(days=1)
        )
        self.choice = self.question.choice_set.create(choice_text="Python", votes=2)
        self.vote_url = reverse("polls:vote", args=[self.question.pk])

    def test_index_shows_published_questions_and_excludes_future_questions(self):
        future_question = Question.objects.create(
            question_text="A future question", pub_date=timezone.now() + timedelta(days=1)
        )
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, self.question.question_text)
        self.assertNotContains(response, future_question.question_text)

    def test_index_has_empty_state(self):
        Question.objects.all().delete()
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")

    def test_detail_displays_question_choices_and_form(self):
        response = self.client.get(reverse("polls:detail", args=[self.question.pk]))
        self.assertContains(response, self.question.question_text)
        self.assertContains(response, self.choice.choice_text)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, self.vote_url)

    def test_unknown_question_returns_404(self):
        response = self.client.get(reverse("polls:detail", args=[self.question.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_vote_increments_and_redirects_to_results(self):
        response = self.client.post(self.vote_url, {"choice": self.choice.pk})
        self.assertRedirects(response, reverse("polls:results", args=[self.question.pk]))
        self.choice.refresh_from_db()
        self.assertEqual(self.choice.votes, 3)
        results = self.client.get(response.url)
        self.assertContains(results, "Python &mdash; 3 votes")

    def test_missing_or_invalid_choice_displays_error_without_changing_votes(self):
        for data in ({}, {"choice": "invalid"}, {"choice": self.choice.pk + 100}):
            with self.subTest(data=data):
                response = self.client.post(self.vote_url, data)
                self.assertContains(response, "You didn&#x27;t select a choice.")
                self.choice.refresh_from_db()
                self.assertEqual(self.choice.votes, 2)

    def test_choice_from_another_question_cannot_be_used(self):
        other_question = Question.objects.create(
            question_text="Another question", pub_date=timezone.now()
        )
        other_choice = other_question.choice_set.create(choice_text="Other")
        response = self.client.post(self.vote_url, {"choice": other_choice.pk})
        self.assertContains(response, "You didn&#x27;t select a choice.")
        other_choice.refresh_from_db()
        self.assertEqual(other_choice.votes, 0)

    def test_vote_requires_post(self):
        response = self.client.get(self.vote_url)
        self.assertEqual(response.status_code, 405)
        self.choice.refresh_from_db()
        self.assertEqual(self.choice.votes, 2)

    def test_vote_requires_valid_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        rejected = client.post(self.vote_url, {"choice": self.choice.pk})
        self.assertEqual(rejected.status_code, 403)
        client.get(reverse("polls:detail", args=[self.question.pk]))
        accepted = client.post(
            self.vote_url,
            {"choice": self.choice.pk, "csrfmiddlewaretoken": client.cookies["csrftoken"].value},
        )
        self.assertEqual(accepted.status_code, 302)
        self.choice.refresh_from_db()
        self.assertEqual(self.choice.votes, 3)


class SeedPollsTests(TestCase):
    def test_repeated_seeding_preserves_questions_choices_and_votes(self):
        call_command("seed_polls", stdout=StringIO())
        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Choice.objects.count(), 8)
        choice = Choice.objects.first()
        choice.votes = 7
        choice.save()
        question_dates = list(Question.objects.values_list("id", "pub_date"))

        call_command("seed_polls", stdout=StringIO())

        self.assertEqual(Question.objects.count(), 2)
        self.assertEqual(Choice.objects.count(), 8)
        self.assertEqual(list(Question.objects.values_list("id", "pub_date")), question_dates)
        choice.refresh_from_db()
        self.assertEqual(choice.votes, 7)
