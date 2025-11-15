from django.urls import path
from .views import ProductApiView

urlpatterns = [

    #==================== VENDING API =========================
    path('getProductCategories', ProductApiView.as_view({'get':'get_product_cats'}),name="getProductCategories"),
    path('getProducts', ProductApiView.as_view({'get':'get_products'}),name="getProducts"),
    path('getDataBundle', ProductApiView.as_view({'get':'get_data_bundle'}),name="getDataBundle"),
    path('vendAirtime', ProductApiView.as_view({'post':'vend_vtu'}),name="vendAirtime"),
    path('vendData', ProductApiView.as_view({'post':'vend_data'}),name="vendData"),
    path('requeryTransaction', ProductApiView.as_view({'post':'get_transaction_by_client_ref'}),name="requeryTransaction"),

    #==================== CRON JOB =========================
    path('cronReverseTimeoutUnreversedTransaction', ProductApiView.as_view({'get':'cron_reverse_timeout_unreversed_transaction'}),name="cronReverseTimeoutUnreversedTransaction"),
]