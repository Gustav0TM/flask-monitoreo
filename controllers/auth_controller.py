from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario_modelo import verificar_credenciales

auth_bp = Blueprint('auth', __name__)

# Ruta para login (inicio de sesión)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        if verificar_credenciales(usuario, clave):
            session['usuario'] = usuario  # Guarda el usuario en la sesión
            flash('Ingreso exitoso.', 'success')
            return redirect(url_for('dashboard.index'))  # Redirige al dashboard
        else:
            flash('Usuario o clave incorrectos.', 'danger')  # Muestra mensaje de error

    return render_template('login.html')  # Muestra el formulario de login

# Ruta para logout (cerrar sesión)
@auth_bp.route('/logout')
def logout():
    session.pop('usuario', None)  # Elimina el usuario de la sesión
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))  # Redirige a la página de login
