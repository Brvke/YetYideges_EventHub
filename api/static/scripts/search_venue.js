$(document).ready(init);

const HOST = '0.0.0.0';
const searchParams = {
  location: {},
  date: {},
  eventType: {}
};

function init() {
  // Location checkboxes
  $('.locations .popover input').change(function() {
    updateSearchParams('location', $(this));
  });

  // Date checkboxes
  $('.dates .popover input').change(function() {
    updateSearchParams('date', $(this));
  });

  // Event Type checkboxes
  $('.event-types .popover input').change(function() {
    updateSearchParams('eventType', $(this));
  });

  updateLocationDisplay();
  updateDateDisplay();
  updateEventTypeDisplay();

  apiStatus();
  searchVenues();
}

function updateSearchParams(type, checkbox) {
  if (checkbox.is(':checked')) {
    searchParams[type][checkbox.attr('data-name')] = checkbox.attr('data-id');
  } else if (checkbox.is(':not(:checked)')) {
    delete searchParams[type][checkbox.attr('data-name')];
  }
}

function updateLocationDisplay() {
  const locationNames = Object.keys(searchParams.location);
  $('.locations h4').text(locationNames.sort().join(', '));
}

function updateDateDisplay() {
  const dateNames = Object.keys(searchParams.date);
  $('.dates h4').text(dateNames.sort().join(', '));
}

function updateEventTypeDisplay() {
  const eventTypeNames = Object.keys(searchParams.eventType);
  $('.event-types h4').text(eventTypeNames.sort().join(', '));
}

function apiStatus() {
  const API_URL = `http://${HOST}:5001/api/status/`;
  $.get(API_URL, (data, textStatus) => {
    if (textStatus === 'success' && data.status === 'OK') {
      $('#api_status').addClass('available');
    } else {
      $('#api_status').removeClass('available');
    }
  });
}

function searchVenues() {
  const VENUES_URL = `http://${HOST}:5001/api/venues_search/`;
  $.ajax({
    url: VENUES_URL,
    type: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data: JSON.stringify({
      location: Object.values(searchParams.location),
      date: Object.values(searchParams.date),
      eventType: Object.values(searchParams.eventType)
    }),
    success: function(response) {
      $('SECTION.venues').empty();
      for (const v of response) {
        const article = ['<article>',
          `<h2>${v.name}</h2>`,
          `<div class="address">${v.address}</div>`,
          `<div class="capacity">${v.capacity} capacity</div>`,
          `<div class="event-types">${v.event_types.join(', ')}</div>`,
          '</article>'];
        $('SECTION.venues').append(article.join(''));
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
}