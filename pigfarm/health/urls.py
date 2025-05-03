from django.urls import path
from .views import *
 

urlpatterns = [
    path('health-records/', health_records_list, name='health_records'),
    path('health-records/add/', add_or_edit_health_record, name='add_health_record'),
    path('health-records/edit/<uuid:record_id>/', add_or_edit_health_record, name='edit_health_record'),
    path('health-records/<uuid:record_id>/delete/', delete_health_record, name='delete_health_record'),
    path('vaccination/add/', add_or_edit_vaccination, name='add_vaccination'),
    path('vaccination/edit/<int:pk>/', add_or_edit_vaccination, name='edit_vaccination'),
    path('vaccination/', vaccination_list, name='vaccination_list'),
    path('vaccination/delete/<int:vaccine_id>/', delete_vaccination, name='delete_vaccination'),
    path('vaccination/assign/', assign_vaccination, name='assign_vaccination'),
    path('vaccination/records/', vaccination_records_list, name='vaccination_records'),
    path('vaccination/edit/<uuid:record_id>/', edit_vaccination, name='edit_vaccination'),
    path('vaccination/delete/<uuid:record_id>/', delete_vaccination, name='delete_vaccination'),
    path('record-weight/', add_or_edit_weight_record, name='record_weight'),
    path('weight-records/', weight_records_list, name='weight_records_list'),
    path('weight-records/<uuid:record_id>/delete/', delete_weight_record, name='delete_weight_record'),
    path('record-weight/<uuid:record_id>/', add_or_edit_weight_record, name='edit_weight_record'),
    path('delete-weight-record/<uuid:record_id>/', delete_weight_record, name='delete_weight_record'),
    path('health-records/<uuid:record_id>/delete/', delete_health_record, name='delete_health_record'),
    path('health-records/<uuid:record_id>/delete-from-sow/', delete_health_record_from_sow, name='delete_health_record_from_sow'),
]
