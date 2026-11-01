from django.db import models

# Create your models here.
class Pet(models.Model):
    SEX_CHOICE = [('M','Male'),('F','Female')]
    name = models.CharField(max_length=100)
    submitter = models.CharField(max_length=100)
    species = models.CharField(max_length=30)
    breed = models.CharField(max_length=30, blank=True)
    description = models.TextField()
    sex = models.CharField(max_length=1, choices= SEX_CHOICE, blank=True)
    submission_date = models.DateTimeField()
    age = models.IntegerField(null=True)
    vaccinations = models.ManyToManyField('Vaccine', blank=True)

    def __str__(self):
        return f'{self.name} ({self.species})'


class Vaccine(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class AdoptionRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    ]
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='adoption_requests')
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(help_text='Tell us a little about yourself and your home.')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.full_name} for {self.pet.name}'