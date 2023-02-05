from django.urls import path

from . import views

urlpatterns = [
	path('', views.patent_form, name='patent-form'),
]
