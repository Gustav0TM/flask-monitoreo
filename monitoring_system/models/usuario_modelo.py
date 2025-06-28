usuarios = {
    "admin": "1234",
    "usuario": "abcd"
}

def verificar_credenciales(usuario, clave):
    return usuarios.get(usuario) == clave
