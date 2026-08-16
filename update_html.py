import os

html_path = 'barber/templates/barber/booking_app.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add step 5 to indicator
content = content.replace(
    '<div class="step-node" data-step="4">4</div>',
    '<div class="step-node" data-step="4">4</div>\n        <div class="step-node" data-step="5">5</div>'
)

# 2. Add Zone View and shift others
zone_view = """
    <!-- VIEW 1: Zone Selection -->
    <section class="view-section active" id="view-1">
        <h2 class="section-title">🪑 Zonani tanlang</h2>
        <div id="zones-loading" class="spinner"></div>
        <div class="service-list" id="zones-container"></div>
    </section>
"""
content = content.replace('<!-- VIEW 1: Service Selection -->', zone_view + '\n    <!-- VIEW 2: Service Selection -->')
content = content.replace('id="view-1"', 'id="view-2"', 1) # First occurrence of view-1 in services
# We must be careful because we just inserted view-1
# Let's do it smarter:

content = content.replace('id="view-4"', 'id="view-5"')
content = content.replace('id="view-3"', 'id="view-4"')
content = content.replace('id="view-2"', 'id="view-3"')
content = content.replace('<section class="view-section active" id="view-1">', '<section class="view-section" id="view-2">')

# Re-insert view-1
content = content.replace(
    '<!-- VIEW 2: Service Selection -->',
    '<!-- VIEW 1: Zone Selection -->\n    <section class="view-section active" id="view-1">\n        <h2 class="section-title">🪑 Zonani tanlang</h2>\n        <div id="zones-loading" class="spinner"></div>\n        <div class="service-list" id="zones-container"></div>\n    </section>\n\n    <!-- VIEW 2: Service Selection -->'
)

# 3. Add Zone to Summary
summary_zone = """
            <div class="summary-row">
                <span class="summary-label">Zona</span>
                <span class="summary-value" id="sum-zone">-</span>
            </div>"""
content = content.replace('<div class="summary-row">\n                <span class="summary-label">Xizmat</span>', summary_zone + '\n            <div class="summary-row">\n                <span class="summary-label">Xizmat</span>')

# 4. JS state and loop
content = content.replace('let selectedService = null;', 'let selectedZone = null;\n        let selectedService = null;')
content = content.replace('for(let i=1; i<=4; i++) {', 'for(let i=1; i<=5; i++) {')
content = content.replace("const progressWidths = { 1: '0%', 2: '33%', 3: '66%', 4: '100%' };", "const progressWidths = { 1: '0%', 2: '25%', 3: '50%', 4: '75%', 5: '100%' };")

# 5. JS validateStep
content = content.replace('let isValid = false;', 'let isValid = false;\n            if (currentStep === 1 && selectedZone !== null) isValid = true;')
content = content.replace('if (currentStep === 1 && selectedService !== null) isValid = true;', 'if (currentStep === 2 && selectedService !== null) isValid = true;')
content = content.replace('if (currentStep === 2 && selectedBarber !== null) isValid = true;', 'if (currentStep === 3 && selectedBarber !== null) isValid = true;')
content = content.replace('if (currentStep === 3 && selectedDate !== null && selectedTime !== null) isValid = true;', 'if (currentStep === 4 && selectedDate !== null && selectedTime !== null) isValid = true;')
content = content.replace('if (currentStep === 4) isValid = true;', 'if (currentStep === 5) isValid = true;')

# 6. JS btn actions
content = content.replace('if (currentStep < 4) {', 'if (currentStep < 5) {')
content = content.replace('if (step === 4) {', 'if (step === 5) {')
content = content.replace("document.getElementById('view-4').classList.remove('active');", "document.getElementById('view-5').classList.remove('active');")

# 7. JS loadZones
load_zones_js = """
        // Step 1: Load Zones
        async function loadZones() {
            try {
                const response = await fetch('/api/zones/');
                const data = await response.json();
                
                document.getElementById('zones-loading').style.display = 'none';
                const container = document.getElementById('zones-container');
                container.innerHTML = '';

                data.zones.forEach(zone => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.dataset.id = zone.id;
                    card.innerHTML = `
                        <div class="card-left">
                            <div class="card-icon">${zone.icon}</div>
                            <div class="card-info">
                                <span class="card-name">${zone.name}</span>
                                <span class="card-desc">${zone.description}</span>
                            </div>
                        </div>
                        <div class="card-right">
                            <span class="card-price">${zone.price > 0 ? zone.price.toLocaleString() + ' UZS' : 'Bepul'}</span>
                        </div>
                    `;
                    card.addEventListener('click', () => {
                        selectedZone = zone;
                        document.querySelectorAll('#zones-container .card').forEach(c => c.classList.remove('selected'));
                        card.classList.add('selected');
                        validateStep();
                    });
                    container.appendChild(card);
                });
            } catch (err) {
                console.error("Zones fetch error:", err);
            }
        }
"""
content = content.replace('// Step 1: Load Services', load_zones_js + '\n        // Step 2: Load Services')

# 8. JS prepareSummary & Payload
content = content.replace("document.getElementById('sum-service').innerText", "document.getElementById('sum-zone').innerText = `${selectedZone.icon} ${selectedZone.name}`;\n            document.getElementById('sum-service').innerText")
content = content.replace("`${selectedService.price.toLocaleString()} UZS`;", "`${(selectedService.price + selectedZone.price).toLocaleString()} UZS`;")
content = content.replace("service_id: selectedService.id,", "zone_id: selectedZone.id,\n                service_id: selectedService.id,")

# 9. Initialize
content = content.replace('loadServices();', 'loadZones();\n        loadServices();')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated HTML successfully.")
