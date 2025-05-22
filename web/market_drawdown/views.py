from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.views.generic import View
from rest_framework.permissions import IsAuthenticated


@api_view(['POST'])
def test_view(request):
    data = {
        "message": f"Hello! {request.data}",
        "status": "success"
    }
    return Response(data)
