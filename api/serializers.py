from rest_framework import serializers
from knowledge_base.models import (
    GitCommit, GitCommitFile, JiraTicket, ConfluencePage,
    Meeting, Project, ProjectEntity, EntityReference,
)


class GitCommitFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitCommitFile
        fields = ['id', 'filename', 'additions', 'deletions', 'status']


class GitCommitSerializer(serializers.ModelSerializer):
    files = GitCommitFileSerializer(many=True, read_only=True)

    class Meta:
        model = GitCommit
        fields = [
            'id', 'sha', 'author_name', 'author_email',
            'commit_date', 'message', 'related_tickets',
            'created_at', 'updated_at', 'files',
        ]


class JiraTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraTicket
        fields = '__all__'


class ConfluencePageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfluencePage
        fields = [
            'id', 'title', 'space', 'author', 'labels',
            'version', 'page_created_date', 'page_updated_date',
        ]


class ConfluencePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfluencePage
        fields = '__all__'


class MeetingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'meeting_date', 'summary',
            'key_decisions', 'action_items', 'participants',
            'duration_seconds', 'source_filename',
            'created_at', 'updated_at',
        ]


class MeetingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = '__all__'


class ProjectEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectEntity
        fields = ['id', 'entity_type', 'entity_id', 'added_manually', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    entities = ProjectEntitySerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'


class EntityReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityReference
        fields = '__all__'
