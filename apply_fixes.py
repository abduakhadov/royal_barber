import os

html_path = 'booking_app.html.backup'
dest_path = 'barber/templates/barber/booking_app.html'

if not os.path.exists(html_path):
    print("Xatolik: booking_app.html.backup fayli topilmadi!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add step 5 to indicator
if 'data-step="5"' not in content:
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
if 'Zonani tanlang' not in content:
    content = content.replace('<!-- VIEW 1: Service Selection -->', zone_view + '\n    <!-- VIEW 2: Service Selection -->')
    content = content.replace('id="view-1"', 'id="view-2"', 1) 
    
    content = content.replace('id="view-4"', 'id="view-5"')
    content = content.replace('id="view-3"', 'id="view-4"')
    content = content.replace('id="view-2"', 'id="view-3"')
    content = content.replace('<section class="view-section active" id="view-1">', '<section class="view-section" id="view-2">')
    
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
if 'id="sum-zone"' not in content:
    content = content.replace('<div class="summary-row">\n                <span class="summary-label">Xizmat</span>', summary_zone + '\n            <div class="summary-row">\n                <span class="summary-label">Xizmat</span>')

# 4. JS state and loop
if 'selectedZone = null' not in content:
    content = content.replace('let selectedService = null;', 'let selectedZone = null;\n        let selectedService = null;')
    content = content.replace('for(let i=1; i<=4; i++) {', 'for(let i=1; i<=5; i++) {')
    content = content.replace("const progressWidths = { 1: '0%', 2: '33%', 3: '66%', 4: '100%' };", "const progressWidths = { 1: '0%', 2: '25%', 3: '50%', 4: '75%', 5: '100%' };")

# 5. JS validateStep
if 'selectedZone !== null' not in content:
    content = content.replace('let isValid = false;', 'let isValid = false;\n            if (currentStep === 1 && selectedZone !== null) isValid = true;')
    content = content.replace('if (currentStep === 1 && selectedService !== null) isValid = true;', 'if (currentStep === 2 && selectedService !== null) isValid = true;')
    content = content.replace('if (currentStep === 2 && selectedBarber !== null) isValid = true;', 'if (currentStep === 3 && selectedBarber !== null) isValid = true;')
    content = content.replace('if (currentStep === 3 && selectedDate !== null && selectedTime !== null) isValid = true;', 'if (currentStep === 4 && selectedDate !== null && selectedTime !== null) isValid = true;')
    content = content.replace('if (currentStep === 4) isValid = true;', 'if (currentStep === 5) isValid = true;')

# 6. JS btn actions
if 'currentStep < 5' not in content:
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
if 'loadZones()' not in content:
    content = content.replace('// Step 1: Load Services', load_zones_js + '\n        // Step 2: Load Services')

# 8. JS prepareSummary & Payload
if 'zone_id: selectedZone.id' not in content:
    content = content.replace("document.getElementById('sum-service').innerText", "document.getElementById('sum-zone').innerText = `${selectedZone.icon} ${selectedZone.name}`;\n            document.getElementById('sum-service').innerText")
    content = content.replace("`${selectedService.price.toLocaleString()} UZS`;", "`${(selectedService.price + selectedZone.price).toLocaleString()} UZS`;")
    content = content.replace("service_id: selectedService.id,", "zone_id: selectedZone.id,\n                service_id: selectedService.id,")

# 9. Initialize
if 'loadZones();' not in content:
    content = content.replace('loadServices();', 'loadZones();\n        loadServices();')

# 10. External Website Button and CSS
ext_css = """
        /* External Website Button (Gold & Black/White) */
        .site-link-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            padding: 8px 18px;
            border-radius: 20px;
            background: #000000;
            color: #ffffff;
            border: 1.5px solid var(--gold);
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            transition: var(--transition);
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
            letter-spacing: 0.5px;
        }
        .site-link-btn:hover {
            background: var(--gold-gradient);
            color: #121212;
            border-color: transparent;
            box-shadow: 0 4px 20px rgba(212, 175, 55, 0.4);
            transform: translateY(-1px);
        }
        .site-link-btn:active {
            transform: translateY(1px);
        }
"""
if 'site-link-btn' not in content:
    content = content.replace('</style>', ext_css + '\n    </style>')
    content = content.replace('<p class="subtitle" id="user-greeting">Xush kelibsiz!</p>', '<p class="subtitle" id="user-greeting">Xush kelibsiz!</p>\n        {% if external_website_url %}\n        <a href="{{ external_website_url }}" target="_blank" class="site-link-btn">🌐 Saytga o\'tish</a>\n        {% endif %}')

with open(dest_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("To'g'rilangan HTML muvaffaqiyatli saqlandi!")
