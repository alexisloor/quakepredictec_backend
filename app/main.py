# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, auth
from .database import engine, Base, get_db

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

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
