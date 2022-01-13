function initMap() {
    navigator.geolocation.getCurrentPosition(position => {
        const { latitude, longitude } = position.coords;
        // Handle navigator.geolocation error: https://developers.google.com/maps/documentation/javascript/geolocation
        
        infowindow = new google.maps.InfoWindow();

        // Show a map centered at latitude / longitude.
        let map = new google.maps.Map(document.getElementById('map'), {
            center: {lat:latitude, lng: longitude},
            zoom: 11
          });

        const retailer_name = document.getElementById("retailer_name").textContent
        
        let request = {
        query: `${retailer_name}`,
        fields: ['name', 'geometry', 'formatted_address', 'place_id'],
        locationBias: {radius: 100, center: {lat: latitude, lng: longitude}}
        };

        let service = new google.maps.places.PlacesService(map);

        
        service.findPlaceFromQuery(request, function(results, status) {
          if (status === google.maps.places.PlacesServiceStatus.OK) {
            for (let i = 0; i < results.length; i++) {
                const infowindow = new google.maps.InfoWindow();
                const marker = new google.maps.Marker({
                    position: results[i].geometry.location,
                    map: map,
                  });
                  function display_infowindow() {
                    const content = document.createElement("div");
                    
                    const nameElement = document.createElement("h2");
                    nameElement.textContent = results[i].name;
                    content.appendChild(nameElement);
            
                    const placeAddressElement = document.createElement("p");
                    placeAddressElement.textContent = results[i].formatted_address;
                    content.appendChild(placeAddressElement);

                    const placeGmapsLink = document.createElement("a");
                    placeGmapsLink.textContent = "Directions From Current Location";
                    url = `https://www.google.com/maps/dir/?api=1&origin=${latitude},${longitude}&destination=${results[i].geometry.location}&destination_place_id=${results[i].place_id}&travelmode=driving`;
                    placeGmapsLink.href = url;
                    content.appendChild(placeGmapsLink);
                    
                    infowindow.setContent(content);
                    infowindow.open(map, marker);
                  }
                  if (i == 0) {
                    display_infowindow()
                  }
                  google.maps.event.addListener(marker, "click", () => {
                    display_infowindow()
                 });
              }
            map.setCenter(results[0].geometry.location);
          }
        });
    });
}

  