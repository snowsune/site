from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView
from django.http import Http404
from .models import CustomPage


class CustomPageDetailView(DetailView):
    """View for displaying custom pages"""

    model = CustomPage
    template_name = "custompages/page_detail.html"
    context_object_name = "page"
    slug_field = "path"
    slug_url_kwarg = "path"

    def get_queryset(self):
        """Only show published pages unless user is staff"""
        queryset = CustomPage.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        return queryset

    def get_object(self, queryset=None):
        """Get the page object by path"""
        if queryset is None:
            queryset = self.get_queryset()

        path = self.kwargs.get(self.slug_url_kwarg)
        if path is None:
            raise Http404("No path provided.")

        try:
            obj = queryset.get(path=path)
        except CustomPage.DoesNotExist:
            raise Http404("No custom page found matching the path.")
        except Exception:
            # Catch database connection errors and return 404 instead of 500
            raise Http404("Error loading page.")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = context["page"]

        # Parse sidebar links
        sidebar_links = []
        if page.sidebar_links and isinstance(page.sidebar_links, list):
            sidebar_links = page.sidebar_links

        context["sidebar_links"] = sidebar_links
        return context
