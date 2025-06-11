# inventory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db import models, transaction
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

# Imports pour les modèles
from .models import Produit, Categorie, MouvementStock, Fournisseur
# Imports pour les formulaires (assurez-vous que tous sont définis dans forms.py)
from .forms import ProduitForm, MouvementStockForm, RapportMouvementsForm, CategorieForm, FournisseurForm

# Imports pour les réponses HTTP (export CSV/PDF)
from django.http import HttpResponse # Importé ici car utilisé pour HttpResponse
import csv # Pour la génération CSV
import io # Pour gérer les fichiers en mémoire (pour PDF)

# Imports pour l'export PDF (assurez-vous d'avoir pip install reportlab)
from reportlab.lib.pagesizes import letter, A4 # A4 est plus commun en Europe
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch # Ajouté ici, car il était potentiellement manquant


# Helper pour vérifier si l'utilisateur est administrateur (peut être basé sur le groupe ou is_staff)
def is_admin(user):
    return user.is_staff or user.groups.filter(name='Administrateurs').exists()

# Helper pour vérifier si l'utilisateur est employé (ou fait partie du groupe Employés)
def is_employee(user):
    return user.groups.filter(name='Employés').exists()


# --- Vues Générales ---

@login_required
def home_view(request):
    low_stock_products = Produit.objects.filter(quantite_actuelle__lte=models.F('seuil_alerte_faible'), quantite_actuelle__gt=0).order_by('nom')

    total_products = Produit.objects.count()
    total_low_stock_products = low_stock_products.count()
    total_out_of_stock_products = Produit.objects.filter(quantite_actuelle=0).count()

    recent_movements = MouvementStock.objects.all().order_by('-date_mouvement')[:5]

    today = date.today()
    one_month_ago = today - relativedelta(months=1)

    total_in_last_month = MouvementStock.objects.filter(
        date_mouvement__gte=one_month_ago,
        type_mouvement='entree'
    ).aggregate(total_qty=Coalesce(Sum('quantite'), 0))['total_qty']

    total_out_last_month = MouvementStock.objects.filter(
        date_mouvement__gte=one_month_ago,
        type_mouvement='sortie'
    ).aggregate(total_qty=Coalesce(Sum('quantite'), 0))['total_qty']

    context = {
        'low_stock_products': low_stock_products,
        'total_products': total_products,
        'total_low_stock_products': total_low_stock_products,
        'total_out_of_stock_products': total_out_of_stock_products,
        'recent_movements': recent_movements,
        'total_in_last_month': total_in_last_month,
        'total_out_last_month': total_out_last_month,
    }
    return render(request, 'inventory/home.html', context)


# Vue personnalisée pour la déconnexion
def custom_logout_view(request):
    auth_logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')


# --- Vues pour les Produits ---

@login_required
def product_list_view(request):
    products = Produit.objects.all()
    query = request.GET.get('q')
    if query:
        products = products.filter(
            models.Q(nom__icontains=query) |
            models.Q(code_barre__icontains=query)
        ).distinct()
    products = products.order_by('nom')
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'inventory/product_list.html', context)


@permission_required('inventory.add_produit', raise_exception=True)
def product_add_view(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Le produit '{product.nom}' a été ajouté avec succès.")
            return redirect('product_list')
    else:
        form = ProduitForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/product_form.html', context)


@permission_required('inventory.change_produit', raise_exception=True)
def product_edit_view(request, pk):
    product = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le produit '{product.nom}' a été mis à jour avec succès.")
            return redirect('product_list')
    else:
        form = ProduitForm(instance=product)

    context = {
        'form': form,
        'product': product,
    }
    return render(request, 'inventory/product_form.html', context)


@permission_required('inventory.delete_produit', raise_exception=True)
def product_delete_view(request, pk):
    product = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f"Le produit '{product.nom}' a été supprimé avec succès.")
        return redirect('product_list')
    context = {
        'product': product,
    }
    return render(request, 'inventory/product_confirm_delete.html', context)


# --- Vues pour les Catégories ---

@login_required
def categorie_list_view(request):
    categories = Categorie.objects.all().order_by('nom')
    context = {
        'categories': categories,
    }
    return render(request, 'inventory/categorie_list.html', context)


@permission_required('inventory.add_categorie', raise_exception=True)
def categorie_add_view(request):
    if request.method == 'POST':
        form = CategorieForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"La catégorie '{category.nom}' a été ajoutée avec succès.")
            return redirect('categorie_list')
    else:
        form = CategorieForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/categorie_form.html', context)


@permission_required('inventory.change_categorie', raise_exception=True)
def categorie_edit_view(request, pk):
    category = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        form = CategorieForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"La catégorie '{category.nom}' a été mise à jour avec succès.")
            return redirect('categorie_list')
    else:
        form = CategorieForm(instance=category)

    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'inventory/categorie_form.html', context)


@permission_required('inventory.delete_categorie', raise_exception=True)
def categorie_delete_view(request, pk):
    category = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, f"La catégorie '{category.nom}' a été supprimée avec succès.")
            return redirect('categorie_list')
        except models.ProtectedError:
            messages.error(request, f"Impossible de supprimer la catégorie '{category.nom}' car elle contient des produits.")
            return redirect('categorie_list')
    context = {
        'category': category,
    }
    return render(request, 'inventory/categorie_confirm_delete.html', context)


# --- Vues pour les Fournisseurs ---

@login_required
def fournisseur_list_view(request):
    fournisseurs = Fournisseur.objects.all().order_by('nom')
    context = {
        'fournisseurs': fournisseurs,
    }
    return render(request, 'inventory/fournisseur_list.html', context)


@permission_required('inventory.add_fournisseur', raise_exception=True)
def fournisseur_add_view(request):
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            fournisseur = form.save()
            messages.success(request, f"Le fournisseur '{fournisseur.nom}' a été ajouté avec succès.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/fournisseur_form.html', context)


@permission_required('inventory.change_fournisseur', raise_exception=True)
def fournisseur_edit_view(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le fournisseur '{fournisseur.nom}' a été mis à jour avec succès.")
            return redirect('fournisseur_list')
    else:
        form = FournisseurForm(instance=fournisseur)

    context = {
        'form': form,
        'fournisseur': fournisseur,
    }
    return render(request, 'inventory/fournisseur_form.html', context)


@permission_required('inventory.delete_fournisseur', raise_exception=True)
def fournisseur_delete_view(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    if request.method == 'POST':
        try:
            fournisseur.delete()
            messages.success(request, f"Le fournisseur '{fournisseur.nom}' a été supprimé avec succès.")
            return redirect('fournisseur_list')
        except models.ProtectedError:
            messages.error(request, f"Impossible de supprimer le fournisseur '{fournisseur.nom}' car il est lié à des mouvements de stock.")
            return redirect('fournisseur_list')
    context = {
        'fournisseur': fournisseur,
    }
    return render(request, 'inventory/fournisseur_confirm_delete.html', context)


# --- Vues pour les Mouvements de Stock (Réception/Sortie) ---

@permission_required('inventory.add_mouvementstock', raise_exception=True)
def stock_in_view(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            mouvement = form.save(commit=False)
            mouvement.type_mouvement = 'entree'
            mouvement.utilisateur = request.user
            mouvement.save()

            messages.success(request, f"Réception de {mouvement.quantite} unités de '{mouvement.produit.nom}' enregistrée avec succès.")
            return redirect('product_list')
    else:
        form = MouvementStockForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/stock_in_form.html', context)


@permission_required('inventory.add_mouvementstock', raise_exception=True)
def stock_out_view(request):
    if request.method == 'POST':
        form = MouvementStockForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            quantite_sortie = form.cleaned_data['quantite']

            if quantite_sortie > produit.quantite_actuelle:
                messages.error(request, f"Erreur : La quantité de sortie ({quantite_sortie}) dépasse le stock actuel ({produit.quantite_actuelle}) pour '{produit.nom}'.")
            else:
                mouvement = form.save(commit=False)
                mouvement.type_mouvement = 'sortie'
                mouvement.utilisateur = request.user
                mouvement.save()

                messages.success(request, f"Sortie de {mouvement.quantite} unités de '{mouvement.produit.nom}' enregistrée avec succès.")
                return redirect('product_list')
    else:
        form = MouvementStockForm()

    context = {
        'form': form,
    }
    return render(request, 'inventory/stock_out_form.html', context)


# --- Vues pour les Alertes et Rapports ---

@login_required
def alert_list_view(request):
    low_stock_products = Produit.objects.filter(
        models.Q(quantite_actuelle__lte=models.F('seuil_alerte_faible'))
    ).order_by('nom')
    context = {
        'low_stock_products': low_stock_products,
    }
    return render(request, 'inventory/alert_list.html', context)


@permission_required('inventory.view_mouvementstock', raise_exception=True)
@user_passes_test(is_admin, login_url='/login/', redirect_field_name='')
def report_generation_view(request):
    form = RapportMouvementsForm(request.GET or None)
    movements = None
    if form.is_valid():
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        produit = form.cleaned_data.get('produit')
        type_mouvement = form.cleaned_data.get('type_mouvement')

        movements = MouvementStock.objects.all()

        if date_debut:
            movements = movements.filter(date_mouvement__gte=date_debut)
        if date_fin:
            movements = movements.filter(date_mouvement__lt=date_fin + timedelta(days=1))
        if produit:
            movements = movements.filter(produit=produit)
        if type_mouvement:
            movements = movements.filter(type_mouvement=type_mouvement)

        movements = movements.order_by('-date_mouvement')

    context = {
        'form': form,
        'movements': movements,
    }
    return render(request, 'inventory/report_form.html', context)


# --- Vues pour l'Export de Rapports ---

@permission_required('inventory.view_mouvementstock', raise_exception=True)
@user_passes_test(is_admin, login_url='/login/', redirect_field_name='')
def export_movements_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rapport_mouvements.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Produit', 'Code Barre', 'Type Mouvement', 'Quantite', 'Raison Mouvement', 'Utilisateur', 'Fournisseur'])

    form = RapportMouvementsForm(request.GET)
    movements = MouvementStock.objects.all()
    if form.is_valid():
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        produit = form.cleaned_data.get('produit')
        type_mouvement = form.cleaned_data.get('type_mouvement')

        if date_debut:
            movements = movements.filter(date_mouvement__gte=date_debut)
        if date_fin:
            movements = movements.filter(date_mouvement__lt=date_fin + timedelta(days=1))
        if produit:
            movements = movements.filter(produit=produit)
        if type_mouvement:
            movements = movements.filter(type_mouvement=type_mouvement)

    movements = movements.order_by('-date_mouvement')

    for movement in movements:
        writer.writerow([
            movement.date_mouvement.strftime('%Y-%m-%d %H:%M:%S'),
            movement.produit.nom,
            movement.produit.code_barre,
            movement.get_type_mouvement_display(),
            movement.quantite,
            movement.raison_mouvement if movement.raison_mouvement else '',
            movement.utilisateur.username if movement.utilisateur else 'N/A',
            movement.fournisseur.nom if movement.fournisseur else '',
        ])
    return response


@permission_required('inventory.view_mouvementstock', raise_exception=True)
@user_passes_test(is_admin, login_url='/login/', redirect_field_name='')
def export_movements_pdf(request):
    # Utilise BytesIO pour écrire le PDF en mémoire
    buffer = io.BytesIO() # <<< CORRECTION ICI
    doc = SimpleDocTemplate(buffer, pagesize=A4) # <<< CORRECTION ICI

    elements = []
    styles = getSampleStyleSheet()

    # Titre du rapport
    title_style = styles['h1']
    title_style.alignment = 1 # Centre
    elements.append(Paragraph("Rapport des Mouvements de Stock", title_style))
    elements.append(Paragraph("<br/><br/>", styles['Normal'])) # Espace

    # Récupérer les mouvements de stock avec les mêmes filtres
    form = RapportMouvementsForm(request.GET)
    movements = MouvementStock.objects.all()
    if form.is_valid():
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        produit = form.cleaned_data.get('produit')
        type_mouvement = form.cleaned_data.get('type_mouvement')

        if date_debut:
            elements.append(Paragraph(f"De: {date_debut.strftime('%d/%m/%Y')}", styles['Normal']))
            movements = movements.filter(date_mouvement__gte=date_debut)
        if date_fin:
            elements.append(Paragraph(f"À: {date_fin.strftime('%d/%m/%Y')}", styles['Normal']))
            movements = movements.filter(date_mouvement__lt=date_fin + timedelta(days=1))
        if produit:
            elements.append(Paragraph(f"Produit: {produit.nom}", styles['Normal']))
            movements = movements.filter(produit=produit)
        if type_mouvement:
            elements.append(Paragraph(f"Type de Mouvement: {dict(MouvementStock.TYPE_MOUVEMENT_CHOICES).get(type_mouvement, type_mouvement)}", styles['Normal']))
            movements = movements.filter(type_mouvement=type_mouvement)
        
        elements.append(Paragraph("<br/>", styles['Normal'])) # Espace
        
    movements = movements.order_by('-date_mouvement')

    # Préparer les données pour le tableau PDF
    data = [
        ['Date', 'Produit', 'Type Mouvement', 'Quantité', 'Raison Mouvement', 'Utilisateur', 'Fournisseur']
    ]
    for movement in movements:
        data.append([
            movement.date_mouvement.strftime('%Y-%m-%d %H:%M:%S'),
            movement.produit.nom + ' (' + movement.produit.code_barre + ')',
            movement.get_type_mouvement_display(),
            str(movement.quantite), # Convertir en chaîne
            movement.raison_mouvement if movement.raison_mouvement else '',
            movement.utilisateur.username if movement.utilisateur else 'N/A',
            movement.fournisseur.nom if movement.fournisseur else '',
        ])

    # Créer le tableau
    table = Table(data, colWidths=[1.3*inch, 1.8*inch, 1*inch, 0.8*inch, 1.5*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')), # Couleur de l'entête
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('FONTSIZE', (0,0), (-1,-1), 8), # Taille de police réduite
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('WORDWRAP', (1,1), (1,-1), True), # En cas de noms de produits longs
        ('WORDWRAP', (4,1), (4,-1), True), # En cas de raisons longues
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0) # Ramène le curseur au début du buffer
    return HttpResponse(buffer.getvalue(), content_type='application/pdf') 