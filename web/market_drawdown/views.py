from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.views.generic import View
from rest_framework.permissions import AllowAny
from django_ratelimit.decorators import ratelimit


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='1/2s', block=True)
def get_data_view(request):
    data = {
        "message": f"Hello! {request.data}",
        "status": "success"
    }
    print(request.data)
    return Response(data)

def main_view(request):
    return render(request, "html/main.html", locals())