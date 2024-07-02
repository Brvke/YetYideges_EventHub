// Select the button element
const button = document.querySelector('About us');

// Add a click event listener to the button
button.addEventListener('click', generateAbout);

// Function to generate the about.html
function generateAbout() {
    // Create a new XMLHttpRequest object
    const xhr = new XMLHttpRequest();

    // Set the request URL
    const url = '..static/temp/about.html';

    // Send a GET request to the server
    xhr.open('GET', url, true);
    xhr.send();

    // Handle the response
    xhr.onload = function() {
        if (xhr.status === 200) {
            // Get the response text
            const responseText = xhr.responseText;

            // Create a new window or tab with the about.html content
            const aboutWindow = window.open();
            aboutWindow.document.open();
            aboutWindow.document.write(responseText);
            aboutWindow.document.close();
        }
    };
}