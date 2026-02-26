from django.urls import path
from . import views

urlpatterns = [
    # Commits
    path("commits/", views.CommitListView.as_view(), name="commit-list"),
    path("commits/<str:sha>/", views.CommitDetailView.as_view(), name="commit-detail"),
    # Tickets
    path("tickets/", views.TicketListView.as_view(), name="ticket-list"),
    path(
        "tickets/<str:issue_key>/",
        views.TicketDetailView.as_view(),
        name="ticket-detail",
    ),
    path(
        "tickets/<str:issue_key>/context/",
        views.TicketContextView.as_view(),
        name="ticket-context",
    ),
    # Confluence Pages
    path("pages/", views.PageListView.as_view(), name="page-list"),
    path("pages/<uuid:pk>/", views.PageDetailView.as_view(), name="page-detail"),
    # Meetings
    path("meetings/", views.MeetingListView.as_view(), name="meeting-list"),
    path(
        "meetings/<uuid:pk>/", views.MeetingDetailView.as_view(), name="meeting-detail"
    ),
    # Projects
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path(
        "projects/<uuid:pk>/", views.ProjectDetailView.as_view(), name="project-detail"
    ),
    # Search
    path("search/", views.SearchView.as_view(), name="search"),
    # test
    path("test/", views.HelloPreetyView.as_view(), name="search"),
]
