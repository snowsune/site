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
            uploadFiles(e.dataTransfer.files);
        });

        const fileInput = document.getElementById('blogFileInput');
        const fileButton = document.getElementById('blogFileButton');
        if (fileButton && fileInput) {
            fileButton.addEventListener('click', function () {
                fileInput.click();
            });
            fileInput.addEventListener('change', function () {
                uploadFiles(fileInput.files);
                fileInput.value = '';
            });
        }

        document.addEventListener('paste', function (e) {
            if (!e.clipboardData) {
                return;
            }
            const files = [];
            for (const item of e.clipboardData.items || []) {
                if (item.type.indexOf('image') !== -1) {
                    files.push(item.getAsFile());
                }
            }
            if (files.length) {
                uploadFiles(files);
            }
        });
    }

    function uploadFiles(fileList) {
        const files = Array.from(fileList || []);
        if (!files.length) {
            return;
        }
        const maxBytes = Number(imageUploadZone.dataset.maxBytes) || (2 * 1024 * 1024 * 1024);
        let chain = Promise.resolve();
        files.forEach(function (file) {
            chain = chain.then(function () {
                return uploadOne(file, maxBytes);
            });
        });
    }

    function uploadOne(file, maxBytes) {
        if (file.size > maxBytes) {
            setUploadStatus(file.name + ' is too large.');
            return Promise.resolve();
        }
        const formData = new FormData();
        formData.append('file', file);
        const progress = document.getElementById('uploadProgress');
        const bar = document.getElementById('uploadProgressBar');
        if (progress) {
            progress.hidden = false;
        }
        return new Promise(function (resolve) {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/blog/upload-file/');
            const token = document.querySelector('[name=csrfmiddlewaretoken]');
            if (token) {
                xhr.setRequestHeader('X-CSRFToken', token.value);
            }
            xhr.upload.onprogress = function (event) {
                if (!event.lengthComputable || !bar) {
                    return;
                }
                const pct = Math.round((event.loaded / event.total) * 100);
                bar.style.width = pct + '%';
                setUploadStatus('Uploading ' + file.name + '… ' + pct + '%');
            };
            xhr.onload = function () {
                let data = {};
                try {
                    data = JSON.parse(xhr.responseText);
                } catch (e) {
                    data = {};
                }
                if (xhr.status >= 200 && xhr.status < 300 && data.success) {
                    insertAtCursor(data.markdown);
                    setUploadStatus('Added ' + file.name);
                } else {
                    setUploadStatus(data.error || 'Upload failed.');
                }
                resolve();
            };
            xhr.onerror = function () {
                setUploadStatus('Upload failed.');
                resolve();
            };
            xhr.send(formData);
        });
    }

    function setUploadStatus(message) {
        const status = document.getElementById('uploadStatus');
        if (!status) {
            return;
        }
        status.hidden = false;
        status.textContent = message;
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