from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class MunchMakerView(LoginRequiredMixin, TemplateView):
    template_name = "munch_maker.html"
