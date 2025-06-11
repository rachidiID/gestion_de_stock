from django import forms
from .models import Produit, MouvementStock, Categorie, Fournisseur # Assurez-vous que tous les modèles sont importés ici
from django.forms.models import ModelChoiceField

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        # Tous les champs sauf quantite_actuelle (car elle est auto-gérée)
        fields = ['nom', 'description', 'code_barre', 'prix_unitaire', 'seuil_alerte_faible']
        # Vous pouvez personnaliser les widgets ou ajouter des labels ici si besoin
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'code_barre': forms.TextInput(attrs={'placeholder': 'Entrez le code-barres unique'}),
            'prix_unitaire': forms.NumberInput(attrs={'step': '0.01'}),
            'seuil_alerte_faible': forms.NumberInput(attrs={'min': '0'}),
        }
        labels = {
            'nom': 'Nom du Produit',
            'description': 'Description',
            'code_barre': 'Code-barres / Référence',
            'prix_unitaire': 'Prix Unitaire',
            'seuil_alerte_faible': 'Seuil d\'Alerte Faible',
        }

class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['produit', 'quantite', 'raison_mouvement', 'fournisseur']
        labels = {
            'produit': 'Produit',
            'quantite': 'Quantité',
            'raison_mouvement': 'Raison du mouvement (pour les sorties)',
            'fournisseur': 'Fournisseur (pour les entrées)',
        }
        widgets = {
            'raison_mouvement': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Vente, Casse, Consommation interne'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Manière propre et qui plaît à Pylance de définir le queryset pour un ModelChoiceField
        # Nous nous assurons que le champ 'produit' est bien un ModelChoiceField avant de modifier son queryset
        if 'produit' in self.fields and isinstance(self.fields['produit'], ModelChoiceField):
            self.fields['produit'].queryset = Produit.objects.all().order_by('nom')
        # Vous pourriez ajouter une condition pour les formulaires d'entrée/sortie si vous voulez filtrer
        # ex: self.fields['produit'].queryset = Produit.objects.filter(is_active=True).order_by('nom')

# AJOUT DE LA CLASSE CATEGORIEFORM ICI
class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom']
        labels = {
            'nom': 'Nom de la Catégorie',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Électronique, Alimentaire'}),
        }

# AJOUT DE LA CLASSE FOURNISSEURFORM ICI
class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact', 'adresse']
        labels = {
            'nom': 'Nom du Fournisseur',
            'contact': 'Contact (Email/Téléphone)',
            'adresse': 'Adresse',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Fournisseur A'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: contact@fournisseura.com, 0123456789'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ex: 123 Rue de la Forêt, Ville'}),
        }
        
class RapportMouvementsForm(forms.Form):
    """
    Formulaire pour la sélection des critères de génération de rapport de mouvements de stock.
    """
    date_debut = forms.DateField(
        label="Date de Début",
        required=False, # Pas obligatoire, si l'utilisateur veut tout l'historique
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}) # Widget HTML5 pour date
    )
    date_fin = forms.DateField(
        label="Date de Fin",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all().order_by('nom'), # Liste de tous les produits
        label="Produit (Optionnel)",
        required=False,
        empty_label="-- Tous les produits --", # Option pour ne pas filtrer par produit
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    type_mouvement = forms.ChoiceField(
        choices=[('', '-- Tous les types --')] + MouvementStock.TYPE_MOUVEMENT_CHOICES, # Ajouter une option "Tous"
        label="Type de Mouvement (Optionnel)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Validation personnalisée pour s'assurer que la date de début est avant la date de fin
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_debut > date_fin:
            self.add_error('date_fin', "La date de fin ne peut pas être antérieure à la date de début.")
        return cleaned_data