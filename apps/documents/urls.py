from django.urls import path
from .views import (
    GazetteListView, GazetteCreateView, GazetteUpdateView, 
    GazetteDeleteView, GazetteDetailView,
    DocumentListView, DocumentCreateView, DocumentUpdateView,
    DocumentDeleteView, DocumentDetailView
)

app_name = 'documents'

urlpatterns = [
    # ============================================================
    # GACETAS
    # ============================================================
    path('gazette/', GazetteListView.as_view(), name='gazette_list'),
    path('gazette/create/', GazetteCreateView.as_view(), name='gazette_create'),
    path('gazette/<int:pk>/update/', GazetteUpdateView.as_view(), name='gazette_update'),
    path('gazette/<int:pk>/delete/', GazetteDeleteView.as_view(), name='gazette_delete'),
    path('gazette/<int:pk>/', GazetteDetailView.as_view(), name='gazette_detail'),

    # ============================================================
    # DOCUMENTOS
    # ============================================================
    path('', DocumentListView.as_view(), name='document_list'),
    path('create/', DocumentCreateView.as_view(), name='document_create'),
    path('<int:pk>/detail/', DocumentDetailView.as_view(), name='document_detail'),
    path('<int:pk>/update/', DocumentUpdateView.as_view(), name='document_update'),
    path('<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),
]