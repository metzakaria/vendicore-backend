
from django.contrib import admin
from django.urls import path, include, re_path
#from rest_framework_simplejwt import views as jwt_views
from . import views


urlpatterns = [
    #path('admin/', admin.site.urls),
    path('api/product/',include('apps.product.urls')),
    path('api/merchant/',include('apps.merchant.urls')),
   # Catch-all pattern for unrecognized routes
    re_path(r'^.*$', views.HandleInvalidRoute.as_view()),
]
