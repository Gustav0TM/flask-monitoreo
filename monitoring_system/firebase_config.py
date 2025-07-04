import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Inicializa la aplicación con las credenciales
cred = credentials.Certificate('monitoring_system/config/agentemonitoreo-4e521-firebase-adminsdk-fbsvc-864f96354b.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://agentemonitoreo-4e521-default-rtdb.firebaseio.com/'
})

# Referencia a la base de datos
db_ref = db.reference()