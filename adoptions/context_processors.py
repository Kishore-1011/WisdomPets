from django.conf import settings


def demo_mode(request):
    """Lets every template know whether this is the public demo site."""
    return {'demo_mode': settings.DEMO_MODE}
