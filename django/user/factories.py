from django.conf import settings

import factory


class UserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user %d' % n)
    password = 'unittest'

    class Meta:
        model = settings.AUTH_USER_MODEL

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
