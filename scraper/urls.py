from django.urls import path
from .views import ScrapeAndExtractView

urlpatterns = [
    path('scrape/<str:username>/<int:max_posts>/', ScrapeAndExtractView.as_view(), name='scrape_and_extract'),
]
