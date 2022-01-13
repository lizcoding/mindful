function initMap() {
    navigator.geolocation.getCurrentPosition(position => {
        const { latitude, longitude } = position.coords;
        // Handle navigator.geolocation error: https://developers.google.com/maps/documentation/javascript/geolocation
        
        infowindow = new google.maps.InfoWindow();

        // Show a map centered at latitude / longitude.
        let map = new google.maps.Map(document.getElementById('map'), {
            center: {lat:latitude, lng: longitude},
            zoom: 10
          });

        let request = {
        query: 'Lululemon',
        fields: ['name', 'geometry', 'formatted_address', 'opening_hours'],
        locationBias: {radius: 100, center: {lat: latitude, lng: longitude}}
        };

        let service = new google.maps.places.PlacesService(map);

        service.findPlaceFromQuery(request, function(results, status) {
          if (status === google.maps.places.PlacesServiceStatus.OK) {
            for (let i = 0; i < results.length; i++) {
                const marker = new google.maps.Marker({
                    position: results[i].geometry.location,
                    map: map,
                  });
            }
            map.setCenter(results[0].geometry.location);
          }
        });
    });
}

  