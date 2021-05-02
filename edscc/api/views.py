import logging

from django.contrib.auth.models import Group, User
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from edscc.commander.models import Commander

from .serializers import GroupSerializer, UserSerializer

# Create your views here.

log = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)


# class CommanderViewSet(viewsets.ModelViewSet):
#     queryset = Commander.objects.all()
#     serializer_class = CommanderSerializer
#     permission_classes = [IsAuthenticated]


@api_view(["GET"])
def commander_detail(request, pk):
    log.debug(request.user)
    log.debug(request.auth)

    content = {"commander": JSONRenderer().render(Commander.objects.filter(user_id=pk))}
    return Response(content)


# class HelloView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         log.debug(request.user)
#         log.debug(request.auth)
#         content = {
#             'message': 'Hello world!'
#         }
#         return Response(content)
