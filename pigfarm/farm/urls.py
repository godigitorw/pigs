# farm/urls.py
from django.urls import path
from . import views 
from .views import *

urlpatterns = [
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/add/', views.add_room, name='add_room'),
    path('rooms/<int:pk>/edit/', views.add_room, name='room_update'),  # Same view handles update
    path('rooms/<int:pk>/delete/', views.room_delete, name='room_delete'),
    path('sows/', views.sow_list, name='sow_list'),
    path('sows/add/', views.add_sow, name='add_sow'),
    path('sows/<int:pk>/edit/', views.add_sow, name='update_sow'),
    path('sows/<int:pk>/delete/', views.sow_delete, name='delete_sow'),
    path('piglets/', views.piglet_list, name='piglets'),
    path('piglets/add/', views.add_piglet, name='add_piglet'),
    path('piglets/<int:pk>/edit/', views.add_piglet, name='piglet_update'),
    path('piglets/<int:pk>/delete/', views.piglet_delete, name='piglet_delete'),   
    path('sow/<uuid:sow_id>/', sow_profile, name='sow_profile'),
    path('feed-stock/', feed_stock_list, name='feed_stock_list'),
    path('feed-stock/add/', add_feed_stock, name='add_feed_stock'),
    path('feed-stock/<int:pk>/edit/', add_feed_stock, name='edit_feed_stock'),
    path('feed-stock/<int:pk>/delete/', delete_feed_stock, name='delete_feed_stock'),
    path('feeding-records/', feeding_records_list, name='feeding_records'),
    path('feeding-records/add/', add_feeding_record, name='add_feeding_record'),  # ✅ Add this
    path('sow/<uuid:sow_id>/weight/', sow_weight_profile, name='sow_weight_profile'),
    path('inactive/mark/', mark_inactive, name='mark_inactive'),
    path('inactive/list/', inactive_pigs_list, name='inactive_pigs_list'),
    path('api/active-pigs/', get_active_pigs, name='get_active_pigs'),
    path('inactive/reactivate/', reactivate_pig, name='reactivate_pig'),
    path('inseminations/', list_inseminations, name='insemination_list'),
    path('inseminations/add/', add_or_edit_insemination, name='add_insemination'),
    path('inseminations/edit/<uuid:insemination_id>/', add_or_edit_insemination, name='edit_insemination'),
    path('piglet/make-sow/', make_sow_from_piglet, name='make_sow_from_piglet'),
    path('breeding/records/', breeding_records_list, name='breeding_records_list'),
    path('breeding/add/', add_or_update_breeding_record, name='add_breeding_record'),
    path('breeding/edit/<uuid:record_id>/', add_or_update_breeding_record, name='edit_breeding_record'),
    path('breeding/delete/<uuid:record_id>/', views.delete_breeding_record, name='delete_breeding_record'),
    path('income/', income_list, name='income_list'),
    path('income/add/', add_or_update_income_record, name='add_income'),
    path('income/edit/<uuid:record_id>/', add_or_update_income_record, name='edit_income'),
    path('income/edit/<uuid:record_id>/', add_or_update_income_record, name='edit_income'),
    path('income/delete/<uuid:record_id>/', delete_income, name='delete_income'),
    path('sows/sell/', sell_sow, name='sell_sow'),
    path('piglets/<uuid:unique_id>/', piglet_profile, name='piglet_profile'),
    path('piglets/sell/', sell_piglet, name='sell_piglet'),
    path('expenses/', expense_list, name='expense_list'),
    path('expenses/add/', add_or_update_expense_record, name='add_expense'),
    path('expenses/edit/<uuid:record_id>/', add_or_update_expense_record, name='edit_expense'),
    path('expenses/delete/<uuid:record_id>/', delete_expense, name='delete_expense'),
    
]
    


