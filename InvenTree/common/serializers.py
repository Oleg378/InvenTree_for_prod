"""JSON serializers for common components."""

from django.db.models import OuterRef, Subquery
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import django_q.models
from error_report.models import Error
from flags.state import flag_state
from rest_framework import serializers

import common.models as common_models
from InvenTree.helpers import get_objectreference
from InvenTree.helpers_model import construct_absolute_url
from InvenTree.serializers import (
    InvenTreeImageSerializerField,
    InvenTreeModelSerializer,
)
from users.serializers import OwnerSerializer


class SettingsValueField(serializers.Field):
    """Custom serializer field for a settings value."""

    def get_attribute(self, instance):
        """Return the object instance, not the attribute value."""
        return instance

    def to_representation(self, instance):
        """Return the value of the setting.

        Protected settings are returned as '***'
        """
        return '***' if instance.protected else str(instance.value)

    def to_internal_value(self, data):
        """Return the internal value of the setting."""
        return str(data)


class SettingsSerializer(InvenTreeModelSerializer):
    """Base serializer for a settings object."""

    key = serializers.CharField(read_only=True)

    name = serializers.CharField(read_only=True)

    description = serializers.CharField(read_only=True)

    type = serializers.CharField(source='setting_type', read_only=True)

    choices = serializers.SerializerMethodField()

    model_name = serializers.CharField(read_only=True)

    api_url = serializers.CharField(read_only=True)

    value = SettingsValueField()

    units = serializers.CharField(read_only=True)

    typ = serializers.CharField(read_only=True)

    def get_choices(self, obj):
        """Returns the choices available for a given item."""
        results = []

        choices = obj.choices()

        if choices:
            for choice in choices:
                results.append({'value': choice[0], 'display_name': choice[1]})

        return results


class GlobalSettingsSerializer(SettingsSerializer):
    """Serializer for the InvenTreeSetting model."""

    class Meta:
        """Meta options for GlobalSettingsSerializer."""

        model = common_models.InvenTreeSetting
        fields = [
            'pk',
            'key',
            'value',
            'name',
            'description',
            'type',
            'units',
            'choices',
            'model_name',
            'api_url',
            'typ',
        ]


class UserSettingsSerializer(SettingsSerializer):
    """Serializer for the InvenTreeUserSetting model."""

    class Meta:
        """Meta options for UserSettingsSerializer."""

        model = common_models.InvenTreeUserSetting
        fields = [
            'pk',
            'key',
            'value',
            'name',
            'description',
            'user',
            'type',
            'units',
            'choices',
            'model_name',
            'api_url',
            'typ',
        ]

    user = serializers.PrimaryKeyRelatedField(read_only=True)


class GenericReferencedSettingSerializer(SettingsSerializer):
    """Serializer for a GenericReferencedSetting model.

    Args:
        MODEL: model class for the serializer
        EXTRA_FIELDS: fields that need to be appended to the serializer
            field must also be defined in the custom class
    """

    MODEL = None
    EXTRA_FIELDS = None

    def __init__(self, *args, **kwargs):
        """Init overrides the Meta class to make it dynamic."""

        class CustomMeta:
            """Scaffold for custom Meta class."""

            fields = [
                'pk',
                'key',
                'value',
                'name',
                'description',
                'type',
                'choices',
                'model_name',
                'api_url',
                'typ',
            ]

        # set Meta class
        self.Meta = CustomMeta
        self.Meta.model = self.MODEL
        # extend the fields
        self.Meta.fields.extend(self.EXTRA_FIELDS)

        # resume operations
        super().__init__(*args, **kwargs)


class NotificationMessageSerializer(InvenTreeModelSerializer):
    """Serializer for the InvenTreeUserSetting model."""

    class Meta:
        """Meta options for NotificationMessageSerializer."""

        model = common_models.NotificationMessage
        fields = [
            'pk',
            'target',
            'source',
            'user',
            'category',
            'name',
            'message',
            'creation',
            'age',
            'age_human',
            'read',
        ]

        read_only_fields = [
            'category',
            'name',
            'message',
            'creation',
            'age',
            'age_human',
        ]

    target = serializers.SerializerMethodField(read_only=True)
    source = serializers.SerializerMethodField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    read = serializers.BooleanField()

    def get_target(self, obj) -> dict:
        """Function to resolve generic object reference to target."""
        target = get_objectreference(obj, 'target_content_type', 'target_object_id')

        if target and 'link' not in target:
            # Check if object has an absolute_url function
            if hasattr(obj.target_object, 'get_absolute_url'):
                target['link'] = obj.target_object.get_absolute_url()
            else:
                # check if user is staff - link to admin
                request = self.context['request']
                if request.user and request.user.is_staff:
                    meta = obj.target_object._meta
                    target['link'] = construct_absolute_url(
                        reverse(
                            f'admin:{meta.db_table}_change',
                            kwargs={'object_id': obj.target_object_id},
                        )
                    )

        return target

    def get_source(self, obj) -> dict:
        """Function to resolve generic object reference to source."""
        return get_objectreference(obj, 'source_content_type', 'source_object_id')


class NewsFeedEntrySerializer(InvenTreeModelSerializer):
    """Serializer for the NewsFeedEntry model."""

    class Meta:
        """Meta options for NewsFeedEntrySerializer."""

        model = common_models.NewsFeedEntry
        fields = [
            'pk',
            'feed_id',
            'title',
            'link',
            'published',
            'author',
            'summary',
            'read',
        ]

    read = serializers.BooleanField()


class ConfigSerializer(serializers.Serializer):
    """Serializer for the InvenTree configuration.

    This is a read-only serializer.
    """

    def to_representation(self, instance):
        """Return the configuration data as a dictionary."""
        if not isinstance(instance, str):
            instance = list(instance.keys())[0]
        return {'key': instance, **self.instance[instance]}


class NotesImageSerializer(InvenTreeModelSerializer):
    """Serializer for the NotesImage model."""

    class Meta:
        """Meta options for NotesImageSerializer."""

        model = common_models.NotesImage
        fields = ['pk', 'image', 'user', 'date']

        read_only_fields = ['date', 'user']

    image = InvenTreeImageSerializerField(required=True)


class ProjectCodeSerializer(InvenTreeModelSerializer):
    """Serializer for the ProjectCode model."""

    class Meta:
        """Meta options for ProjectCodeSerializer."""

        model = common_models.ProjectCode
        fields = ['pk', 'code', 'description', 'responsible', 'responsible_detail']

    responsible_detail = OwnerSerializer(source='responsible', read_only=True)


class FlagSerializer(serializers.Serializer):
    """Serializer for feature flags."""

    def to_representation(self, instance):
        """Return the configuration data as a dictionary."""
        request = self.context.get('request')
        if not isinstance(instance, str):
            instance = list(instance.keys())[0]
        data = {'key': instance, 'state': flag_state(instance, request=request)}

        if request and request.user.is_superuser:
            data['conditions'] = self.instance[instance]

        return data


class CustomUnitSerializer(InvenTreeModelSerializer):
    """DRF serializer for CustomUnit model."""

    class Meta:
        """Meta options for CustomUnitSerializer."""

        model = common_models.CustomUnit
        fields = ['pk', 'name', 'symbol', 'definition']


class ErrorMessageSerializer(InvenTreeModelSerializer):
    """DRF serializer for server error messages."""

    class Meta:
        """Metaclass options for ErrorMessageSerializer."""

        model = Error

        fields = ['when', 'info', 'data', 'path', 'pk']

        read_only_fields = ['when', 'info', 'data', 'path', 'pk']


class TaskOverviewSerializer(serializers.Serializer):
    """Serializer for background task overview."""

    is_running = serializers.BooleanField(
        label=_('Is Running'),
        help_text='Boolean value to indicate if the background worker process is running.',
        read_only=True,
    )

    pending_tasks = serializers.IntegerField(
        label=_('Pending Tasks'),
        help_text='Number of active background tasks',
        read_only=True,
    )

    scheduled_tasks = serializers.IntegerField(
        label=_('Scheduled Tasks'),
        help_text='Number of scheduled background tasks',
        read_only=True,
    )

    failed_tasks = serializers.IntegerField(
        label=_('Failed Tasks'),
        help_text='Number of failed background tasks',
        read_only=True,
    )


class PendingTaskSerializer(InvenTreeModelSerializer):
    """Serializer for an individual pending task object."""

    class Meta:
        """Metaclass options for the serializer."""

        model = django_q.models.OrmQ
        fields = ['pk', 'key', 'lock', 'task_id', 'name', 'func', 'args', 'kwargs']

    task_id = serializers.CharField(label=_('Task ID'), help_text=_('Unique task ID'))

    lock = serializers.DateTimeField(label=_('Lock'), help_text=_('Lock time'))

    name = serializers.CharField(label=_('Name'), help_text=_('Task name'))

    func = serializers.CharField(label=_('Function'), help_text=_('Function name'))

    args = serializers.CharField(label=_('Arguments'), help_text=_('Task arguments'))

    kwargs = serializers.CharField(
        label=_('Keyword Arguments'), help_text=_('Task keyword arguments')
    )


class ScheduledTaskSerializer(InvenTreeModelSerializer):
    """Serializer for an individual scheduled task object."""

    class Meta:
        """Metaclass options for the serializer."""

        model = django_q.models.Schedule
        fields = [
            'pk',
            'name',
            'func',
            'args',
            'kwargs',
            'schedule_type',
            'repeats',
            'last_run',
            'next_run',
            'success',
            'task',
        ]

    last_run = serializers.DateTimeField()
    success = serializers.BooleanField()

    @staticmethod
    def annotate_queryset(queryset):
        """Add custom annotations to the queryset.

        - last_run: The last time the task was run
        - success: The outcome status of the last run
        """
        task = django_q.models.Task.objects.filter(id=OuterRef('task'))

        queryset = queryset.annotate(
            last_run=Subquery(task.values('started')[:1]),
            success=Subquery(task.values('success')[:1]),
        )

        return queryset


class FailedTaskSerializer(InvenTreeModelSerializer):
    """Serializer for an individual failed task object."""

    class Meta:
        """Metaclass options for the serializer."""

        model = django_q.models.Failure
        fields = [
            'pk',
            'name',
            'func',
            'args',
            'kwargs',
            'started',
            'stopped',
            'attempt_count',
            'result',
        ]

    pk = serializers.CharField(source='id', read_only=True)

    result = serializers.CharField()
