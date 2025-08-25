// Vixi makes a simple drag and drop


document.addEventListener('DOMContentLoaded', function () {
    const uploadArea = document.querySelector('.upload-area');
    const fileInput = document.querySelector('input[type="file"]');

    // If the upload area or file input is not found, return
    if (!uploadArea || !fileInput) return;

    // Click to browse
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    // Drag leave (give up lol~)
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    // Drop (upload)
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            showReadyState();
        }
    });

    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            showReadyState();
        }
    });

    // Show the ready state (sets the upload area style to ready)
    function showReadyState() {
        const fileName = fileInput.files[0].name;
        uploadArea.classList.add('ready');
        uploadArea.querySelector('.upload-text').textContent = 'Ready to upload!';
        uploadArea.querySelector('.upload-hint').textContent = fileName;
    }

    function resetUploadArea() {
        uploadArea.classList.remove('ready');
        uploadArea.querySelector('.upload-text').textContent = 'Drag & Drop your image here';
        uploadArea.querySelector('.upload-hint').textContent = 'or click to browse';
    }
}); 