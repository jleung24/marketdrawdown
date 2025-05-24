from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.shortcuts import render, redirect
from django_ratelimit.decorators import ratelimit
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse

from computation.drawdown import Drawdown
from computation.drawdowns import Drawdowns


@api_view(['POST','GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='1/2s', block=True)
def get_data_view(request):

    # hide if go to api url
    if request.method == "GET":
        return redirect("/")

    drawdown = Drawdown(
        str(request.data['index-dropdown']),
        int(request.data['drawdown_range_min']), 
        int(request.data['drawdown_range_max']),
        int(request.data['duration_range_min']),
        int(request.data['duration_range_max'])
    )

    drawdowns = Drawdowns(drawdown)
    drawdowns.get_drawdown_info(int(request.data['recovery_target']))
    data = {
        'median': drawdowns.median_recovery_days,
        'avg': drawdowns.avg_recovery_days,
        'total': drawdowns.total_drawdowns,
        'scatter_points': drawdowns.recovery_yearly_scatter
    }
    drawdowns.client.cleanup()
    html = render_to_string('html/dashboard.html', data)

    return HttpResponse(html)

def main_view(request):
    return render(request, "html/main.html", locals())