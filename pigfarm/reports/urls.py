from django.urls import path
from . import views

urlpatterns = [
    path('finance/', views.finance_report, name='finance_report'),
    path('finance/export/', views.finance_report_export, name='finance_report_export'),
    path('finance/pdf/', views.finance_report_pdf, name='finance_report_pdf'),
    path('piglet-births/', views.piglet_births_report, name='piglet_births_report'),
    path('piglet-births/export/', views.piglet_births_report_export, name='piglet_births_report_export'),
    path('piglet-births/pdf/', views.piglet_births_report_pdf, name='piglet_births_report_pdf'),
    path('sows/', views.sow_report, name='sow_report'),
    path('sows/export/', views.sow_report_export, name='sow_report_export'),
    path('sows/pdf/', views.sow_report_pdf, name='sow_report_pdf'),
    path('weights/', views.weight_report, name='weight_report'),
    path('weights/export/', views.weight_report_export, name='weight_report_export'),
    path('weights/pdf/', views.weight_report_pdf, name='weight_report_pdf'),
    path('feeding-cost/', views.feeding_cost_report, name='feeding_cost_report'),
    path('feeding-cost/export/', views.feeding_cost_report_export, name='feeding_cost_report_export'),
    path('feeding-cost/pdf/', views.feeding_cost_report_pdf, name='feeding_cost_report_pdf'),
]