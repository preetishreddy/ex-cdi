from django.db.models import Q
from rest_framework import generics, views
from rest_framework.response import Response

from knowledge_base.models import (
    GitCommit, JiraTicket, ConfluencePage,
    Meeting, Project, EntityReference,
)
from .serializers import (
    GitCommitSerializer,
    JiraTicketSerializer,
    ConfluencePageListSerializer,
    ConfluencePageSerializer,
    MeetingListSerializer,
    MeetingDetailSerializer,
    ProjectSerializer,
    EntityReferenceSerializer,
)
from rest_framework.views import APIView

class HelloPreetyView(APIView):
    def get(self, request):
        return Response({"message": "hello preety"})



# ── Commits ──────────────────────────────────────────────────────────────────

class CommitListView(generics.ListAPIView):
#   '''
#   need payloads and response bodies
#   '''
    serializer_class = GitCommitSerializer
    queryset = GitCommit.objects.prefetch_related('files').all()


class CommitDetailView(generics.RetrieveAPIView):
    serializer_class = GitCommitSerializer
    queryset = GitCommit.objects.prefetch_related('files').all()
    lookup_field = 'sha'


# ── Tickets ───────────────────────────────────────────────────────────────────

class TicketListView(generics.ListAPIView):
    serializer_class = JiraTicketSerializer
    queryset = JiraTicket.objects.all()


class TicketDetailView(generics.RetrieveAPIView):
    serializer_class = JiraTicketSerializer
    queryset = JiraTicket.objects.all()
    lookup_field = 'issue_key'


class TicketContextView(views.APIView):
    """Returns a ticket plus all linked commits, pages, and meetings via entity_references."""

    def get(self, request, issue_key):
        ticket = generics.get_object_or_404(JiraTicket, issue_key=issue_key)

        # EntityReferences where this ticket is the reference target
        refs = EntityReference.objects.filter(
            reference_type='jira_ticket',
            reference_id=issue_key,
        )

        commit_ids = [r.source_id for r in refs if r.source_type == 'commit']
        meeting_ids = [r.source_id for r in refs if r.source_type == 'meeting']
        page_ids = [r.source_id for r in refs if r.source_type == 'confluence']

        from .serializers import GitCommitSerializer, MeetingListSerializer, ConfluencePageListSerializer
        return Response({
            'ticket': JiraTicketSerializer(ticket).data,
            'linked_commits': GitCommitSerializer(
                GitCommit.objects.filter(id__in=commit_ids).prefetch_related('files'),
                many=True,
            ).data,
            'linked_pages': ConfluencePageListSerializer(
                ConfluencePage.objects.filter(id__in=page_ids),
                many=True,
            ).data,
            'linked_meetings': MeetingListSerializer(
                Meeting.objects.filter(id__in=meeting_ids),
                many=True,
            ).data,
        })


# ── Confluence Pages ──────────────────────────────────────────────────────────

class PageListView(generics.ListAPIView):
    serializer_class = ConfluencePageListSerializer
    queryset = ConfluencePage.objects.all()


class PageDetailView(generics.RetrieveAPIView):
    serializer_class = ConfluencePageSerializer
    queryset = ConfluencePage.objects.all()


# ── Meetings ──────────────────────────────────────────────────────────────────

class MeetingListView(generics.ListAPIView):
    serializer_class = MeetingListSerializer
    queryset = Meeting.objects.all()


class MeetingDetailView(generics.RetrieveAPIView):
    serializer_class = MeetingDetailSerializer
    queryset = Meeting.objects.all()


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.prefetch_related('entities').all()


class ProjectDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.prefetch_related('entities').all()


# ── Search ────────────────────────────────────────────────────────────────────

class SearchView(views.APIView):
    """
    GET /api/search/?q=<query>

    Searches across commit messages, ticket summaries/descriptions,
    page titles/content, and meeting titles.
    """

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return Response({'error': 'Query parameter "q" is required.'}, status=400)

        commits = GitCommit.objects.filter(message__icontains=q).prefetch_related('files')
        tickets = JiraTicket.objects.filter(
            Q(summary__icontains=q) | Q(description__icontains=q)
        )
        pages = ConfluencePage.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q)
        )
        meetings = Meeting.objects.filter(title__icontains=q)

        return Response({
            'query': q,
            'commits': GitCommitSerializer(commits, many=True).data,
            'tickets': JiraTicketSerializer(tickets, many=True).data,
            'pages': ConfluencePageListSerializer(pages, many=True).data,
            'meetings': MeetingListSerializer(meetings, many=True).data,
        })
