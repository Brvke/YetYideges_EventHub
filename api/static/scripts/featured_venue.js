$(document).ready(function() {
    // Perform AJAX request to fetch featured venues
    $.ajax({
        url: '/api/featured-venues',  // Replace with your actual API endpoint
        method: 'GET',
        success: function(response) {
            // Handle successful response and populate venues
            const venues = response.venues;
            const venuesContainer = $('#featured-venues-container');
            venues.forEach(function(venue) {
                const venueHtml = `
                    <div class="venue">
                        <img src="${venue.imageUrl}" alt="${venue.name}">
                        <h3>${venue.name}</h3>
                        <p>${venue.description}</p>
                        <p>${venue.priceRange}</p>
                    </div>
                `;
                venuesContainer.append(venueHtml);
            });
        },
        error: function(err) {
            console.error('Error fetching featured venues:', err);
        }
    });
});