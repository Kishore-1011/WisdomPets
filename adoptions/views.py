from django.db.models import Q
from django.shortcuts import render
from django.http import Http404
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
    try:
        pet = Pet.objects.get(id = pet_id)
    except Pet.DoesNotExist:
        raise Http404('Pet not found')
    
    return render(request, 'pet_detail.html', {'pet':pet})