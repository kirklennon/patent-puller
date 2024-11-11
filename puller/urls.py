from django.urls import path

from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
	# path('', views.patent_form, name='patent-form'),
	path('', views.new),
	path('search', views.search),
	path('new', views.new),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
