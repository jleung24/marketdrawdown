from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])
def test_view(request):
    if request.method == 'POST':
        return Response({"received": request.data})
    data = {
        "message": "Hello, this endpoint is not tied to a model!",
        "status": "success"
    }
    return Response(data)
