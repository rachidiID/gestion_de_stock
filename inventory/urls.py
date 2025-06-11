# inventory/urls.py
from django.urls import path
from . import views # Cet import est correct ici

urlpatterns = [
    # Page d'accueil de l'application (sera la racine de l'URL incluse)
    path('', views.home_view, name='home'),

    # URLs pour les Produits
    path('products/', views.product_list_view, name='product_list'),
    path('products/add/', views.product_add_view, name='product_add'),
    path('products/edit/<int:pk>/', views.product_edit_view, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete_view, name='product_delete'),

    # URLs pour les Catégories
    path('categories/', views.categorie_list_view, name='categorie_list'),
    path('categories/add/', views.categorie_add_view, name='categorie_add'),
    path('categories/edit/<int:pk>/', views.categorie_edit_view, name='categorie_edit'),
    path('categories/delete/<int:pk>/', views.categorie_delete_view, name='categorie_delete'),

    # URLs pour les Fournisseurs
    path('fournisseurs/', views.fournisseur_list_view, name='fournisseur_list'),
    path('fournisseurs/add/', views.fournisseur_add_view, name='fournisseur_add'),
    path('fournisseurs/edit/<int:pk>/', views.fournisseur_edit_view, name='fournisseur_edit'),
    path('fournisseurs/delete/<int:pk>/', views.fournisseur_delete_view, name='fournisseur_delete'),

    # URLs pour les Mouvements de Stock
    path('stock_in/', views.stock_in_view, name='stock_in'),
    path('stock_out/', views.stock_out_view, name='stock_out'),

    # URLs pour les Alertes
    path('alerts/', views.alert_list_view, name='alert_list'),
    
    # URLs pour les Rapports et Exports
    path('reports/', views.report_generation_view, name='report_generation'),
    path('reports/export/csv/', views.export_movements_csv, name='export_movements_csv'),
    path('reports/export/pdf/', views.export_movements_pdf, name='export_movements_pdf'),
]