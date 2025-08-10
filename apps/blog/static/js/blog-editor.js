document.addEventListener('DOMContentLoaded', function () {
    // Initialize toolbar buttons
    const toolbarButtons = document.querySelectorAll('.toolbar-btn');
    const contentField = document.querySelector('textarea[name="content"]');

    if (toolbarButtons.length && contentField) {
        toolbarButtons.forEach(button => {
            button.addEventListener('click', function () {
                const insertText = this.getAttribute('data-insert');
                if (insertText && contentField) {
                    const start = contentField.selectionStart;
                    const end = contentField.selectionEnd;
                    const text = contentField.value;

                    contentField.value = text.substring(0, start) + insertText + text.substring(end);
                    contentField.focus();
                    contentField.setSelectionRange(start + insertText.length, start + insertText.length);
                }
            });
        });
    }

    // Image upload zone functionality
    const imageUploadZone = document.getElementById('imageUploadZone');

    if (imageUploadZone && contentField) {
        // Handle drag and drop
        imageUploadZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        imageUploadZone.addEventListener('dragleave', function (e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });

        imageUploadZone.addEventListener('drop', function (e) {
            e.preventDefault();
            this.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleImageUpload(files[0]);
            }
        });

        // Handle paste from clipboard
        document.addEventListener('paste', function (e) {
            if (e.clipboardData && e.clipboardData.items) {
                for (let i = 0; i < e.clipboardData.items.length; i++) {
                    if (e.clipboardData.items[i].type.indexOf('image') !== -1) {
                        const file = e.clipboardData.items[i].getAsFile();
                        handleImageUpload(file);
                        break;
                    }
                }
            }
        });
    }

    function handleImageUpload(file) {
        if (!file || !file.type.startsWith('image/')) {
            return;
        }

        const formData = new FormData();
        formData.append('image', file);

        fetch('/blog/upload-image/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const imageMarkdown = `![${file.name}](${data.url})`;
                    insertAtCursor(imageMarkdown);
                } else {
                    console.error('Upload failed:', data.error);
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
            });
    }

    function insertAtCursor(text) {
        if (contentField) {
            const start = contentField.selectionStart;
            const end = contentField.selectionEnd;
            const currentText = contentField.value;

            contentField.value = currentText.substring(0, start) + text + currentText.substring(end);
            contentField.focus();
            contentField.setSelectionRange(start + text.length, start + text.length);
        }
    }
}); 