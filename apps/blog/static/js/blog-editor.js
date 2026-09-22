document.addEventListener('DOMContentLoaded', function () {
    const toolbarButtons = document.querySelectorAll('.toolbar-btn');
    const contentField = document.querySelector('textarea[name="content"]');
    const imageUploadZone = document.getElementById('imageUploadZone');

    if (toolbarButtons.length && contentField) {
        toolbarButtons.forEach(function (button) {
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

    if (!imageUploadZone || !contentField || typeof Resumable === 'undefined') {
        return;
    }

    const maxBytes = Number(imageUploadZone.dataset.maxBytes) || (2 * 1024 * 1024 * 1024);
    const chunkBytes = Number(imageUploadZone.dataset.chunkBytes) || (4 * 1024 * 1024);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    const progress = document.getElementById('uploadProgress');
    const bar = document.getElementById('uploadProgressBar');

    const r = new Resumable({
        target: '/blog/upload-chunk/',
        chunkSize: chunkBytes,
        simultaneousUploads: 2,
        testChunks: true,
        throttleProgressCallbacks: 1,
        fileParameterName: 'file',
        headers: csrfToken ? { 'X-CSRFToken': csrfToken.value } : {},
    });

    if (!r.support) {
        setUploadStatus('Chunked uploads are not supported in this browser.');
        return;
    }

    const fileInput = document.getElementById('blogFileInput');
    const fileButton = document.getElementById('blogFileButton');
    if (fileButton && fileInput) {
        r.assignBrowse(fileInput);
        fileButton.addEventListener('click', function () {
            fileInput.click();
        });
    }
    r.assignDrop(imageUploadZone);

    imageUploadZone.addEventListener('dragover', function (e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });
    imageUploadZone.addEventListener('dragleave', function (e) {
        e.preventDefault();
        this.classList.remove('drag-over');
    });
    imageUploadZone.addEventListener('drop', function () {
        this.classList.remove('drag-over');
    });

    document.addEventListener('paste', function (e) {
        if (!e.clipboardData) {
            return;
        }
        for (const item of e.clipboardData.items || []) {
            if (item.type.indexOf('image') !== -1) {
                const file = item.getAsFile();
                if (file) {
                    r.addFile(file);
                }
            }
        }
    });

    r.on('fileAdded', function (file) {
        if (file.size > maxBytes) {
            r.removeFile(file);
            setUploadStatus(file.fileName + ' is too large.');
            return;
        }
        if (progress) {
            progress.hidden = false;
        }
        setUploadStatus('Uploading ' + file.fileName + '…');
        r.upload();
    });

    r.on('fileProgress', function (file) {
        const pct = Math.round(file.progress() * 100);
        if (bar) {
            bar.style.width = pct + '%';
        }
        setUploadStatus('Uploading ' + file.fileName + '… ' + pct + '%');
    });

    r.on('fileSuccess', function (file, message) {
        let data = {};
        try {
            data = JSON.parse(message || '{}');
        } catch (err) {
            data = {};
        }
        if (data.complete && data.markdown) {
            insertAtCursor(data.markdown);
            setUploadStatus('Added ' + file.fileName);
        } else if (data.error) {
            setUploadStatus(data.error);
        } else {
            setUploadStatus('Upload finished for ' + file.fileName);
        }
        if (bar) {
            bar.style.width = '100%';
        }
    });

    r.on('fileError', function (file, message) {
        let detail = message;
        try {
            const data = JSON.parse(message || '{}');
            detail = data.error || message;
        } catch (err) {
            // keep raw message
        }
        setUploadStatus(detail || ('Upload failed for ' + file.fileName));
    });

    function setUploadStatus(message) {
        const status = document.getElementById('uploadStatus');
        if (!status) {
            return;
        }
        status.hidden = false;
        status.textContent = message;
    }

    function insertAtCursor(text) {
        const start = contentField.selectionStart;
        const end = contentField.selectionEnd;
        const currentText = contentField.value;
        contentField.value = currentText.substring(0, start) + text + currentText.substring(end);
        contentField.focus();
        contentField.setSelectionRange(start + text.length, start + text.length);
    }
});
