from django.urls import path
from . import views

urlpatterns = [
    path('ratings/', views.RatingListCreate.as_view(), name='ratings'),
    path('ratings/list/', views.RatingList.as_view(), name='ratings-list'),
]
