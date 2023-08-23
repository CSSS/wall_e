from django.urls import path

from wall_e_leveling.views import IndexPage

urlpatterns = [
    path("", IndexPage.as_view(), name="index"),

]
