from django.urls import path
from .views import TrashListView, RestoreTrashItemView, HardDeleteTrashItemView, BulkTrashActionView

app_name = 'common'

urlpatterns = [
    path('trash/', TrashListView.as_view(), name='trash_list'),
    path('trash/restore/<int:model_index>/<int:pk>/', RestoreTrashItemView.as_view(), name='trash_restore'),
    path('trash/hard-delete/<int:model_index>/<int:pk>/', HardDeleteTrashItemView.as_view(), name='trash_hard_delete'),
    path('trash/bulk-action/', BulkTrashActionView.as_view(), name='bulk_trash_action'),
]

