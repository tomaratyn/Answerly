from datetime import date
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase, RequestFactory

from selenium.webdriver.chrome.webdriver import WebDriver

from qanda.factories import QuestionFactory, DEFAULT_BODY_HTML
from qanda.models import Question
from qanda.views import DailyQuestionList
from user.factories import UserFactory

QUESTION_CREATED_STRFTIME = '%Y-%m-%d %H:%M'


class QuestionSaveTestCase(TestCase):
    """
    Tests Question.save()
    """

    @patch('qanda.service.elasticsearch.Elasticsearch')
    def test_elasticsearch_upsert_on_save(self, ElasticsearchMock):
        user = get_user_model().objects.create_user(
            username='unittest',
            password='unittest',
        )
        question_title = 'Unit test'
        question_body = 'some long text'
        q = Question(
            title=question_title,
            question=question_body,
            user=user,
        )
        q.save()

        self.assertIsNotNone(q.id)
        self.assertTrue(ElasticsearchMock.called)
        mock_client = ElasticsearchMock.return_value
        mock_client.update.assert_called_once_with(
            settings.ES_INDEX,
            'doc',
            id=q.id,
            body={
                'doc': {
                    'text': '{}\n{}'.format(question_title, question_body),
                    'question_body': question_body,
                    'title': question_title,
                    'id': q.id,
                    'created': q.created,
                },
                'doc_as_upsert': True,
            }
        )


class DailyQuestionListTestCase(TestCase):
    """
    Tests the DailyQuestionList view
    """
    QUESTION_LIST_NEEDLE_TEMPLATE = '''
    <li >
        <a href="/q/{id}" >{title}</a >
        by {username} on {date}
    </li >
    '''

    REQUEST = RequestFactory().get(path='/q/2030-12-31')
    today = date.today()

    def test_GET_on_day_with_no_questions(self):
        response = DailyQuestionList.as_view()(
            self.REQUEST,
            year=self.today.year,
            month=self.today.month,
            day=self.today.day
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(['qanda/question_archive_day.html'],
                         response.template_name)
        self.assertEqual(0, response.context_data['object_list'].count())
        self.assertContains(response,
                            'Hmm... Everyone thinks they know everything '
                            'today.')

    def test_GET_on_day_with_many_questions(self):
        todays_questions = [QuestionFactory() for _ in range(10)]

        response = DailyQuestionList.as_view()(
            self.REQUEST,
            year=self.today.year,
            month=self.today.month,
            day=self.today.day
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(10, response.context_data['object_list'].count())
        rendered_content = response.rendered_content
        for question in todays_questions:
            needle = self.QUESTION_LIST_NEEDLE_TEMPLATE.format(
                id=question.id,
                title=question.title,
                username=question.user.username,
                date=question.created.strftime(QUESTION_CREATED_STRFTIME)
            )
            self.assertInHTML(needle, rendered_content)


class QuestionDetailViewTestCase(TestCase):
    QUESTION_DISPLAY_SNIPPET = '''
    <div class="question" >
      <div class="meta col-sm-12" >
        <h1 >{title}</h1 >
        Asked by {user} on {date}
      </div >
      <div class="body col-sm-12" >
        {body}
      </div >
    </div >'''
    LOGIN_TO_POST_ANSWERS = 'Login to post answers.'
    NO_ANSWERS_SNIPPET = '<li class="answer" >No answers yet!</li >'

    def test_anonymous_user_cannot_post_answers(self):
        question = QuestionFactory()

        response = self.client.get('/q/{}'.format(question.id))
        rendered_content = response.rendered_content

        self.assertEqual(200, response.status_code)

        template_names = [t.name for t in response.templates]
        self.assertNotIn('qanda/common/post_answer.html', template_names)
        self.assertIn(self.LOGIN_TO_POST_ANSWERS, rendered_content)

        self.assertInHTML(self.NO_ANSWERS_SNIPPET, rendered_content)

        question_needle = self.QUESTION_DISPLAY_SNIPPET.format(
            title=question.title,
            user=question.user.username,
            date=question.created.strftime(QUESTION_CREATED_STRFTIME),
            body=DEFAULT_BODY_HTML,
        )
        self.assertInHTML(question_needle, rendered_content)

    def test_logged_in_user_can_post_answers(self):
        question = QuestionFactory()

        self.assertTrue(self.client.login(
            username=question.user.username,
            password=UserFactory.password)
        )
        response = self.client.get('/q/{}'.format(question.id))
        rendered_content = response.rendered_content

        self.assertEqual(200, response.status_code)
        self.assertInHTML(self.NO_ANSWERS_SNIPPET, rendered_content)

        template_names = [t.name for t in response.templates]
        self.assertIn('qanda/common/post_answer.html', template_names)

        question_needle = self.QUESTION_DISPLAY_SNIPPET.format(
            title=question.title,
            user=question.user.username,
            date=question.created.strftime(QUESTION_CREATED_STRFTIME),
            body=DEFAULT_BODY_HTML,
        )
        self.assertInHTML(question_needle, rendered_content)


class AskQuestionTestCase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver(executable_path=settings.CHROMEDRIVER)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = UserFactory()

    def test_cant_ask_blank_question(self):
        initial_question_count = Question.objects.count()

        self.selenium.get('%s%s' % (self.live_server_url, '/user/login'))

        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys(self.user.username)
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys(UserFactory.password)
        self.selenium.find_element_by_id('log_in').click()

        self.selenium.find_element_by_link_text("Ask").click()
        ask_question_url = self.selenium.current_url
        submit_btn = self.selenium.find_element_by_id('ask')
        submit_btn.click()
        after_empty_submit_click = self.selenium.current_url

        self.assertEqual(ask_question_url, after_empty_submit_click)
        self.assertEqual(initial_question_count, Question.objects.count())
