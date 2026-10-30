from sqlalchemy.orm import Session
from app.database.models.inventory import InventoryItem

INVENTORY_ITEMS_DEF = [
    # Network items
    {"code": "INV-NET-001", "name": "Enterprise Wi-Fi 6 AP Module", "category": "network", "stock": 2, "reserved": 2, "cost": 450.0, "threshold": 5},
    {"code": "INV-NET-002", "name": "Cat6A High-Speed Patch Cable 3m", "category": "network", "stock": 120, "reserved": 5, "cost": 12.5, "threshold": 25},
    {"code": "INV-NET-003", "name": "PoE+ Gigabit 24-Port Switch", "category": "network", "stock": 4, "reserved": 1, "cost": 680.0, "threshold": 3},
    {"code": "INV-NET-004", "name": "Fiber Optic Patch Lead LC-LC 10m", "category": "network", "stock": 35, "reserved": 0, "cost": 28.0, "threshold": 10},
    {"code": "INV-NET-005", "name": "SFP+ 10G Transceiver Module", "category": "network", "stock": 18, "reserved": 2, "cost": 95.0, "threshold": 6},
    {"code": "INV-NET-006", "name": "RJ45 Modular Plugs (Pack of 100)", "category": "network", "stock": 25, "reserved": 0, "cost": 22.0, "threshold": 8},
    {"code": "INV-NET-007", "name": "Cisco Access Point Radio Replacement Card", "category": "network", "stock": 0, "reserved": 0, "cost": 310.0, "threshold": 4},

    # AV & Presentation
    {"code": "INV-AV-001", "name": "High-Output Laser Projector Bulb", "category": "hardware", "stock": 3, "reserved": 1, "cost": 185.0, "threshold": 5},
    {"code": "INV-AV-002", "name": "HDMI 2.1 4K 10-Metre Cable", "category": "hardware", "stock": 45, "reserved": 3, "cost": 32.0, "threshold": 15},
    {"code": "INV-AV-003", "name": "Wireless Lapel Microphone Kit", "category": "hardware", "stock": 12, "reserved": 0, "cost": 140.0, "threshold": 4},
    {"code": "INV-AV-004", "name": "USB-C Multi-Port Presentation Hub", "category": "hardware", "stock": 28, "reserved": 2, "cost": 65.0, "threshold": 10},
    {"code": "INV-AV-005", "name": "Ceiling Mount Bracket for Projector", "category": "hardware", "stock": 8, "reserved": 0, "cost": 75.0, "threshold": 3},
    {"code": "INV-AV-006", "name": "Smartboard Stylus Pen Dual-Tip", "category": "hardware", "stock": 40, "reserved": 0, "cost": 18.0, "threshold": 10},

    # Electrical & Power
    {"code": "INV-ELE-001", "name": "Industrial Miniature Circuit Breaker 32A", "category": "electrical", "stock": 16, "reserved": 2, "cost": 35.0, "threshold": 6},
    {"code": "INV-ELE-002", "name": "Surface Mount Dual Power Socket 13A", "category": "electrical", "stock": 65, "reserved": 4, "cost": 14.5, "threshold": 20},
    {"code": "INV-ELE-003", "name": "UPS Sealed Lead-Acid Battery 12V 9Ah", "category": "electrical", "stock": 14, "reserved": 0, "cost": 48.0, "threshold": 6},
    {"code": "INV-ELE-004", "name": "LED High-Efficiency Batten Light 40W", "category": "electrical", "stock": 50, "reserved": 5, "cost": 26.0, "threshold": 15},
    {"code": "INV-ELE-005", "name": "Surge Protected 8-Way PDU Strip", "category": "electrical", "stock": 22, "reserved": 1, "cost": 55.0, "threshold": 8},
    {"code": "INV-ELE-006", "name": "Emergency Exit Luminaire Battery Kit", "category": "electrical", "stock": 10, "reserved": 0, "cost": 62.0, "threshold": 4},

    # HVAC & Climate
    {"code": "INV-HVC-001", "name": "Antimicrobial AC Filter Cartridge", "category": "general", "stock": 30, "reserved": 4, "cost": 38.0, "threshold": 12},
    {"code": "INV-HVC-002", "name": "Digital Smart Room Thermostat Unit", "category": "hardware", "stock": 7, "reserved": 0, "cost": 125.0, "threshold": 4},
    {"code": "INV-HVC-003", "name": "HVAC Fan Blower Capacitor 50uF", "category": "electrical", "stock": 15, "reserved": 1, "cost": 19.5, "threshold": 5},
    {"code": "INV-HVC-004", "name": "Condensate Drain Mini Removal Pump", "category": "plumbing", "stock": 6, "reserved": 0, "cost": 92.0, "threshold": 3},
    {"code": "INV-HVC-005", "name": "R410A Refrigerant Recharge Canister 5kg", "category": "general", "stock": 8, "reserved": 1, "cost": 160.0, "threshold": 3},

    # Plumbing & Sanitation
    {"code": "INV-PLM-001", "name": "Automatic Touchless Tap Sensor Valve", "category": "plumbing", "stock": 9, "reserved": 0, "cost": 115.0, "threshold": 4},
    {"code": "INV-PLM-002", "name": "Flexible Stainless Steel Water Hose 1/2in", "category": "plumbing", "stock": 42, "reserved": 2, "cost": 11.0, "threshold": 15},
    {"code": "INV-PLM-003", "name": "Ceramic Disc Cartridge 35mm", "category": "plumbing", "stock": 30, "reserved": 0, "cost": 16.0, "threshold": 8},
    {"code": "INV-PLM-004", "name": "Commercial Toilet Flush Valve Flushometer", "category": "plumbing", "stock": 5, "reserved": 1, "cost": 145.0, "threshold": 3},
    {"code": "INV-PLM-005", "name": "Automatic Hand Soap Dispenser Mechanism", "category": "general", "stock": 24, "reserved": 3, "cost": 42.0, "threshold": 8},

    # Hardware & IT Peripherals
    {"code": "INV-IT-001", "name": "DDR5 16GB 4800MHz ECC Desktop RAM", "category": "hardware", "stock": 20, "reserved": 0, "cost": 72.0, "threshold": 6},
    {"code": "INV-IT-002", "name": "NVMe PCIe 4.0 SSD 1TB Workstation Grade", "category": "hardware", "stock": 15, "reserved": 0, "cost": 89.0, "threshold": 5},
    {"code": "INV-IT-003", "name": "Wired Ergonomic Optical Mouse & Keyboard Combo", "category": "hardware", "stock": 60, "reserved": 8, "cost": 34.0, "threshold": 20},
    {"code": "INV-IT-004", "name": "27-inch IPS QHD Lab Monitor", "category": "hardware", "stock": 8, "reserved": 2, "cost": 220.0, "threshold": 4},
    {"code": "INV-IT-005", "name": "DisplayPort to HDMI Active Adapter", "category": "hardware", "stock": 35, "reserved": 1, "cost": 15.0, "threshold": 10},
    {"code": "INV-IT-006", "name": "Anti-Static Lab Grounding Wristbands (10pk)", "category": "general", "stock": 18, "reserved": 0, "cost": 25.0, "threshold": 5},
]

def seed_inventory(db: Session):
    items = []
    for d in INVENTORY_ITEMS_DEF:
        item = InventoryItem(
            item_code=d["code"],
            name=d["name"],
            category=d["category"],
            stock_quantity=d["stock"],
            reserved_quantity=d["reserved"],
            unit_cost=d["cost"],
            minimum_threshold=d["threshold"]
        )
        db.add(item)
        items.append(item)

    db.flush()
    return items

