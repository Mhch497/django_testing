from http import HTTPStatus

from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'
FORM_DATA = {'text': COMMENT_TEXT}
NEW_FORM_DATA = {'text': NEW_COMMENT_TEXT}


def test_anonymous_user_cant_create_comment(
        client, news):
    count_comments_before = Comment.objects.count()
    url_detail = reverse('news:detail', args=(news.id,))
    client.post(url_detail, data=FORM_DATA)
    comments_count = Comment.objects.count()
    assert comments_count == count_comments_before


def test_user_can_create_comment(author_client,
                                 author,
                                 news):
    url_detail = reverse('news:detail', args=(news.id,))
    count_comments_before = Comment.objects.count()
    response = author_client.post(url_detail, data=FORM_DATA)
    assertRedirects(response, url_detail + '#comments')
    comments_count = Comment.objects.count()
    assert comments_count == count_comments_before + 1
    comment = Comment.objects.first()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, news):
    count_comments_before = Comment.objects.count()
    url_detail = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(url_detail, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == count_comments_before


def test_author_can_edit_comment(
        author_client, comment, news):
    edit_url = reverse('news:edit', args=(comment.id,))
    response = author_client.post(edit_url, data=NEW_FORM_DATA)
    url_detail = reverse('news:detail', args=(news.id,))
    assertRedirects(response, url_detail + '#comments')
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT


def test_user_cant_edit_comment_of_another_user(
        not_author_client, comment):
    edit_url = reverse('news:edit', args=(comment.id,))
    response = not_author_client.post(edit_url, data=NEW_FORM_DATA)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT


def test_author_can_delete_comment(
        author_client, comment, news):
    count_comments_before = Comment.objects.count()
    delete_url = reverse('news:delete', args=(comment.id,))
    url_detail = reverse('news:detail', args=(news.id,))
    response = author_client.delete(delete_url)
    assertRedirects(response, url_detail + '#comments')
    comments_count = Comment.objects.count()
    assert comments_count == count_comments_before - 1


def test_user_cant_delete_comment_of_another_user(
        not_author_client, comment):
    count_comments_before = Comment.objects.count()
    delete_url = reverse('news:delete', args=(comment.id,))
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == count_comments_before
