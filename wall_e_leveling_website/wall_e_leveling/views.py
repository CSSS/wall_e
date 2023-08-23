from django.core.paginator import Paginator
from django.shortcuts import render

# Create your views here.
from django.views import View

from WalleModels.models import UserPoint


class IndexPage(View):

    def get(self, request):
        points = UserPoint.objects.all()
        paginated_object = Paginator(points.order_by('-points'), per_page=30).page(1)

        return render(request, 'index.html', {"points": paginated_object})
