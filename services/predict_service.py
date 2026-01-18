import os
import pandas as pd
import requests
import xgboost as xgb 
from sqlalchemy.orm import Session  
from sqlalchemy import func         
from datetime import date
from app import models              

# Ruta al modelo
SERVICES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SERVICES_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "app", "modelo_xgboost.json")

print(f"Configuración de ruta del modelo: {MODEL_PATH}")

# Lista de cantones 
CANTONES_MUESTRA = [
    # COSTA
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
    
    # SIERRA
    {"canton": "Quito",      "provincia": "Pichincha",  "lat": -0.2299, "lon": -78.5249},
    {"canton": "Latacunga",  "provincia": "Cotopaxi",   "lat": -0.9352, "lon": -78.6155},
    {"canton": "Ambato",     "provincia": "Tungurahua", "lat": -1.2491, "lon": -78.6168},
    {"canton": "Riobamba",   "provincia": "Chimborazo", "lat": -1.6635, "lon": -78.6546},
    {"canton": "Cuenca",     "provincia": "Azuay",      "lat": -2.9001, "lon": -79.0059},
    {"canton": "Tulcán",     "provincia": "Carchi",     "lat": 0.8119, "lon": -77.7173},
    {"canton": "Loja",       "provincia": "Loja",       "lat": -3.9931, "lon": -79.2042},
    
    # ORIENTE
    {"canton": "Puyo",       "provincia": "Pastaza",    "lat": -1.4924, "lon": -77.9992},
    {"canton": "Tena",       "provincia": "Napo",       "lat": -0.9938, "lon": -77.8129},
    {"canton": "Nueva Loja", "provincia": "Sucumbíos",  "lat": 0.0847,  "lon": -76.8828}
]

class SismoService:
    def __init__(self):
        self.model = None
        self.feature_names = []
        self.load_model()

    def load_model(self):
        if not os.path.exists(MODEL_PATH):
            print(f"ERROR: No existe el archivo en {MODEL_PATH}")
            return

        print("Cargando motor XGBoost...")
        try:
            self.model = xgb.Booster()
            self.model.load_model(MODEL_PATH)
            self.feature_names = self.model.feature_names
            print("Modelo cargado exitosamente.")
            
        except Exception as e:
            print(f"Error cargando el JSON del modelo: {e}")

    def generar_mapa_riesgo(self):
        if not self.model:
            return {"error": "El modelo no está disponible."}

        resultados = []

        for item in CANTONES_MUESTRA:
            try:
                datos_clima = self.consultar_open_meteo(item['lat'], item['lon'])
                df_input = self.preparar_datos(item, datos_clima)
                
                dmatrix_data = xgb.DMatrix(df_input)
                
                probabilidad = float(self.model.predict(dmatrix_data)[0])
                
                nivel, color = self.calcular_semaforo(probabilidad)

                resultados.append({
                    "canton": item['canton'],
                    "lat": item['lat'],
                    "lon": item['lon'],
                    "probabilidad": round(probabilidad, 4),
                    "nivel_riesgo": nivel,
                    "color": color
                })
                
            except Exception as e:
                print(f"Error procesando {item['canton']}: {e}")
                continue
        
        return resultados

    def consultar_open_meteo(self, lat, lon):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat, "longitude": lon,
            "daily": ["precipitation_sum", "temperature_2m_mean", "pressure_msl_mean"],
            "timezone": "auto", "past_days": 30, "forecast_days": 1
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def preparar_datos(self, ubicacion, data_json):
        daily = pd.DataFrame(data_json['daily'])
        daily = daily.iloc[-31:] 
        
        input_dict = {
            'latitud': ubicacion['lat'],
            'longitud': ubicacion['lon'],
            'precip_sum': daily['precipitation_sum'].sum(),
            'temp_mean': daily['temperature_2m_mean'].mean(),
            'temp_std': daily['temperature_2m_mean'].std(),
            'pres_mean': daily['pressure_msl_mean'].mean(),
            'pres_delta': daily['pressure_msl_mean'].iloc[-1] - daily['pressure_msl_mean'].iloc[0]
        }
        
        df = pd.DataFrame([input_dict])
        
        # Reordenamiento de columnas
        if self.feature_names:
            df = df[self.feature_names]
            
        return df

    def calcular_semaforo(self, prob):
        if prob < 0.30: return "BAJO", "#28a745"
        if prob < 0.70: return "MODERADO", "#ffc107"
        return "ALTO", "#dc3545"

sismo_service = SismoService()


def obtener_reporte_con_historial(db: Session):
    fecha_hoy = date.today()
    print(f"Consultando historial para: {fecha_hoy}")

    # 1. Buscar en BD
    registros_hoy = db.query(models.PredictionReport).filter(
        func.date(models.PredictionReport.created_at) == fecha_hoy
    ).all()

    # 2. ESCENARIO A: YA EXISTEN (Retornar desde BD)
    if registros_hoy:
        print(f"Se encontraron {len(registros_hoy)} registros en BD.")
        
        # Reconstruir la respuesta para el frontend (agregando lat/lon/color)
        resultados_reconstruidos = []
        
        # Crear un mapa rápido de cantones para buscar lat/lon por nombre
        mapa_cantones = {c['canton']: c for c in CANTONES_MUESTRA}
        
        for reporte in registros_hoy:
            # Recuperar datos estáticos del mapa
            info_geo = mapa_cantones.get(reporte.location, {"lat": 0, "lon": 0})
            
            # Recalcular color (es lógica visual, no se guarda en BD para ahorrar espacio)
            _, color = sismo_service.calcular_semaforo(reporte.probability)
            
            resultados_reconstruidos.append({
                "canton": reporte.location,
                "lat": info_geo["lat"],
                "lon": info_geo["lon"],
                "probabilidad": reporte.probability,
                "nivel_riesgo": reporte.risk_level,
                "color": color,
                "fecha": reporte.created_at # Opcional
            })
            
        return resultados_reconstruidos

    # 3. ESCENARIO B: NO EXISTEN (Calcular y Guardar)
    print("No hay registros de hoy. Iniciando cálculo con XGBoost...")
    
    # Calcular usando la clase existente
    nuevas_predicciones = sismo_service.generar_mapa_riesgo()
    
    # Verificar si hubo error en el cálculo
    if isinstance(nuevas_predicciones, list) and len(nuevas_predicciones) > 0 and "error" in nuevas_predicciones[0]:
         print("Error en cálculo, no se guardará en BD.")
         return nuevas_predicciones

    # Guardar en Postgres
    try:
        for item in nuevas_predicciones:
            nuevo_registro = models.PredictionReport(
                location=item['canton'],
                probability=item['probabilidad'],
                risk_level=item['nivel_riesgo']
            )
            db.add(nuevo_registro)
        
        db.commit()
        print("Nuevas predicciones guardadas exitosamente en la base Postgres.")
    except Exception as e:
        print(f"Error guardando en BD: {e}")
        db.rollback()
    
    return nuevas_predicciones
