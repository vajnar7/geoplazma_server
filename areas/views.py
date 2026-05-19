from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Serve the main frontend application."""
    template_name = 'index.html'


