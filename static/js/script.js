document.addEventListener('DOMContentLoaded', function () {
    // Color picker functionality
    const colorOptions = document.querySelectorAll('.color-option');
    colorOptions.forEach(option => {
        option.addEventListener('click', function () {
            colorOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            const color = this.getAttribute('data-color').split(',');
            fetch('/set_color', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    r: parseInt(color[0]),
                    g: parseInt(color[1]),
                    b: parseInt(color[2])
                })
            });
        });
    });

    // Brush size slider
    const brushSlider = document.getElementById('brush-slider');
    const brushValue = document.getElementById('brush-value');

    brushSlider.addEventListener('input', function () {
        brushValue.textContent = this.value;
        fetch('/set_brush_size', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                size: parseInt(this.value)
            })
        });
    });

    // Clear canvas button
    document.getElementById('clear-btn').addEventListener('click', function () {
        fetch('/clear_canvas', {
            method: 'POST'
        });
    });

    // Save drawing button
    document.getElementById('save-drawing').addEventListener('click', function () {
        fetch('/save_drawing', {
            method: 'POST'
        }).then(response => {
            if (response.ok) {
                alert('Drawing saved successfully!');
                window.location.href = '/drawings';
            }
        });
    });
});