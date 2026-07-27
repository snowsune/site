/**
 * Embedding modal for the matrix widget!~
 */
(function () {
  function init() {
    const modal = document.getElementById("matrix-widget-modal");
    const iframe = document.getElementById("matrix-widget-iframe");
    if (!modal || !iframe) return;

    const openers = document.querySelectorAll(".js-matrix-widget-open");

    function openModal(event) {
      if (event) event.preventDefault();
      if (!iframe.getAttribute("src")) {
        iframe.setAttribute("src", iframe.dataset.src);
      }
      modal.showModal();
    }

    function closeModal() {
      if (modal.open) modal.close();
    }

    openers.forEach((el) => el.addEventListener("click", openModal));

    // Close when clicking the backdrop (outside the dialog box)
    modal.addEventListener("click", (event) => {
      const rect = modal.getBoundingClientRect();
      const inside =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;
      if (!inside) closeModal();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
