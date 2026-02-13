document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('file-name');
    const dropZone = document.getElementById('drop-zone');

    fileInput.addEventListener('change', function(e) {
        if (this.files && this.files.length > 0) {
            fileNameDisplay.textContent = 'Выбран: ' + this.files[0].name;
            dropZone.style.borderColor = '#ff6b6b';
            dropZone.style.backgroundColor = '#fff0f0';
        }
    });
});
