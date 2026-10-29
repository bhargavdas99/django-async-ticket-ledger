from django.urls import path
from .views import EventListCreateView, BookTicketView

urlpatterns = [
    path('events/', EventListCreateView.as_view(), name='event-list'),
    path('tickets/book/', BookTicketView.as_view(), name='book-ticket'),
]