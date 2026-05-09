def detect_service(text):
    """
    Detects the service type based on user input text.
    Returns the service name if found, otherwise 'unknown'.
    """

    text = text.lower()

    services = {
        "Electrician": [
            "electrician", "fan", "switch", "light", "bulb", "tube light", "wire", "wiring",
            "socket", "plug", "short circuit", "mcb", "fuse", "inverter",
            "ac", "air conditioner", "power", "electric", "voltage"
        ],

        "Plumber": [
            "plumber", "water", "leak", "pipe", "tap", "faucet", "bathroom", "toilet",
            "flush", "drain", "sewage", "tank", "geyser", "motor",
            "blocked", "overflow"
        ],

        "Carpenter": [
            "carpenter", "door", "window", "wood", "furniture", "cupboard", "wardrobe",
            "bed", "table", "chair", "sofa", "shelf", "drawer",
            "plywood", "modular"
        ],

        "Painter": [
            "painter", "paint", "painting", "wall", "ceiling", "color", "whitewash",
            "putty", "primer", "texture", "polish"
        ],
        "Tiles Worker": [
            "tiles", "floor tiles", "wall tiles", "marble", "granite", "flooring", "tile repair"
        ],
        "Demolition Worker": [
            "break wall", "break floor", "demolition", "debris removal", "concrete breaking"
        ],
        "Waterproofing Worker": [
            "leakage", "dampness", "roof leakage", "balcony leakage", "seepage", "waterproofing", "dr fixit"
        ],
        "Welder": [
            "weld", "welding", "metal", "iron gate", "grill", "steel work", "soldering"
        ],
        "Event Decorator": [
            "decoration", "party", "wedding", "balloon", "flowers", "birthday", "event decor"
        ],
        "Stage Setup Worker": [
            "stage", "ramp", "podium", "backdrop", "truss", "stage builder"
        ],
        "Lighting Technician": [
            "stage light", "focus light", "led wall", "generator", "event lighting"
        ],
        "Bouncer": [
            "security", "guard", "event security", "bouncer", "bodyguard"
        ],
        "Driver on Hire": [
            "driver", "chauffeur", "car driver", "valet", "outstation driver"
        ],
        "Car Wash": [
            "car cleaning", "car wash", "foam wash", "car polish", "interior cleaning"
        ],
        "Bike Wash": [
            "bike wash", "two wheeler cleaning", "chain cleaning", "bike polish"
        ],
        "Cook": [
            "cook", "chef", "food", "meal", "home cook", "party cook", "breakfast", "dinner"
        ],
        "Household Helper": [
            "maid", "helper", "cleaning", "dusting", "vessel wash", "home cleaning"
        ],
        "Water Tank Cleaning": [
            "tank cleaning", "water tank", "sump cleaning", "overhead tank"
        ],
        "Home Organizer": [
            "organizer", "closet", "wardrobe organization", "kitchen organization", "declutter"
        ],
        "Gardener": [
            "plants", "grass", "lawn", "gardening", "pruning", "seeds", "potting"
        ],
        "Pest Control Worker": [
            "termite", "cockroach", "mosquito", "bed bug", "pest control", "ants"
        ],
        "Packers & Movers Helper": [
            "packing", "moving", "shifting", "bubble wrap", "box packing"
        ],
        "Warehouse Labour": [
            "warehouse", "inventory", "stock", "factory labour", "sorting"
        ],
        "Loading/Unloading Worker": [
            "loading", "unloading", "heavy lifting", "shifting labour", "truck load"
        ]
    }

    # Check each service and its keywords
    for service, keywords in services.items():
        for keyword in keywords:
            if keyword in text:
                return service

    return "unknown"

def chatbot_response(text):
    """
    Returns a reply based on pattern matching logic.
    """
    import re
    text = text.lower()
    
    # Priority 1: Specific Service Request with Booking/Interest
    service = detect_service(text)
    if service != "unknown":
        if re.search(r'book|hire|get|need|want|find|booking|looking', text):
            return f"To book a {service}, just go to our 'Services' page, find a professional you like, and click the 'Book Now' button on their details page. It's that easy!"
        else:
            return f"It looks like you're interested in our {service} services. You can view all available professionals in that category on the 'Services' page."

    # Priority 2: General Patterns
    responses = [
        (r'\b(hi|hello|hey|greetings|hiya)\b', "Hello! How can I help you today? I can help you find services like electricians, plumbers, or drivers."),
        (r'\b(ok|okay|cool|nice|fine|great|awesome)\b', "Got it! Let me know if you'd like to find a service or if you have any questions."),
        (r'\b(yes|yeah|yep|sure|absolutely)\b', "Great! What service are you looking for? (e.g., plumber, electrician)"),
        (r'\b(no|nope|not now|nah)\b', "No problem! I'm here if you change your mind. What else can I help you with?"),
        (r'\b(bye|goodbye|see you)\b', "Goodbye! Have a great day ahead."),
        (r'\b(thank you|thanks)\b', "You're welcome! Let me know if you need anything else."),
        (r'what (is|are) you|who are you', "I am the LABOURLINK Chatbot. I'm here to help you find and book local service professionals."),
        (r'how (are|do) you', "I'm doing great! Ready to help you find the best workers in your area."),
        (r'help|what can you do', "I can help you find electricians, plumbers, painters, drivers, and many more professionals. Just tell me what you're looking for!"),
        (r'location|where|area', "We provide services in your local area. You can see available workers on the 'Services' page or search for specific ones."),
        (r'price|cost|money', "Prices vary depending on the service and the professional. You can see the details on each service page."),
        (r'how (can|do) i (book|hire|get)', "To book a service, click on 'Services' in the navigation bar, choose the professional you need, and click 'Book Now' on their profile."),
        (r'book|hire|appointment', "You can book any service by visiting our 'Services' page and searching for the professional you need."),
    ]
    
    for pattern, response in responses:
        if re.search(pattern, text):
            return response
            
    return "I'm not sure I understand. Could you please rephrase that or ask about a specific service like 'electrician', 'plumber', or 'Tiles Worker'?"
