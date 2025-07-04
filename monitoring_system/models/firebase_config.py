import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

class FirebaseManager:
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
            cls._instance._initialize_firebase()
        return cls._instance
    
    def _initialize_firebase(self):
        """Inicializa Firebase con las credenciales"""
        try:
            # Opción 1: Usar archivo de credenciales
            if os.path.exists('firebase-credentials.json'):
                cred = credentials.Certificate('firebase-credentials.json')
                firebase_admin.initialize_app(cred)
            
            # Opción 2: Usar variable de entorno (recomendado para producción)
            elif os.getenv('FIREBASE_CREDENTIALS'):
                cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            
            else:
                raise ValueError("No se encontraron credenciales de Firebase")
            
            self._db = firestore.client()
            print("✓ Firebase inicializado correctamente")
            
        except Exception as e:
            print(f"✗ Error al inicializar Firebase: {str(e)}")
            self._db = None
    
    def get_db(self):
        """Retorna la instancia de Firestore"""
        return self._db
    
    def is_connected(self):
        """Verifica si Firebase está conectado"""
        return self._db is not None

# Instancia global
firebase_manager = FirebaseManager()