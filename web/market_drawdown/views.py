import json
import hashlib
from datetime import datetime, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.shortcuts import render, redirect
from django_ratelimit.decorators import ratelimit
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache

from computation.drawdown import Drawdown
from computation.drawdowns import Drawdowns


@api_view(['POST','GET'])
@permission_classes([AllowAny])
@ratelimit(key='header:x-forwarded-for', rate='1/2s', block=True)
def get_data_view(request):

    # hide if go to api url
    if request.method == "GET":
        return redirect("/")
    
    if not data_ok(request):
        html = render_to_string('html/error.html')
        return HttpResponse(html)
    
    try:
        request_data = dict(request.data)
        request_data.pop('csrfmiddlewaretoken', None)
        data_string = json.dumps(request_data, sort_keys=True)
        cache_key = "get_data_view:" + hashlib.sha256(data_string.encode()).hexdigest()
    except Exception as e:
        cache_key = None

    if cache_key:
        cached_html = cache.get(cache_key)
        if cached_html is not None:
            return HttpResponse(cached_html)

    try:
        drawdown = Drawdown(
            str(request.data['index-dropdown']),
            int(request.data['drawdown_range_min']), 
            int(request.data['drawdown_range_max']),
            int(request.data['duration_range_min'])*30,
            int(request.data['duration_range_max'])*30
        )

        drawdowns = Drawdowns(drawdown)
        drawdowns.get_drawdown_info(int(request.data['recovery_target']))
        data = {
            'median': drawdowns.median_recovery_months,
            'avg': drawdowns.avg_recovery_months,
            'total': drawdowns.total_drawdowns,
            'scatter_points': drawdowns.recovery_yearly_scatter,
            'recovery_graph': drawdowns.recovery_graph,
            'drawdown_period_graph': drawdowns.drawdown_period_graph,
            'max_drawdown_graph': drawdowns.max_drawdown_graph
        }

        html = render_to_string('html/dashboard.html', data)

    except:
        html = render_to_string('html/error.html')

    # set timeout for 09:00 UTC
    now = datetime.now()
    next_expiration = now.replace(hour=7, minute=30, second=0, microsecond=0)
    if now >= next_expiration:
        next_expiration = (now + timedelta(days=1)).replace(hour=7, minute=30, second=0, microsecond=0)
    timeout = int((next_expiration - now).total_seconds())

    if cache_key:
        cache.set(cache_key, html, timeout=timeout)

    return HttpResponse(html)

def data_ok(request):
    conditions = [
        str(request.data['index-dropdown']) in ['QQQ', 'SPY'],
        int(request.data['drawdown_range_min']) < int(request.data['drawdown_range_max']),
        int(request.data['duration_range_min']) < int(request.data['duration_range_max']),
        int(request.data['recovery_target']) <= 100 and int(request.data['recovery_target']) >= 20,
        int(request.data['drawdown_range_min']) >= 5 and int(request.data['drawdown_range_max']) <= 100,
        int(request.data['duration_range_min']) >= 0 and int(request.data['duration_range_max']) <= 200
    ]

    return all(conditions)

def main_view(request):
    return render(request, "html/main.html", locals())
