from django.db import models
from django.contrib.auth.models import User

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Catégories" # Pour une meilleure lisibilité dans l'admin

    def __str__(self):
        return self.nom

class Fournisseur(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    contact = models.CharField(max_length=200, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Fournisseurs"

    def __str__(self):
        return self.nom

class Produit(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    code_barre = models.CharField(max_length=100, unique=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    # La quantité actuelle sera mise à jour par les mouvements, pas saisie manuellement
    quantite_actuelle = models.IntegerField(default=0, editable=False) # editable=False cache ce champ dans les formulaires admin par défaut
    seuil_alerte_faible = models.IntegerField(default=10)
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Produits"

    def __str__(self):
        return self.nom

    @property
    def est_stock_faible(self):
        return self.quantite_actuelle <= self.seuil_alerte_faible and self.quantite_actuelle > 0 # Ajouté > 0 pour ne pas alerter si stock vide et non géré

    @property
    def est_en_rupture(self):
        return self.quantite_actuelle == 0


class MouvementStock(models.Model):
    TYPE_MOUVEMENT_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'sortie'),
    ]
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=10, choices=TYPE_MOUVEMENT_CHOICES)
    quantite = models.IntegerField()
    date_mouvement = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    raison_mouvement = models.TextField(blank=True, null=True) # Ex: "Vente", "Retour", "Casse"
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
                                    help_text="Sélectionner un fournisseur si c'est une entrée de stock.")


    class Meta:
        ordering = ['-date_mouvement'] # Tri par date la plus récente
        verbose_name_plural = "Mouvements de Stock"


    def __str__(self):
        return f"{self.type_mouvement.capitalize()} de {self.quantite} {self.produit.nom} le {self.date_mouvement.strftime('%Y-%m-%d %H:%M')}"

    # Logique pour mettre à jour la quantité du produit lors de la sauvegarde du mouvement
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) # Sauvegarde d'abord le mouvement

        # Met à jour la quantité actuelle du produit
        produit = self.produit
        if self.type_mouvement == 'entree':
            produit.quantite_actuelle += self.quantite
        elif self.type_mouvement == 'sortie':
            produit.quantite_actuelle -= self.quantite
        produit.save() # Sauvegarde le produit mis à jour

    # Logique pour annuler la mise à jour de la quantité si le mouvement est supprimé
    def delete(self, *args, **kwargs):
        produit = self.produit
        if self.type_mouvement == 'entree':
            produit.quantite_actuelle -= self.quantite
        elif self.type_mouvement == 'sortie':
            produit.quantite_actuelle += self.quantite
        produit.save()
        return super().delete(*args, **kwargs)