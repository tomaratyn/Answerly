from datetime import datetime
from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import streaming_bulk

from django.conf import settings

import logging

ALREADY_EXISTS_EXCEPTION = 'resource_already_exists_exception'

FAILED_TO_LOAD_ERROR = 'Failed to load {}: {!r}'

ISO_DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

logger = logging.getLogger(__name__)


def get_client():
    return Elasticsearch(hosts=[
        {'host': settings.ES_HOST, 'port': settings.ES_PORT,}
    ])


def create_index(name=settings.ES_INDEX):
    client = get_client()
    if not client.indices.exists(index=name):
        try:
            client.indices.create(index=name)
        except TransportError as e:
            if e.error == ALREADY_EXISTS_EXCEPTION:
                pass
            else:
                raise e


def bulk_load(questions):
    all_ok = True
    es_questions = (q.as_elasticsearch_dict() for q in questions)
    for ok, result in streaming_bulk(
            get_client(),
            es_questions,
            index=settings.ES_INDEX,
            raise_on_error=False,
    ):
        if not ok:
            all_ok = False
            action, result = result.popitem()
            logger.error(FAILED_TO_LOAD_ERROR.format(result['_id'], result))
    return all_ok


def search_for_questions(query):
    client = get_client()
    result = client.search(index=settings.ES_INDEX, body={
      'query': {
          'match': {
              'text': query,
          },
      },
    })
    return (h['_source'] for h in result['hits']['hits'])


def get_question_last_load_date():
    client = get_client()
    response = client.search(
        index=settings.ES_INDEX,
        body={
            'query': {
                'match_all': {}
            },
            'aggs': {
                'last_created': {
                    'max': {
                        'field': 'created'
                    }
                }
            }
        },
        params={'size': 0})
    last_created = response['aggregations']['last_created']['value']
    if last_created is None:
        return None
    last_date = datetime.utcfromtimestamp(last_created / 1000)
    return last_date


def upsert(question_model):
    client = get_client()
    question_dict = question_model.as_elasticsearch_dict()
    doc_type = question_dict['_type']
    del question_dict['_id']
    del question_dict['_type']
    response = client.update(
        settings.ES_INDEX,
        doc_type,
        id=question_model.id,
        body={
            'doc': question_dict,
            'doc_as_upsert': True,
        }
    )
    return response
