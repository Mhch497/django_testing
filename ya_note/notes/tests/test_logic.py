from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

from pytils.translit import slugify

User = get_user_model()

class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.success_url = reverse('notes:success')

    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        assert Note.objects.count() == 1
        new_note = Note.objects.get()
        assert new_note.title == self.form_data['title']
        assert new_note.text == self.form_data['text']
        assert new_note.slug == self.form_data['slug']
        assert new_note.author == self.author

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        assert Note.objects.count() == 0

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.note = Note.objects.create(**self.form_data,
                                        author=self.author)
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)
        self.assertFormError(response, 'form', 'slug',
                             errors=(self.note.slug + WARNING))
        assert Note.objects.count() == 1

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, self.success_url) 
        assert Note.objects.count() == 1
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        assert new_note.slug == expected_slug

class TestNoteEditDelete(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.note = Note.objects.create(title='Заголовок',
                                       text='Текст',
                                       slug='text',
                                       author=cls.author)
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')


    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        assert self.note.title == self.form_data['title']
        assert self.note.text == self.form_data['text']
        assert self.note.slug == self.form_data['slug']

    def test_other_user_cant_edit_note(self):
        response = self.not_author_client.post(self.edit_url, self.form_data)
        assert response.status_code == HTTPStatus.NOT_FOUND
        note_from_db = Note.objects.get(id=self.note.id)
        assert self.note.title == note_from_db.title
        assert self.note.text == note_from_db.text
        assert self.note.slug == note_from_db.slug

    def test_author_can_delete_note(self):
        response = self.author_client.post(self.delete_url)
        self.assertRedirects(response, self.success_url)
        assert Note.objects.count() == 0


    def test_other_user_cant_delete_note(self):
        response = self.not_author_client.post(self.delete_url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Note.objects.count() == 1
