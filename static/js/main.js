document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const processBtn = document.getElementById('processBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const processStatus = document.getElementById('processStatus');
    const filesList = document.getElementById('filesList');
    const fileInput = document.getElementById('fileInput');
    const selectedFiles = document.getElementById('selectedFiles');
    const downloadAllBtn = document.getElementById('downloadAllBtn');

    // Load initial file list
    loadFiles();

    // Handle file selection
    fileInput.addEventListener('change', () => {
        updateSelectedFilesList();
    });

    // Handle file upload
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const files = fileInput.files;

        if (!files.length) {
            showStatus(uploadStatus, 'Vennligst velg minst én fil', 'error');
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showStatus(uploadStatus, data.message, 'success');
                fileInput.value = '';
                selectedFiles.innerHTML = '';
                loadFiles();
            } else {
                showStatus(uploadStatus, data.error, 'error');
            }
        } catch (error) {
            showStatus(uploadStatus, 'Feil ved opplasting av filer', 'error');
        }
    });

    // Handle file processing
    processBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/process', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                showStatus(processStatus, data.message, 'success');
                loadFiles();
            } else {
                showStatus(processStatus, data.error, 'error');
            }
        } catch (error) {
            showStatus(processStatus, 'Feil ved prosessering av filer', 'error');
        }
    });

    // Handle download all files
    downloadAllBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/download-all');
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'processed_files.zip';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const data = await response.json();
                showStatus(processStatus, data.error, 'error');
            }
        } catch (error) {
            showStatus(processStatus, 'Feil ved nedlasting av filer', 'error');
        }
    });

    // Load and display processed files
    async function loadFiles() {
        try {
            const response = await fetch('/files');
            const data = await response.json();

            if (response.ok) {
                filesList.innerHTML = '';
                data.files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <span>${file}</span>
                        <a href="/download/${file}" class="download-btn">Last ned</a>
                    `;
                    filesList.appendChild(fileItem);
                });
                
                // Show/hide download all button based on number of files
                downloadAllBtn.style.display = data.files.length > 0 ? 'block' : 'none';
            }
        } catch (error) {
            console.error('Error loading files:', error);
        }
    }

    // Update selected files list
    function updateSelectedFilesList() {
        selectedFiles.innerHTML = '';
        const files = fileInput.files;

        for (let i = 0; i < files.length; i++) {
            const fileItem = document.createElement('div');
            fileItem.className = 'selected-file-item';
            fileItem.innerHTML = `
                <span>${files[i].name}</span>
                <span class="remove-file" data-index="${i}">×</span>
            `;
            selectedFiles.appendChild(fileItem);
        }

        // Add click handlers for remove buttons
        document.querySelectorAll('.remove-file').forEach(button => {
            button.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                const dt = new DataTransfer();
                const { files } = fileInput;

                for (let i = 0; i < files.length; i++) {
                    if (i !== index) {
                        dt.items.add(files[i]);
                    }
                }

                fileInput.files = dt.files;
                updateSelectedFilesList();
            });
        });
    }

    // Helper function to show status messages
    function showStatus(element, message, type) {
        element.textContent = message;
        element.className = `status-message ${type}`;
    }
}); 