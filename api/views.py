from django.db.models import Q
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework.views import APIView

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
from .ingestion import (
    run_github_ingest,
    run_jira_ingest,
    run_confluence_ingest,
    run_meeting_ingest,
)

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


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestGithubView(APIView):
    def post(self, request):
        try:
            result = run_github_ingest()
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class IngestJiraView(APIView):
    def post(self, request):
        try:
            result = run_jira_ingest()
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class IngestConfluenceView(APIView):
    def post(self, request):
        try:
            result = run_confluence_ingest()
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class IngestMeetingView(APIView):
    def post(self, request):
        vtt_file = request.FILES.get('file')
        if not vtt_file:
            return Response(
                {'error': 'No file uploaded. Send a .vtt file with key "file".'},
                status=400,
            )
        if not vtt_file.name.endswith('.vtt'):
            return Response({'error': 'File must be a .vtt file.'}, status=400)
        try:
            vtt_content = vtt_file.read().decode('utf-8')
            result = run_meeting_ingest(vtt_content, vtt_file.name)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


# ── Delete ────────────────────────────────────────────────────────────────────

ENTITY_MAP = {
    'commits':  (GitCommit,      'sha'),
    'tickets':  (JiraTicket,     'issue_key'),
    'pages':    (ConfluencePage, 'pk'),
    'meetings': (Meeting,        'pk'),
    'projects': (Project,        'pk'),
}

class DeleteView(APIView):
    """
    DELETE /api/delete/<entity_type>/<id>/

    entity_type : commits | tickets | pages | meetings | projects
    id          : sha (commits), issue_key (tickets), uuid (everything else)
    """
    def delete(self, request, entity_type, id):
        if entity_type not in ENTITY_MAP:
            return Response(
                {'error': f'Unknown entity type "{entity_type}". '
                          f'Choose from: {", ".join(ENTITY_MAP.keys())}'},
                status=400,
            )
        model, lookup_field = ENTITY_MAP[entity_type]
        obj = generics.get_object_or_404(model, **{lookup_field: id})
        obj.delete()
        return Response({'deleted': True, 'entity_type': entity_type, 'id': id})
