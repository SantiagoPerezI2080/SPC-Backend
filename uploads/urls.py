from django.urls import path
from .views import UploadCSVView
from .views import ListUploadedCSVs, PreviewCSV

urlpatterns = [
    path('upload/<str:file_type>/', UploadCSVView.as_view(), name='upload-csv'),
    path('uploaded/', ListUploadedCSVs.as_view(), name='list-uploaded'),
    path('uploaded/<str:file_type>/preview/', PreviewCSV.as_view(), name='preview-csv'),
]
