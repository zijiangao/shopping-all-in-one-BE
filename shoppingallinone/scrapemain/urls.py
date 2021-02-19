from django.urls import path
from . import views
app_name = 'products'

urlpatterns = [

    path('<str:product_id>/', views.get_product, name="get_product"),

]