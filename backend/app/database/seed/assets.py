from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.models.asset import Asset

def seed_assets(db: Session, rooms):
    assets = []
    now = datetime.utcnow()

    # Specific key asset: Wi-Fi Access Point in Computer Lab A
    comp_lab_a = next((r for r in rooms if "Computer Lab A" in r.name), rooms[0])
    wifi_ap_lab_a = Asset(
        asset_tag="AST-ENG-WIFI-01",
        name="Wi-Fi Access Point - Cisco Catalyst 9130",
        category="network",
        building_id=comp_lab_a.building_id,
        room_id=comp_lab_a.id,
        status="operational",
        serial_number="SN-WIFI-ENG-9130-A",
        last_inspected_at=now - timedelta(days=5)
    )
    db.add(wifi_ap_lab_a)
    assets.append(wifi_ap_lab_a)

    categories = ["network", "av_equipment", "hvac", "electrical", "lab_equipment", "furniture"]
    cat_names = {
        "network": ["Wi-Fi Access Point", "Managed PoE Switch 24-Port", "Edge Router", "Network Patch Panel"],
        "av_equipment": ["4K Laser Projector", "Ceiling Acoustic Array", "Interactive Smart Podium", "Wireless Mic Receiver"],
        "hvac": ["Daikin Central Inverter AC", "Cassette Air Conditioning Unit", "Smart Thermostat Zone Controller", "HEPA Ventilation Air Filter"],
        "electrical": ["Modular UPS 3000VA", "Power Distribution Rack", "Emergency Lighting Inverter", "Main Room Breaker Unit"],
        "lab_equipment": ["Dell Precision Workstation", "Digital Storage Oscilloscope", "Dual-Channel Power Supply", "3D Rapid Prototyper"],
        "furniture": ["Ergonomic Faculty Desk", "Heavy-Duty Workstation Bench", "Motorized Projector Screen", "Safety Goggle Cabinet"]
    }

    # Generate total of 150 assets
    for i in range(1, 150):
        room = rooms[i % len(rooms)]
        category = categories[i % len(categories)]
        name_choice = cat_names[category][i % len(cat_names[category])]
        status = "operational"
        if i % 23 == 0:
            status = "degraded"
        elif i % 37 == 0:
            status = "maintenance"

        asset = Asset(
            asset_tag=f"AST-{room.room_number}-{i+1:03d}",
            name=f"{name_choice} #{i+1}",
            category=category,
            building_id=room.building_id,
            room_id=room.id,
            status=status,
            serial_number=f"SN-{category.upper()[:3]}-{i+1000}",
            last_inspected_at=now - timedelta(days=(i * 3) % 45)
        )
        db.add(asset)
        assets.append(asset)

    db.flush()
    return assets

