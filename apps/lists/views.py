from django.http import Http404
from django.shortcuts import render

from .data import LISTS, get_item, get_list


def lists_index(request):
    return render(request, "lists/index.html", {"lists": LISTS.values()})


def list_detail(request, list_slug):
    lst = get_list(list_slug)
    if not lst:
        raise Http404("List not found")
    return render(request, "lists/list_grid.html", {"list": lst})


def item_detail(request, list_slug, item_slug):
    lst, item = get_item(list_slug, item_slug)
    if not item:
        raise Http404("Item not found")
    return render(request, "lists/item_detail.html", {"list": lst, "item": item})
