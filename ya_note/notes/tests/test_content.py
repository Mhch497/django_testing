from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       slug='text',
                                       author=cls.author)
        cls.urls = (
            ('notes:add', None),
            ('notes:edit', (cls.note.slug,))
        )

    def test_notes_list_for_different_users(self):
        users_note_in_list = (
            (self.author, True),
            (self.not_author, False),
        )
        for user, note_in_list in users_note_in_list:
            self.client.force_login(user)
            with self.subTest(user=user):
                url = reverse('notes:list')
                response = self.client.get(url)
                object_list = response.context['object_list']
                self.assertEqual(self.note in object_list, note_in_list)

    def test_authorized_client_has_form(self):
        for url, args in self.urls:
            self.client.force_login(self.author)
            with self.subTest(url=url, args=args):
                url = reverse(url, args=args)
                response = self.client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
