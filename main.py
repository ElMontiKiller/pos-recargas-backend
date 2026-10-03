from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

app = FastAPI(title="POS Recargas BDV")

# Sustituye "TU_SERVIC" con la llave service_role que copiaste de Supabase
SUPABASE_URL = "https://eujcxycnqbvhsajcljyd.supabase.co"
SUPABASE_KEY = "sb_secret_gOV4PNlUJwRNSGjDWRiyaA_dyPyFVu3"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estructura de la petición enviada desde FlutterFlow
class SolicitudRecarga(BaseModel):
    operadora: str          # ej: "movistar", "digitel", "cantv", "simpletv"
    telefono_destino: str   # ej: "04141234567"
    monto: float            # ej: 100.00

# Estructura de la confirmación devuelta por el Galaxy A20
class ConfirmacionBDV(BaseModel):
    recarga_id: str
    estado: str             # "exitosa" o "fallida"
    respuesta_banco: str    # Texto del SMS recibido del BDV

@app.post("/solicitar-recarga")
def crear_recarga(data: SolicitudRecarga):
    # Formatear el comando SMS para el Banco de Venezuela
    comando = f"Servicio {data.operadora.lower()} {data.telefono_destino} {int(data.monto)}"
    
    nuevo_registro = {
        "operadora": data.operadora.lower(),
        "telefono_destino": data.telefono_destino,
        "monto": data.monto,
        "comando_sms": comando,
        "estado": "pendiente"
    }
    
    # Guardar la recarga en Supabase
    res = supabase.table("recargas_pos").insert(nuevo_registro).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Error al guardar en Supabase")
    
    orden = res.data[0]
    return {
        "status": "ok",
        "recarga_id": orden["id"],
        "comando_sms": comando,
        "numero_destino": "2661"
    }

@app.post("/confirmar-resultado")
def actualizar_estado(data: ConfirmacionBDV):
    # Actualizar estado cuando responda el BDV
    supabase.table("recargas_pos").update({
        "estado": data.estado,
        "respuesta_banco": data.respuesta_banco
    }).eq("id", data.recarga_id).execute()
    
    return {"status": "ok", "mensaje": "Estado actualizado correctamente"}