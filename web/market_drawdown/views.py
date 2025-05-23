from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.views.generic import View
from rest_framework.permissions import AllowAny
from django_ratelimit.decorators import ratelimit
from computation.drawdown import Drawdown
from computation.drawdowns import Drawdowns


# TODO: validate request data, 
@api_view(['POST','GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='1/2s', block=True)
def get_data_view(request):

    # hide if go to api url
    if request.method == "GET":
        return redirect("/")

    drawdown = Drawdown(
        "SPY",
        int(request.data['drawdown_range_min']), 
        int(request.data['drawdown_range_max']),
        int(request.data['duration_range_min']),
        int(request.data['duration_range_max'])
    )

    drawdowns = Drawdowns(drawdown)
    drawdowns.get_drawdown_info(int(request.data['recovery_target']))

    data = drawdowns.drawdown_data
    drawdowns.client.cleanup()

    return Response(data)

def main_view(request):
    return render(request, "html/main.html", locals())