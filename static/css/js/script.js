// Function to upload the file
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        console.error('File upload failed');
        return;
    }

    const data = await response.json();
    return data.file_path;
}

// Function to analyze the uploaded file
async function analyzeFile(filePath) {
    const response = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath }),  // Send file path for analysis
    });

    if (!response.ok) {
        console.error('Image analysis failed');
        return;
    }

    const analysisData = await response.json();
    return analysisData.parsed_result;  // Return the analysis result
}

// Function to handle the form submission
document.getElementById('upload-form').addEventListener('submit', async function (event) {
    event.preventDefault();

    const fileInput = document.getElementById('image-file');
    const file = fileInput.files[0];

    if (!file) {
        showError("Please select an image to upload.");
        return;
    }

    // Show loading message
    document.getElementById('loading-message').style.display = 'block';

    try {
        // Upload the file
        const filePath = await uploadFile(file);

        // If file upload is successful, analyze the file
        const analysisResult = await analyzeFile(filePath);

        // Redirect to result page with the parsed result
        window.location.href = '/result?result=' + encodeURIComponent(JSON.stringify(analysisResult));

    } catch (error) {
        console.error(error);
        showError(error.message);
    } finally {
        // Hide loading message
        document.getElementById('loading-message').style.display = 'none';
    }
});

// Function to show error message
function showError(message) {
    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.textContent = message;
    errorMessageDiv.style.display = 'block';
}
