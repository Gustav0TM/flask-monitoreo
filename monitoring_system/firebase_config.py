print("Firebase config cargado")
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import os
import json

# Obtener las credenciales desde la variable de entorno
credentials_dict = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
cred = credentials.Certificate(credentials_dict)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://agentemonitoreo-4e521-default-rtdb.firebaseio.com/'
})

# Referencia a la base de datos
db_ref = db.reference()