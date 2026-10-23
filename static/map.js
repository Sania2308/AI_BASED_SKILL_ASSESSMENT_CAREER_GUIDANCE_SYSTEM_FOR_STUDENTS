/**
 * SkillGuide GIS Leaflet Interactive Mapping
 * Safe simulated campus clusters, custom marker styling, and interactive peer popups
 */

let leafletMap = null;
let markerLayerGroup = null;

function initGisSkillMap() {
    const mapCanvas = document.getElementById('gisMapCanvas');
    if (!mapCanvas) return;

    // Initialize Map centered around Bangalore Educational & Tech Hub
    leafletMap = L.map('gisMapCanvas', {
        center: [12.9716, 77.5946],
        zoom: 12,
        zoomControl: true
    });

    // Add OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | SkillGuide GIS'
    }).addTo(leafletMap);

    markerLayerGroup = L.layerGroup().addTo(leafletMap);

    // Initial marker fetch
    loadPeerMarkers();

    // Setup filter event listeners
    const skillSelect = document.getElementById('mapSkillFilter');
    const levelSelect = document.getElementById('mapLevelFilter');
    if (skillSelect) skillSelect.addEventListener('change', loadPeerMarkers);
    if (levelSelect) levelSelect.addEventListener('change', loadPeerMarkers);

    setTimeout(() => {
        leafletMap.invalidateSize();
    }, 250);
}

async function loadPeerMarkers() {
    if (!markerLayerGroup) return;

    const skill = document.getElementById('mapSkillFilter') ? document.getElementById('mapSkillFilter').value : 'all';
    const level = document.getElementById('mapLevelFilter') ? document.getElementById('mapLevelFilter').value : 'all';

    try {
        const res = await fetch(`/api/gis-markers?skill=${encodeURIComponent(skill)}&level=${encodeURIComponent(level)}`);
        const data = await res.json();

        markerLayerGroup.clearLayers();

        const countBadge = document.getElementById('mapPeerCountBadge');
        if (countBadge) countBadge.textContent = `${data.count} Peers Located`;

        if (data.markers && data.markers.length > 0) {
            data.markers.forEach(p => {
                // Custom CSS HTML Marker
                const markerIcon = L.divIcon({
                    className: 'custom-gis-pin',
                    html: `
                        <div style="
                            background: linear-gradient(135deg, #4f46e5, #7c3aed);
                            color: #fff;
                            width: 38px;
                            height: 38px;
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: 700;
                            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
                            border: 2px solid #fff;
                            font-size: 13px;
                            cursor: pointer;
                        ">
                            ${p.name.charAt(0).toUpperCase()}
                        </div>
                    `,
                    iconSize: [38, 38],
                    iconAnchor: [19, 19]
                });

                const verifiedHtml = p.verified_skills.length ?
                    p.verified_skills.map(v => `<span class="badge bg-primary me-1 mb-1">${v.skill} (${v.level} ${v.score}%)</span>`).join('') :
                    '<span class="text-muted small">No verified skills yet</span>';

                const learningHtml = p.learning_skills.length ?
                    p.learning_skills.map(s => `<span class="badge bg-light text-dark border me-1 mb-1">${s}</span>`).join('') :
                    '<span class="text-muted small">None declared</span>';

                const teachSkillNames = p.verified_skills.map(v => v.skill);

                const popupContent = `
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; min-width: 220px; padding: 4px;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <strong style="font-size: 14px; color: #0f172a;">${p.name}</strong>
                            <span class="badge bg-success" style="font-size: 11px;">${p.match}% Match</span>
                        </div>
                        <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
                            ${p.course} &bull; ${p.year} &bull; <i class="bi bi-geo-alt"></i> ${p.zone}
                        </div>
                        <div style="margin-bottom: 6px;">
                            <div style="font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 3px;">Verified to Teach:</div>
                            ${verifiedHtml}
                        </div>
                        <div style="margin-bottom: 10px;">
                            <div style="font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 3px;">Wants to Learn:</div>
                            ${learningHtml}
                        </div>
                        <button onclick="openSwapRequestModal(${p.id}, '${p.name}', ${JSON.stringify(teachSkillNames).replace(/"/g, '&quot;')})" 
                                class="btn btn-sm btn-primary w-100" style="font-size: 12px; font-weight: 600; border-radius: 6px;">
                            <i class="bi bi-arrow-left-right me-1"></i> Request Skill Swap
                        </button>
                    </div>
                `;

                const marker = L.marker([p.lat, p.lng], { icon: markerIcon }).bindPopup(popupContent);
                markerLayerGroup.addLayer(marker);
            });
        }
    } catch (err) {
        console.warn('GIS marker load error:', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('gisMapCanvas')) {
        initGisSkillMap();
    }
});
