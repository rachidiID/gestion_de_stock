from django.contrib import admin
from .models import Categorie, Produit, MouvementStock, Fournisseur

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact')
    search_fields = ('nom', 'contact')

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_barre', 'quantite_actuelle', 'prix_unitaire', 'categorie', 'seuil_alerte_faible', 'est_stock_faible_display', 'est_en_rupture_display')
    list_filter = ('categorie', 'quantite_actuelle')
    search_fields = ('nom', 'code_barre')
    readonly_fields = ('quantite_actuelle',)

    # Utilisez le décorateur admin.display
    @admin.display(boolean=True, description="Stock faible")
    def est_stock_faible_display(self, obj):
        return obj.est_stock_faible

    @admin.display(boolean=True, description="Rupture de stock")
    def est_en_rupture_display(self, obj):
        return obj.est_en_rupture

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('produit', 'type_mouvement', 'quantite', 'date_mouvement', 'utilisateur', 'fournisseur', 'raison_mouvement')
    list_filter = ('type_mouvement', 'date_mouvement', 'utilisateur', 'produit__categorie')
    search_fields = ('produit__nom', 'raison_mouvement', 'fournisseur__nom')
    date_hierarchy = 'date_mouvement' # Permet de naviguer par date

    # Pour que l'utilisateur qui enregistre le mouvement soit automatiquement le user connecté
    def save_model(self, request, obj, form, change):
        if not obj.pk: # Si c'est un nouvel objet
            obj.utilisateur = request.user
        super().save_model(request, obj, form, change)