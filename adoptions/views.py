from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

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
            if settings.DEMO_MODE:
                # Public demo: validate the form but never store visitors' details
                messages.success(
                    request,
                    f'Thanks for trying the demo! Your request to adopt {pet.name} looks good, '
                    'but this is a demo site, so nothing was saved or sent.',
                )
            else:
                adoption_request = form.save(commit=False)
                adoption_request.pet = pet
                adoption_request.save()
                messages.success(
                    request,
                    f'Thank you! Your request to adopt {pet.name} was received. We will contact you soon.',
                )
            # Land on the confirmation message, not back down at the form
            return redirect(reverse('pet_detail', args=[pet.id]) + '#messages')
    else:
        form = AdoptionRequestForm()

    return render(request, 'pet_detail.html', {'pet': pet, 'form': form})