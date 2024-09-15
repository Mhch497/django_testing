import pytest
from pytest_django.asserts import assertRedirects, assertFormError
from http import HTTPStatus

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'


@pytest.fixture
def form_data():
    return {'text': COMMENT_TEXT}


@pytest.fixture
def new_form_data():
    return {'text': NEW_COMMENT_TEXT}


@pytest.fixture
def url_detail(news):
    return reverse('news:detail', args=(news.id,))


@pytest.fixture
def edit_url(comment):
    return reverse('news:edit', args=(comment.id,))


@pytest.fixture
def delete_url(comment):
    return reverse('news:delete', args=(comment.id,))


@pytest.fixture
def url_to_comments(url_detail):
    return url_detail + '#comments'


def test_anonymous_user_cant_create_comment(client, form_data, url_detail):
    client.post(url_detail, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_can_create_comment(author_client,
                                 author,
                                 url_detail,
                                 form_data,
                                 url_to_comments,
                                 news):
    response = author_client.post(url_detail, data=form_data)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, url_detail):
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url_detail, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_edit_comment(
        author_client, edit_url, url_to_comments, new_form_data, comment):
    response = author_client.post(edit_url, data=new_form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT


def test_user_cant_edit_comment_of_another_user(
        not_author_client, edit_url, new_form_data, comment):
    response = not_author_client.post(edit_url, data=new_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT


def test_author_can_delete_comment(author_client, delete_url, url_to_comments):
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_cant_delete_comment_of_another_user(
        not_author_client, delete_url):
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1
