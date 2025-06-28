from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from monitoring_system.models.usuario_modelo import verificar_credenciales

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        if verificar_credenciales(usuario, clave):
            session['usuario'] = usuario
            flash('Ingreso exitoso.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Usuario o clave incorrectos.', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()  # Limpia todo lo que haya en la sesión, incluidos mensajes pendientes
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('auth.login'))
