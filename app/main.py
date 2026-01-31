# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, auth
from .database import engine, Base, get_db
from services.predict_service import sismo_service, obtener_reporte_con_historial
from typing import List
from .models import City, Subscription
from .init_data import init_cities

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

# -----------------------------------------------------
# solo para cargar los cantones
try:
    db = SessionLocal()
    init_cities(db)  
    print("Inicialización de datos completada.")
except Exception as e:
    print(f"Error inicializando datos: {e}")
finally:
    db.close()
# -----------------------------------------------------

app = FastAPI(title="QuakePredictEC Backend")

# CORS
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "https://alexisloor.github.io",  # interfaz desplegaada en gitHub pages
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de usuario
@app.post("/register", response_model=schemas.UserOut)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # ¿correo ya existe?
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario registrado con ese correo.",
        )
    # ¿username ya existe?
    if user_in.username:
        existing_username = (
            db.query(models.User)
            .filter(models.User.username == user_in.username)
            .first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso.",
            )

    hashed_password = auth.get_password_hash(user_in.password)

    user = models.User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        username=user_in.username,
        password_hash=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# Login de usuario
@app.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas.")

    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Obtener el usuario actual
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = auth.decode_access_token(token)
    if token_data is None or token_data.email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
        )
    return user

@app.get("/me", response_model=schemas.UserOut)
def read_me(current_user=Depends(get_current_user)):
    return current_user

@app.get("/riesgo-sismico")
def obtener_riesgo(db: Session = Depends(get_db)):
    """
    Retorna la lista de cantones con su predicción de sismo.
    El frontend usará esto para pintar el mapa.
    """
    datos = obtener_reporte_con_historial(db)
    return datos

# Endpoint para listar ciudades
@app.get("/cities", response_model=List[schemas.CityOut])
def list_cities(db: Session = Depends(get_db)):
    return db.query(City).order_by(City.name.asc()).all()

# Suscribirse a varias ciudades (requiere login)
@app.post("/subscribe")
def subscribe(payload: schemas.SubscribeRequest,
              db: Session = Depends(get_db),
              current_user=Depends(get_current_user)):

    # validar que existan
    cities = db.query(City).filter(City.id.in_(payload.city_ids)).all()
    found_ids = {c.id for c in cities}
    missing = [cid for cid in payload.city_ids if cid not in found_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"Ciudades no válidas: {missing}")

    created = 0
    for cid in payload.city_ids:
        exists = db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.city_id == cid
        ).first()
        if not exists:
            db.add(Subscription(user_id=current_user.id, city_id=cid))
            created += 1

    db.commit()
    return {"ok": True, "added": created}

# Ver mis suscripciones
@app.get("/my-subscriptions", response_model=List[schemas.CityOut])
def my_subscriptions(db: Session = Depends(get_db),
                     current_user=Depends(get_current_user)):

    rows = (
        db.query(City)
        .join(Subscription, Subscription.city_id == City.id)
        .filter(Subscription.user_id == current_user.id)
        .order_by(City.name.asc())
        .all()
    )
    return rows

# Desuscribirse de una ciudad
@app.delete("/unsubscribe/{city_id}")
def unsubscribe(city_id: int,
                db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):

    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.city_id == city_id
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No estabas suscrito a esa ciudad.")

    db.delete(sub)
    db.commit()
    return {"ok": True}


@app.post("/seed-cities")
def seed_cities(db: Session = Depends(get_db)):
    names = ["Quito", "Guayaquil", "Cuenca", "Manta"]
    for n in names:
        if not db.query(City).filter(City.name == n).first():
            db.add(City(name=n))
    db.commit()
    return {"ok": True}
