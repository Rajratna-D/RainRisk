/**
 * MahaRainRisk | Leaflet Map Initialization, Markers & Pin Labels
 * Depends on: state.js (state), Leaflet (L)
 */

// ============================================================================
// MAP INITIALIZATION: CARTODB VOYAGER WITH DYNAMIC PLACE NAMES ON ZOOM
// ============================================================================
function initMap() {
  state.mapInstance = L.map("leaflet-map-element", {
    center: [19.7515, 75.7139],
    zoom: 7,
    minZoom: 6,
    maxZoom: 16,
    zoomControl: false
  });

  L.control.zoom({ position: "bottomright" }).addTo(state.mapInstance);

  // OpenStreetMap Tile Layer: High-clarity places, towns, highways, and relief without API key watermarks
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(state.mapInstance);

  state.markerClusterLayer = L.layerGroup().addTo(state.mapInstance);

  // Load official taluka polygons from backend GeoJSON endpoint
  loadTalukaPolygons();

  // Dynamic place names: When zoomed in (zoom >= 9), reveal permanent taluka place labels
  state.mapInstance.on("zoomend", () => {
    updateMapPinLabels();
  });
}

async function loadTalukaPolygons() {
  try {
    const base = window.API_BASE || "";
    const res = await fetch(`${base}/api/map/geojson`);
    if (!res.ok) return;
    const geojsonData = await res.json();
    if (!state.mapInstance) return;

    L.geoJSON(geojsonData, {
      style: (feature) => {
        const color = feature?.properties?.risk_color || "#10B981";
        return {
          fillColor: color,
          weight: 1.2,
          opacity: 0.7,
          color: "#94A3B8",
          fillOpacity: 0.18
        };
      },
      onEachFeature: (feature, layer) => {
        layer.on("click", () => {
          const tName = feature?.properties?.taluka_name;
          if (tName) {
            if (typeof findAndSelectTaluka === "function") {
              findAndSelectTaluka(tName);
            } else if (typeof fetchTalukaData === "function") {
              fetchTalukaData(tName);
            }
          }
        });
      }
    }).addTo(state.mapInstance);
  } catch (err) {
    console.info("Taluka boundary layer optional load note:", err);
  }
}

function updateMapPinLabels() {
  if (!state.mapInstance || !state.markersList.length) return;
  const currentZoom = state.mapInstance.getZoom();
  const isMr = state.currentLanguage === "mr";

  state.markersList.forEach(({ pin, taluka }) => {
    const placeName = isMr ? (taluka.taluka_name_mr || taluka.taluka_name) : taluka.taluka_name;
    const pinColor = taluka.risk_color || "#10B981";
    const riskLabel = isMr ? (taluka.risk_label_mr || "सुरक्षित") : (taluka.risk_label_en || "Safe");
    
    pin.unbindTooltip();
    if (currentZoom >= 9) {
      // Permanent clean badge above marker showing taluka name clearly
      pin.bindTooltip(placeName, {
        permanent: true,
        direction: "top",
        className: "map-taluka-label",
        offset: [0, -8]
      });
    } else {
      // Non-permanent tooltip on hover at state-wide zoom
      const distName = isMr ? (taluka.district_name_mr || taluka.district_name) : taluka.district_name;
      const statusNote = isMr 
        ? `<span style='display:inline-block; width:8px; height:8px; border-radius:50%; background:${pinColor}; margin-right:5px; vertical-align:middle;'></span>${riskLabel} • माहिती पाहण्यासाठी क्लिक करा` 
        : `<span style='display:inline-block; width:8px; height:8px; border-radius:50%; background:${pinColor}; margin-right:5px; vertical-align:middle;'></span>${riskLabel} • Click to view`;
      pin.bindTooltip(`
        <div style="font-family: inherit; padding: 2px 4px;">
          <div style="font-size: 13px; font-weight: 800; color: #0F172A;">${placeName}</div>
          <div style="font-size: 11px; color: #64748B;">${isMr ? 'जिल्हा' : 'District'}: ${distName}</div>
          <div style="margin-top: 4px; font-size: 11px; font-weight: 700; color: ${pinColor};">${statusNote}</div>
        </div>
      `, { sticky: true });
    }
  });
}

function renderTalukaPinsOnMap(talukas) {
  if (!state.mapInstance || !state.markerClusterLayer) return;
  state.markerClusterLayer.clearLayers();
  state.markersList = [];

  talukas.forEach(t => {
    if (!t.latitude || !t.longitude) return;

    const pinColor = t.risk_color || "#10B981";
    const pin = L.circleMarker([t.latitude, t.longitude], {
      radius: 6,
      fillColor: pinColor,
      color: "#FFFFFF",
      weight: 1.8,
      opacity: 0.95,
      fillOpacity: 0.88
    });
    pin.defaultColor = pinColor;

    pin.on("click", () => {
      if (state.activeMarker) {
        state.activeMarker.setStyle({ radius: 6, fillColor: state.activeMarker.defaultColor || "#10B981", weight: 1.8 });
      }
      state.activeMarker = pin;
      pin.setStyle({ radius: 10, fillColor: "#2563EB", weight: 3 });
      state.mapInstance.flyTo([t.latitude, t.longitude], 10, { duration: 1.2 });
      fetchTalukaData(t.taluka_name);
    });

    pin.addTo(state.markerClusterLayer);
    state.markersList.push({ pin, taluka: t });
  });

  updateMapPinLabels();
}
