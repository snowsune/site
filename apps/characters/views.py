from django.shortcuts import render
import os
import markdown
from django.conf import settings

CHARACTER_DATA_DIR = os.path.join(settings.BASE_DIR, "apps", "characters", "char_data")


def character_list(request):
    """
    Lists all character markdown files as links, properly formatting names.
    """

    character_files = [
        {
            "filename": f.replace(".md", ""),
            "display_name": f.replace(".md", "").replace("_", " ").title(),
        }
        for f in os.listdir(CHARACTER_DATA_DIR)
        if f.endswith(".md")
    ]

    # Wrap the content in .character-content (for style)
    wrapped_content = f'<div class="character-content">{html_content}</div>'

    return render(
        request,
        "characters/detail.html",
        {
            "character_name": char_name.replace("_", " ").title(),
            "content": wrapped_content,
        },
    )


def character_detail(request, char_name):
    """
    Loads a character's markdown file, formats its name, and renders it.
    """
    char_path = os.path.join(CHARACTER_DATA_DIR, f"{char_name}.md")

    if not os.path.exists(char_path):
        return render(
            request,
            "characters/not_found.html",
            {"char_name": char_name.replace("_", " ").title()},
        )

    with open(char_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)

    return render(
        request,
        "characters/detail.html",
        {
            "character_name": char_name.replace("_", " ").title(),
            "content": html_content,
        },
    )
