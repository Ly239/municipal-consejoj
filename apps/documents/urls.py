from django.urls import path
from .views import *

urlpatterns = [
    
	#Gaceta
    path('gazette/', GazetteListView.as_view(), name='gazette-list'),
    path('gazette/create/', GazetteCreateView.as_view(), name='gazette-create'),
    path('gazette/<int:pk>/update/', GazetteUpdateView.as_view(), name='gazette-update'),
    path('gazette/<int:pk>/delete/', GazetteDeleteView.as_view(), name='gazette-delete'),
    path('gazette/<int:pk>/', GazetteDetailView.as_view(), name='gazette-detail'),

 	# Documentos
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('documents/create/', DocumentCreateView.as_view(), name='document-create'),
    path('documents/<int:pk>/detail/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/update/', DocumentUpdateView.as_view(), name='document-update'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document-delete'),
   
]
