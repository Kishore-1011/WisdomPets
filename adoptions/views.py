from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AdoptionRequestForm
from .models import Pet

# Create your views here.


def home(request):
    query = request.GET.get('q', '').strip()
    species = request.GET.get('species', '').strip()

    pets = Pet.objects.all()
    if query:
        pets = pets.filter(
            Q(name__icontains=query)
            | Q(breed__icontains=query)
            | Q(description__icontains=query)
        )
    if species:
        pets = pets.filter(species__iexact=species)

    species_list = Pet.objects.order_by('species').values_list('species', flat=True).distinct()

    return render(request, 'home.html', {
        'pets': pets,
        'query': query,
        'selected_species': species,
        'species_list': species_list,
        'is_filtered': bool(query or species),
    })


def pet_detail(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)

    if request.method == 'POST':
        form = AdoptionRequestForm(request.POST)
        if form.is_valid():
            adoption_request = form.save(commit=False)
            adoption_request.pet = pet
            adoption_request.save()
            messages.success(
                request,
                f'Thank you! Your request to adopt {pet.name} was received. We will contact you soon.',
            )
            return redirect('pet_detail', pet_id=pet.id)
    else:
        form = AdoptionRequestForm()

    return render(request, 'pet_detail.html', {'pet': pet, 'form': form})