from unittest.mock import patch

import factory
from elasticsearch import Elasticsearch

from qanda.models import Question
from user.factories import UserFactory

DEFAULT_BODY_MARKDOWN = '''This is a question with lots of markdown in it.

This is a new paragraph with *italics* and **bold**.

    for foo in bar:
        # what a code sample
    <script>console.log('dangerous!')</script>
'''
DEFAULT_BODY_HTML = '''<p>This is a question with lots of markdown in it.</p>
<p>This is a new paragraph with <em>italics</em> and <strong>bold</strong>.</p>
<pre><code>for foo in bar:
    # what a code sample
&lt;script&gt;console.log('dangerous!')&lt;/script&gt;
</code></pre>
'''


class QuestionFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda n: 'Question #%d' % n)
    question = DEFAULT_BODY_MARKDOWN
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Question

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        with patch('qanda.service.elasticsearch.Elasticsearch',
               spec=Elasticsearch):
            question = super()._create(model_class, *args, **kwargs)
        return question
