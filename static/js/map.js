/**
 * GeoPlazma Map Manager
 * Handles map display and geospatial data visualization using Leaflet
 */

const GeoPlazmaMap = (function() {
    'use strict';

    let map = null;
    let markers = {};
    let polylines = {};
    let currentAreaId = null;

    // Initialize the map
    function init() {
        // Create map centered on Europe by default
        map = L.map('map').setView([46.0, 13.0], 6);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
            crossOrigin: true
        }).addTo(map);

        // Add some default controls
        L.control.zoom().addTo(map);
        L.control.scale().addTo(map);
    }

    // Clear all map layers
    function clearMap() {
        // Remove markers
        Object.values(markers).forEach(marker => marker.remove());
        markers = {};

        // Remove polylines
        Object.values(polylines).forEach(line => line.remove());
        polylines = {};
    }

    // Add a single point to the map
    function addPoint(point, areaId) {
        const markerId = areaId + '_' + point.timestamp;

        const marker = L.circleMarker(
            [point.lat, point.lon],
            {
                radius: 6,
                fillColor: '#3498db',
                color: '#2980b9',
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.7
            }
        ).bindPopup(`
            <div class="map-popup">
                <strong>Coordinates</strong><br>
                Latitude: ${point.lat.toFixed(6)}<br>
                Longitude: ${point.lon.toFixed(6)}<br>
                Time: ${new Date(point.timestamp * 1000).toLocaleString()}
            </div>
        `).addTo(map);

        markers[markerId] = marker;
        return marker;
    }

    // Display area on map
    function displayArea(area, areaId) {
        if (!area.points || area.points.length === 0) {
            UI.showNotification('No points in this area', 'info');
            return;
        }

        clearMap();
        currentAreaId = areaId;

        // Add all points
        const points = area.points;
        points.forEach(point => addPoint(point, areaId));

        // Draw polyline connecting points if more than 1 point
        if (points.length > 1) {
            const coords = points.map(p => [p.lat, p.lon]);
            const polyline = L.polyline(coords, {
                color: '#3498db',
                weight: 2,
                opacity: 0.6,
                dashArray: '5, 5'
            }).addTo(map);

            polylines[areaId] = polyline;
        }

        // Fit map to bounds
        if (markers && Object.keys(markers).length > 0) {
            const group = new L.featureGroup(Object.values(markers));
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    // Get map statistics for display
    function getAreaStats(area) {
        if (!area.points || area.points.length === 0) {
            return {
                pointCount: 0,
                latRange: 'N/A',
                lonRange: 'N/A'
            };
        }

        const lats = area.points.map(p => p.lat);
        const lons = area.points.map(p => p.lon);

        return {
            pointCount: area.points.length,
            latRange: `${Math.min(...lats).toFixed(4)}° - ${Math.max(...lats).toFixed(4)}°`,
            lonRange: `${Math.min(...lons).toFixed(4)}° - ${Math.max(...lons).toFixed(4)}°`
        };
    }

    // Export area data as GeoJSON
    function exportAsGeoJSON(area) {
        const features = area.points.map((point, index) => ({
            type: 'Feature',
            properties: {
                timestamp: point.timestamp,
                name: `Point ${index + 1}`,
                index: index
            },
            geometry: {
                type: 'Point',
                coordinates: [point.lon, point.lat]
            }
        }));

        return {
            type: 'FeatureCollection',
            name: area.name,
            features: features
        };
    }

    // Export area data as KML
    function exportAsKML(area) {
        let kml = '<?xml version="1.0" encoding="UTF-8"?>\n';
        kml += '<kml xmlns="http://www.opengis.net/kml/2.2">\n';
        kml += '  <Document>\n';
        kml += `    <name>${area.name}</name>\n`;
        kml += '    <Placemark>\n';

        kml += '      <LineString>\n';
        kml += '        <coordinates>\n';

        area.points.forEach(point => {
            kml += `          ${point.lon},${point.lat},0\n`;
        });

        kml += '        </coordinates>\n';
        kml += '      </LineString>\n';
        kml += '    </Placemark>\n';

        area.points.forEach((point, index) => {
            kml += '    <Placemark>\n';
            kml += `      <name>Point ${index + 1}</name>\n`;
            kml += `      <description>Lat: ${point.lat}, Lon: ${point.lon}</description>\n`;
            kml += '      <Point>\n';
            kml += `        <coordinates>${point.lon},${point.lat},0</coordinates>\n`;
            kml += '      </Point>\n';
            kml += '    </Placemark>\n';
        });

        kml += '  </Document>\n';
        kml += '</kml>';

        return kml;
    }

    // Public API
    return {
        init: init,
        clearMap: clearMap,
        addPoint: addPoint,
        displayArea: displayArea,
        getAreaStats: getAreaStats,
        exportAsGeoJSON: exportAsGeoJSON,
        exportAsKML: exportAsKML
    };
})();

// Export for use in other modules
window.GeoPlazmaMap = GeoPlazmaMap;
