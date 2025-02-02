from django.shortcuts import render
import os
import markdown
from django.conf import settings

CHARACTER_DATA_DIR = os.path.join(settings.BASE_DIR, "apps", "characters", "char_data")


def character_list(request):
    """
    Lists all character markdown files as links
    """

    character_files = [
        f.replace(".md", "")
        for f in os.listdir(CHARACTER_DATA_DIR)
        if f.endswith(".md")
    ]

    return render(request, "characters/list.html", {"characters": character_files})


def character_detail(request, char_name):
    """
    Loads a character's markdown file and renders it

    TODO: Rendering lol
    """

    char_path = os.path.join(CHARACTER_DATA_DIR, f"{char_name}.md")

    if not os.path.exists(char_path):
        return render(request, "characters/not_found.html", {"char_name": char_name})

    with open(char_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)  # Convert Markdown to HTML

    return render(
        request,
        "characters/detail.html",
        {"character_name": char_name, "content": html_content},
    )
