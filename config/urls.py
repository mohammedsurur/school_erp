# config/urls.py

from django.contrib  import admin
from django.urls     import path, include
from django.conf     import settings
from django.conf.urls.static import static

# Use obscured admin URL in production
ADMIN_URL = getattr(settings, 'ADMIN_URL', 'admin/')

urlpatterns = [
    path(ADMIN_URL,        admin.site.urls),
    path('accounts/',      include('apps.accounts.urls')),
    path('dashboard/',     include('apps.core.urls')),
    path('students/',      include('apps.students.urls')),
    path('staff/',         include('apps.staff.urls')),
    path('academic/',      include('apps.academic.urls')),
    path('attendance/',    include('apps.attendance.urls')),
    path('exams/',         include('apps.exams.urls')),
    path('fees/',          include('apps.fees.urls')),
    path('library/',       include('apps.library.urls')),
    path('transport/',     include('apps.transport.urls')),
    path('communication/', include('apps.communication.urls')),
    path('reports/',       include('apps.reports.urls')),
    # path('api/',           include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Django debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls)),] + urlpatterns
    except ImportError:
        pass 