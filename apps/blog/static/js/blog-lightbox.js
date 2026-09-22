document.addEventListener("DOMContentLoaded", function () {
    const content = document.querySelector(".post-content.markdown-content");
    if (!content) {
        return;
    }

    const dialog = document.createElement("dialog");
    dialog.className = "blog-lightbox";
    dialog.innerHTML = "<img alt=\"\">";
    document.body.appendChild(dialog);
    const full = dialog.querySelector("img");

    content.addEventListener("click", function (event) {
        const img = event.target.closest("img");
        if (!img || !content.contains(img)) {
            return;
        }
        full.src = img.currentSrc || img.src;
        full.alt = img.alt || "";
        dialog.showModal();
    });

    dialog.addEventListener("click", function () {
        dialog.close();
    });
});
