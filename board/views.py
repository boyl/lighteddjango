import hashlib
import requests

from django.conf import settings
from django.core.signing import TimestampSigner
from django.contrib.auth import get_user_model

from rest_framework import viewsets, authentication, permissions, filters
from rest_framework.renderers import JSONRenderer
from rest_framework.pagination import PageNumberPagination
import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Sprint, Task
from .serializers import SprintSerializer, TaskSerializer, UserSerializer

# Create your views here.

User = get_user_model()


class NullFilter(django_filters.BooleanFilter):
    """Filter on a field set as null or not."""

    def filter(self, qs, value):
        if value is not None:
            return qs.filter(**{'%s__isnull' % self.field_name: value})
        return qs


class TaskFilter(django_filters.FilterSet):

    backlog = NullFilter(field_name='sprint')

    class Meta:
        model = Task
        fields = ('sprint', 'status', 'assigned', 'backlog',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['assigned'].extra.update({'to_field_name': User.USERNAME_FIELD})


class SprintFilter(django_filters.FilterSet):

    end_min = django_filters.DateFilter(field_name='end', lookup_expr='gte')
    end_max = django_filters.DateFilter(field_name='end', lookup_expr='lte')

    class Meta:
        model = Sprint
        fields = ('end_min', 'end_max',)


class StandardResultsSetPagination(PageNumberPagination):
    """
    Setting pagination for standard results.
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class DefaultsMixin(object):
    """
    Default settings for view authentication, permissions,
    filtering and pagination.
    """

    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.TokenAuthentication,
        # authentication.SessionAuthentication,
    )
    permission_classes = (
        permissions.IsAuthenticated,
    )
    pagination_class = StandardResultsSetPagination
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )


class UpdateHookMixin(object):
    """Mixin class to send update information to the websocket server."""

    @staticmethod
    def _build_hook_url(obj):
        if isinstance(obj, User):
            model = 'user'
        else:
            model = obj.__class__.__name__.lower()

        proto = 'https' if settings.WATERCOOLER_SECURE else 'http'
        host = settings.WATERCOOLER_SERVER
        return f"{proto}://{host}/{model}/{obj.pk}"

    def _send_hook_request(self, obj, method):
        url = self._build_hook_url(obj)
        if method in ('POST', 'PUT'):
            # Build the body
            serializer = self.get_serializer(obj)
            renderer = JSONRenderer()
            context = dict(request=self.request)
            body = renderer.render(serializer.data, renderer_context=context)
        else:
            body = None
        headers = {
            'content-type': 'application/json',
            'X-Signature': self._build_hook_signature(method, url, body)
        }
        try:
            response = requests.request(method, url, data=body, headers=headers, timeout=0.5)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            # Host could not be resolved or the connection was refused
            pass
        except requests.exceptions.Timeout:
            # Request timed out
            pass
        except requests.exceptions.RequestException:
            # Server response with 4XX or 5XX status code
            pass

    @staticmethod
    def _build_hook_signature(method, url, body):
        signer = TimestampSigner(settings.WATERCOOLER_SECRET)
        body = hashlib.sha256(body or b'').hexdigest()
        value = f"{method.lower()}:{url}:{body}"
        return signer.sign(value)

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._send_hook_request(serializer.instance, 'POST')

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._send_hook_request(serializer.instance, 'PUT')

    def perform_destroy(self, instance):
        self._send_hook_request(instance, 'DELETE')
        super().perform_destroy(instance)


class SprintViewSet(DefaultsMixin, UpdateHookMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating sprints."""

    queryset = Sprint.objects.order_by('end')
    serializer_class = SprintSerializer
    filter_class = SprintFilter
    search_fields = ('name',)
    ordering_fields = ('end', 'name', )


class TaskViewSet(DefaultsMixin, UpdateHookMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating tasks."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_class = TaskFilter
    search_fields = ('name', 'description',)
    ordering_fields = ('name', 'order', 'started', 'due', 'completed',)


class UserViewSet(DefaultsMixin, UpdateHookMixin, viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing users."""

    lookup_field = User.USERNAME_FIELD
    queryset = User.objects.order_by(User.USERNAME_FIELD)
    serializer_class = UserSerializer
    search_fields = (User.USERNAME_FIELD,)
