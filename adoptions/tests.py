from datetime import datetime, timezone
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import AdoptionRequestForm
from .models import AdoptionRequest, Pet, Vaccine


def make_pet(**kwargs):
    defaults = {
        'name': 'Rio',
        'submitter': 'Philip Ransu',
        'species': 'Dog',
        'breed': 'French bulldog',
        'description': 'Loves to play ball with his best dog friend.',
        'sex': 'M',
        'age': 5,
        'submission_date': datetime(2016, 11, 28, 13, 30, tzinfo=timezone.utc),
    }
    defaults.update(kwargs)
    return Pet.objects.create(**defaults)


class ModelTests(TestCase):
    def test_pet_str_includes_species(self):
        pet = make_pet()
        self.assertEqual(str(pet), 'Rio (Dog)')

    def test_adoption_request_defaults_to_new(self):
        request = AdoptionRequest.objects.create(
            pet=make_pet(), full_name='Asha Rao', email='asha@example.com', message='Hello'
        )
        self.assertEqual(request.status, 'new')
        self.assertEqual(str(request), 'Asha Rao for Rio')

    def test_adoption_requests_newest_first(self):
        pet = make_pet()
        first = AdoptionRequest.objects.create(pet=pet, full_name='A', email='a@example.com', message='x')
        second = AdoptionRequest.objects.create(pet=pet, full_name='B', email='b@example.com', message='x')
        self.assertEqual(list(AdoptionRequest.objects.all()), [second, first])


class HomeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        make_pet(name='Rio', species='Dog', breed='French bulldog')
        make_pet(name='Scout', species='Dog', breed='Jack Russell terrier')
        make_pet(name='Fluffy', species='Cat', breed='Domestic longhair')
        make_pet(name='Pepe', species='Rabbit', breed='')

    def get(self, **params):
        return self.client.get(reverse('home'), params)

    def test_lists_all_pets(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['pets']), 4)
        self.assertContains(response, 'Breed unknown')

    def test_filter_by_species_is_case_insensitive(self):
        response = self.get(species='dog')
        names = {pet.name for pet in response.context['pets']}
        self.assertEqual(names, {'Rio', 'Scout'})

    def test_search_matches_breed(self):
        response = self.get(q='TERRIER')
        self.assertEqual([pet.name for pet in response.context['pets']], ['Scout'])

    def test_search_and_species_combined(self):
        response = self.get(q='terrier', species='Cat')
        self.assertEqual(len(response.context['pets']), 0)
        self.assertContains(response, 'No pets match your search')

    def test_species_list_is_distinct_and_sorted(self):
        response = self.get()
        self.assertEqual(list(response.context['species_list']), ['Cat', 'Dog', 'Rabbit'])

    def test_search_input_is_escaped(self):
        response = self.get(q='<script>alert(1)</script>')
        self.assertNotContains(response, '<script>alert(1)</script>')


class PetDetailViewTests(TestCase):
    def setUp(self):
        self.pet = make_pet()
        self.url = reverse('pet_detail', args=[self.pet.id])

    def test_shows_pet_details_and_vaccinations(self):
        self.pet.vaccinations.add(Vaccine.objects.create(name='Canine Rabies'))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'French bulldog')
        self.assertContains(response, 'Canine Rabies')
        self.assertContains(response, 'Male')

    def test_age_zero_shows_under_one_year(self):
        pet = make_pet(name='Pepe', age=0)
        response = self.client.get(reverse('pet_detail', args=[pet.id]))
        self.assertContains(response, 'Under 1 year')

    def test_missing_pet_returns_404(self):
        response = self.client.get(reverse('pet_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)


class AdoptionRequestTests(TestCase):
    def setUp(self):
        self.pet = make_pet()
        self.url = reverse('pet_detail', args=[self.pet.id])
        self.valid_data = {
            'full_name': 'Asha Rao',
            'email': 'asha@example.com',
            'phone': '+91 98765 43210',
            'message': 'I have a big garden and work from home.',
        }

    def test_valid_request_is_saved_and_redirects(self):
        response = self.client.post(self.url, self.valid_data, follow=True)
        self.assertRedirects(response, self.url)
        self.assertContains(response, 'Your request to adopt Rio was received')
        request = AdoptionRequest.objects.get()
        self.assertEqual(request.pet, self.pet)
        self.assertEqual(request.email, 'asha@example.com')

    def test_missing_required_fields_are_rejected(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AdoptionRequest.objects.count(), 0)
        self.assertEqual(set(response.context['form'].errors), {'full_name', 'email', 'message'})

    def test_invalid_email_is_rejected(self):
        response = self.client.post(self.url, {**self.valid_data, 'email': 'not-an-email'})
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(AdoptionRequest.objects.count(), 0)

    def test_phone_is_optional(self):
        form = AdoptionRequestForm(data={**self.valid_data, 'phone': ''})
        self.assertTrue(form.is_valid())

    def test_invalid_phone_is_rejected(self):
        form = AdoptionRequestForm(data={**self.valid_data, 'phone': 'call me maybe'})
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_post_without_csrf_token_is_blocked(self):
        self.client.handler.enforce_csrf_checks = True
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AdoptionRequest.objects.count(), 0)


class LoadPetDataCommandTests(TestCase):
    def run_command(self):
        out = StringIO()
        call_command('load_pet_data', stdout=out)
        return out.getvalue()

    def test_loads_pets_and_vaccines_from_csv(self):
        self.run_command()
        self.assertEqual(Pet.objects.count(), 24)
        self.assertEqual(Vaccine.objects.count(), 7)
        self.assertTrue(Pet.objects.filter(vaccinations__isnull=False).exists())

    def test_keeps_special_characters(self):
        self.run_command()
        self.assertIn('she’s', Pet.objects.get(name='Chyna').description)

    def test_second_run_does_not_duplicate_data(self):
        self.run_command()
        output = self.run_command()
        self.assertIn('already loaded', output)
        self.assertEqual(Pet.objects.count(), 24)
