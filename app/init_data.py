from sqlalchemy.orm import Session
from .models import City

# Tu lista maestra de coordenadas
CANTONES_MUESTRA = [
    {"canton": "Esmeraldas", "provincia": "Esmeraldas", "lat": 0.9682, "lon": -79.6517},
    {"canton": "Atacames",   "provincia": "Esmeraldas", "lat": 0.8667, "lon": -79.8333},
    {"canton": "Muisne",     "provincia": "Esmeraldas", "lat": 0.6000, "lon": -80.0167},
    {"canton": "Pedernales", "provincia": "Manabí",     "lat": 0.0718, "lon": -80.0532},
    {"canton": "Manta",      "provincia": "Manabí",     "lat": -0.9538, "lon": -80.7208},
    {"canton": "Portoviejo", "provincia": "Manabí",     "lat": -1.0546, "lon": -80.4544},
    {"canton": "Puerto López","provincia": "Manabí",    "lat": -1.5542, "lon": -80.8115},
    {"canton": "Guayaquil",  "provincia": "Guayas",     "lat": -2.1709, "lon": -79.9223},
    {"canton": "Salinas",    "provincia": "Santa Elena","lat": -2.2145, "lon": -80.9515},
    {"canton": "Machala",    "provincia": "El Oro",     "lat": -3.2586, "lon": -79.9605},
    {"canton": "Quito",      "provincia": "Pichincha",  "lat": -0.2299, "lon": -78.5249},
    {"canton": "Latacunga",  "provincia": "Cotopaxi",   "lat": -0.9352, "lon": -78.6155},
    {"canton": "Ambato",     "provincia": "Tungurahua", "lat": -1.2491, "lon": -78.6168},
    {"canton": "Riobamba",   "provincia": "Chimborazo", "lat": -1.6635, "lon": -78.6546},
    {"canton": "Cuenca",     "provincia": "Azuay",      "lat": -2.9001, "lon": -79.0059},
    {"canton": "Tulcán",     "provincia": "Carchi",     "lat": 0.8119, "lon": -77.7173},
    {"canton": "Loja",       "provincia": "Loja",       "lat": -3.9931, "lon": -79.2042},
    {"canton": "Puyo",       "provincia": "Pastaza",    "lat": -1.4924, "lon": -77.9992},
    {"canton": "Tena",       "provincia": "Napo",       "lat": -0.9938, "lon": -77.8129},
    {"canton": "Nueva Loja", "provincia": "Sucumbíos",  "lat": 0.0847,  "lon": -76.8828}
]

def init_cities(db: Session):
    print("Verificando cantones...")
    for data in CANTONES_MUESTRA:
        # Buscamos si la ciudad ya existe por nombre
        city = db.query(City).filter(City.name == data["canton"]).first()
        
        if not city:
            # Si no existe, la creamos
            new_city = City(
                name=data["canton"],
                province=data["provincia"],
                lat=data["lat"],
                lon=data["lon"]
            )
            db.add(new_city)
        else:
            # Si ya existe (quizás sin coordenadas), las actualizamos
            city.province = data["provincia"]
            city.lat = data["lat"]
            city.lon = data["lon"]
    
    db.commit()
    print("Base de datos de cantones actualizada.")