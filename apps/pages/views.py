from django.shortcuts import render
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
import markdown

from .models import EditablePage

# Create your views here.


class PageDetailView(DetailView):
    model = EditablePage
    template_name = "pages/page_detail.html"
    context_object_name = "page"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_editable"] = self.request.user.is_superuser
        # Convert markdown to HTML
        context["rendered_content"] = markdown.markdown(
            self.object.content, extensions=["extra", "codehilite", "tables"]
        )
        return context


class PageEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EditablePage
    template_name = "pages/page_edit.html"
    fields = ["title", "content"]
    slug_url_kwarg = "slug"

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        form.instance.last_modified_by = self.request.user
        form.instance.updated_at = timezone.now()
        messages.success(self.request, "Page updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("pages:hungerfight")
