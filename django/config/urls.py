from django.contrib import admin
from django.urls import path, include

import qanda.urls
import user.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include(user.urls, namespace='user')),
    path('', include(qanda.urls, namespace='questions')),
]
