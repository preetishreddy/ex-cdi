from django.db.models import Q
from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, inline_serializer
from rest_framework import serializers as drf_serializers

from knowledge_base.models import (
    GitCommit, JiraTicket, ConfluencePage,
    Meeting, Project, EntityReference,
    Employee, Sprint, SprintTicket, Decision,
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
    EmployeeSerializer,
    SprintSerializer,
    SprintTicketSerializer,
    DecisionSerializer,
    SprintOutcomeSerializer,
)
from .ingestion import (
    run_github_ingest,
    run_jira_ingest,
    run_confluence_ingest,
    run_meeting_ingest,
)


# ── Reusable inline serializers for schema documentation ─────────────────────

_ErrorSerializer = inline_serializer('Error', fields={
    'error': drf_serializers.CharField(),
})

_DeleteResponseSerializer = inline_serializer('DeleteResponse', fields={
    'deleted': drf_serializers.BooleanField(),
    'entity_type': drf_serializers.CharField(),
    'id': drf_serializers.CharField(),
})

_IngestResultSerializer = inline_serializer('IngestResult', fields={
    'status': drf_serializers.CharField(),
    'created': drf_serializers.IntegerField(required=False),
    'updated': drf_serializers.IntegerField(required=False),
    'skipped': drf_serializers.IntegerField(required=False),
})

_SearchResultSerializer = inline_serializer('SearchResult', fields={
    'query': drf_serializers.CharField(),
    'commits': GitCommitSerializer(many=True),
    'tickets': JiraTicketSerializer(many=True),
    'pages': ConfluencePageListSerializer(many=True),
    'meetings': MeetingListSerializer(many=True),
})

_TicketContextSerializer = inline_serializer('TicketContext', fields={
    'ticket': JiraTicketSerializer(),
    'linked_commits': GitCommitSerializer(many=True),
    'linked_pages': ConfluencePageListSerializer(many=True),
    'linked_meetings': MeetingListSerializer(many=True),
})


# ── Test ─────────────────────────────────────────────────────────────────────

class HelloPreetyView(APIView):
    @extend_schema(
        tags=['Test'],
        summary='Health check',
        description='Simple endpoint to verify the API is running.',
        responses={200: inline_serializer('HelloResponse', fields={
            'message': drf_serializers.CharField(),
        })},
    )
    def get(self, request):
        return Response({"message": "hello preety"})



# ── Commits ──────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Commits'],
        summary='List all commits',
        description='Returns every git commit stored in the knowledge base, newest first. Includes changed files.',
    ),
)
class CommitListView(generics.ListAPIView):
    serializer_class = GitCommitSerializer
    queryset = GitCommit.objects.prefetch_related('files').all()


@extend_schema_view(
    get=extend_schema(
        tags=['Commits'],
        summary='Get commit by SHA',
        description='Retrieve a single git commit and its changed files by full SHA.',
    ),
)
class CommitDetailView(generics.RetrieveAPIView):
    serializer_class = GitCommitSerializer
    queryset = GitCommit.objects.prefetch_related('files').all()
    lookup_field = 'sha'


# ── Tickets ───────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Tickets'],
        summary='List all tickets',
        description='Returns every Jira ticket in the knowledge base.',
    ),
)
class TicketListView(generics.ListAPIView):
    serializer_class = JiraTicketSerializer
    queryset = JiraTicket.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=['Tickets'],
        summary='Get ticket by issue key',
        description='Retrieve a single Jira ticket by its issue key (e.g. PAY-123).',
    ),
)
class TicketDetailView(generics.RetrieveAPIView):
    serializer_class = JiraTicketSerializer
    queryset = JiraTicket.objects.all()
    lookup_field = 'issue_key'


class TicketContextView(views.APIView):
    """Returns a ticket plus all linked commits, pages, and meetings via entity_references."""

    @extend_schema(
        tags=['Tickets'],
        summary='Get ticket with linked context',
        description=(
            'Returns the ticket together with all commits, Confluence pages, '
            'and meetings linked to it through entity references.'
        ),
        responses={200: _TicketContextSerializer},
    )
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

@extend_schema_view(
    get=extend_schema(
        tags=['Pages'],
        summary='List all Confluence pages',
        description='Returns a summary list of every Confluence page in the knowledge base.',
    ),
)
class PageListView(generics.ListAPIView):
    serializer_class = ConfluencePageListSerializer
    queryset = ConfluencePage.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=['Pages'],
        summary='Get Confluence page by ID',
        description='Retrieve a single Confluence page with full content.',
    ),
)
class PageDetailView(generics.RetrieveAPIView):
    serializer_class = ConfluencePageSerializer
    queryset = ConfluencePage.objects.all()


# ── Meetings ──────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Meetings'],
        summary='List all meetings',
        description=(
            'Returns meetings with full transcript. '
            'Optionally filter by exact date using `?date=YYYY-MM-DD`.'
        ),
        parameters=[
            OpenApiParameter(
                name='date', type=str, location=OpenApiParameter.QUERY,
                required=False, description='Filter by meeting date (YYYY-MM-DD).',
            ),
        ],
    ),
)
class MeetingListView(generics.ListAPIView):
    serializer_class = MeetingDetailSerializer

    def get_queryset(self):
        qs = Meeting.objects.all()
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(meeting_date__date=date)
        return qs


@extend_schema_view(
    get=extend_schema(
        tags=['Meetings'],
        summary='Get meeting by ID',
        description='Retrieve full meeting details including raw VTT content.',
    ),
)
class MeetingDetailView(generics.RetrieveAPIView):
    serializer_class = MeetingDetailSerializer
    queryset = Meeting.objects.all()


# ── Projects ──────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Projects'],
        summary='List all projects',
        description='Returns every project with its linked entities.',
    ),
)
class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.prefetch_related('entities').all()


@extend_schema_view(
    get=extend_schema(
        tags=['Projects'],
        summary='Get project by ID',
        description='Retrieve a single project with all linked entities.',
    ),
)
class ProjectDetailView(generics.RetrieveAPIView):
    serializer_class = ProjectSerializer
    queryset = Project.objects.prefetch_related('entities').all()


# ── Search ────────────────────────────────────────────────────────────────────

class SearchView(views.APIView):
    """Full-text search across all entity types."""

    @extend_schema(
        tags=['Search'],
        summary='Search across all entities',
        description=(
            'Searches commit messages, ticket summaries/descriptions, '
            'page titles/content, and meeting titles for the given query string.'
        ),
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='Search query string.',
            ),
        ],
        responses={
            200: _SearchResultSerializer,
            400: _ErrorSerializer,
        },
    )
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
    @extend_schema(
        tags=['Ingestion'],
        summary='Ingest GitHub commits',
        description='Pulls commits from the configured GitHub repo and stores them in the knowledge base.',
        request=None,
        responses={200: _IngestResultSerializer, 400: _ErrorSerializer, 500: _ErrorSerializer},
    )
    def post(self, request):
        try:
            result = run_github_ingest()
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class IngestJiraView(APIView):
    @extend_schema(
        tags=['Ingestion'],
        summary='Ingest Jira tickets',
        description='Pulls tickets from the configured Jira project and stores them in the knowledge base.',
        request=None,
        responses={200: _IngestResultSerializer, 400: _ErrorSerializer, 500: _ErrorSerializer},
    )
    def post(self, request):
        try:
            result = run_jira_ingest()
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class IngestConfluenceView(APIView):
    @extend_schema(
        tags=['Ingestion'],
        summary='Ingest Confluence pages',
        description='Pulls pages from the configured Confluence space and stores them in the knowledge base.',
        request=None,
        responses={200: _IngestResultSerializer, 400: _ErrorSerializer, 500: _ErrorSerializer},
    )
    def post(self, request):
        try:
            result = run_confluence_ingest()
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class IngestMeetingView(APIView):
    @extend_schema(
        tags=['Ingestion'],
        summary='Ingest meeting transcript',
        description='Upload a `.vtt` file to parse and store a meeting transcript. Send as multipart/form-data with key `file`.',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary', 'description': 'A .vtt transcript file'},
                },
                'required': ['file'],
            },
        },
        responses={200: _IngestResultSerializer, 400: _ErrorSerializer, 500: _ErrorSerializer},
    )
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


# ── Sprint Outcomes ───────────────────────────────────────────────────────────

class SprintTicketsOutcomeView(views.APIView):
    """GET /api/sprints/<sprint_number>/tickets/ — tickets in a sprint with completion status."""

    @extend_schema(
        tags=['Sprints'],
        summary='Get sprint ticket outcomes',
        description=(
            'Returns all Jira tickets in a sprint with completion status. '
            'Each ticket includes `is_completed`, `teammates`, and `teammates_count`. '
            'Also returns summary counts: total, completed, pending.'
        ),
        responses={
            200: SprintOutcomeSerializer,
            404: _ErrorSerializer,
        },
    )
    def get(self, request, sprint_number):
        sprint = generics.get_object_or_404(Sprint, sprint_number=sprint_number)
        return Response(SprintOutcomeSerializer(sprint).data)


class SprintMeetingsView(views.APIView):
    """GET /api/sprints/<sprint_number>/meetings/ — meetings that happened during a sprint."""

    @extend_schema(
        tags=['Sprints'],
        summary='Get meetings during a sprint',
        description=(
            'Returns all meeting transcripts where the meeting date falls within '
            'the sprint\'s start and end dates.'
        ),
        responses={
            200: MeetingDetailSerializer(many=True),
            404: _ErrorSerializer,
        },
    )
    def get(self, request, sprint_number):
        sprint = generics.get_object_or_404(Sprint, sprint_number=sprint_number)
        meetings = Meeting.objects.filter(
            meeting_date__date__gte=sprint.start_date,
            meeting_date__date__lte=sprint.end_date,
        )
        return Response(MeetingDetailSerializer(meetings, many=True).data)


# ── Employees ────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Employees'],
        summary='List all employees',
        description='Returns all team members stored in the knowledge base.',
    ),
)
class EmployeeListView(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=['Employees'],
        summary='Get employee by ID',
        description='Retrieve a single employee record by UUID.',
    ),
)
class EmployeeDetailView(generics.RetrieveAPIView):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()


# ── Sprints ───────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Sprints'],
        summary='List all sprints',
        description='Returns all sprints with their linked tickets.',
    ),
)
class SprintListView(generics.ListAPIView):
    serializer_class = SprintSerializer
    queryset = Sprint.objects.prefetch_related('sprint_tickets').all()


@extend_schema_view(
    get=extend_schema(
        tags=['Sprints'],
        summary='Get sprint by ID',
        description='Retrieve a single sprint with all its tickets.',
    ),
)
class SprintDetailView(generics.RetrieveAPIView):
    serializer_class = SprintSerializer
    queryset = Sprint.objects.prefetch_related('sprint_tickets').all()


# ── Decisions ─────────────────────────────────────────────────────────────────

@extend_schema_view(
    get=extend_schema(
        tags=['Decisions'],
        summary='List all decisions',
        description='Returns the unified decision timeline across meetings, Confluence, Jira, and commits.',
        parameters=[
            OpenApiParameter(name='category', type=str, location=OpenApiParameter.QUERY,
                             required=False, description='Filter by category (e.g. architecture, technology).'),
            OpenApiParameter(name='source_type', type=str, location=OpenApiParameter.QUERY,
                             required=False, description='Filter by source (meeting, confluence, jira, git_commit).'),
        ],
    ),
)
class DecisionListView(generics.ListAPIView):
    serializer_class = DecisionSerializer

    def get_queryset(self):
        qs = Decision.objects.all()
        category = self.request.query_params.get('category')
        source_type = self.request.query_params.get('source_type')
        if category:
            qs = qs.filter(category=category)
        if source_type:
            qs = qs.filter(source_type=source_type)
        return qs


@extend_schema_view(
    get=extend_schema(
        tags=['Decisions'],
        summary='Get decision by ID',
        description='Retrieve a single decision record by UUID.',
    ),
)
class DecisionDetailView(generics.RetrieveAPIView):
    serializer_class = DecisionSerializer
    queryset = Decision.objects.all()


# ── Delete ────────────────────────────────────────────────────────────────────

ENTITY_MAP = {
    'commits':   (GitCommit,      'sha'),
    'tickets':   (JiraTicket,     'issue_key'),
    'pages':     (ConfluencePage, 'pk'),
    'meetings':  (Meeting,        'pk'),
    'projects':  (Project,        'pk'),
    'employees': (Employee,       'pk'),
    'sprints':   (Sprint,         'pk'),
    'decisions': (Decision,       'pk'),
}

class DeleteView(APIView):
    """
    DELETE /api/delete/<entity_type>/<id>/

    entity_type : commits | tickets | pages | meetings | projects
    id          : sha (commits), issue_key (tickets), uuid (everything else)
    """
    @extend_schema(
        tags=['Delete'],
        summary='Delete an entity',
        description=(
            'Remove a record from the knowledge base.\n\n'
            '**entity_type** must be one of: `commits`, `tickets`, `pages`, `meetings`, `projects`.\n\n'
            '**id** is the SHA for commits, issue_key for tickets, or UUID for everything else.'
        ),
        responses={
            200: _DeleteResponseSerializer,
            400: _ErrorSerializer,
            404: _ErrorSerializer,
        },
    )
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
