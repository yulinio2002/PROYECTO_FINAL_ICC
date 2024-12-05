import os
import pymysql
import threading
import time
from flask import Flask, flash, render_template, redirect, url_for, request, session
from datetime import datetime  # Importar datetime para manejar fechas y horas
from dao.DAOUsuario import DAOUsuario
from dao.DAOVehiculos import DAOVehiculos
from dao.DAOCapturas import DAOCapturas
from dao.DAOEventos import DAOEventos
from werkzeug.utils import secure_filename
import uuid  # Para generar nombres únicos
####PARA PROCESAMIENTO######
from flask import Flask, Response
import cv2
from PIL import Image
import easyocr
from inference_sdk import InferenceHTTPClient
import numpy as np
from collections import Counter
import os

app = Flask(__name__)
app.secret_key = "mys3cr3tk3y"
db = DAOUsuario()
vehiculos_dao = DAOVehiculos()
capturas_dao = DAOCapturas()
eventos_dao = DAOEventos()

# Configuración para la carpeta de imágenes
IMAGE_DIR = "static/images"

# Clase para procesar imágenes
class ImageProcessor:
    def __init__(self):
        self.image_dir = IMAGE_DIR

    def connect_to_db(self):
        return pymysql.connect(
            host="db",
            user="root",
            password="root",
            db="db_icc",
            cursorclass=pymysql.cursors.DictCursor
        )

    def process_new_images(self):
        try:
            con = self.connect_to_db()
            cursor = con.cursor()

            for file in os.listdir(self.image_dir):
                if file.startswith("placa_") and (file.endswith(".png") or file.endswith(".jpg")):
                    placa = file.replace("placa_", "").replace(".png", "").replace(".jpg", "")
                    image_path = f"static/images/{file}"  # Ruta relativa para la base de datos
                    print(f"Procesando archivo: {file} (Placa detectada: {placa})")

                    # Verificar si ya existe en la tabla `capturas`
                    cursor.execute("SELECT * FROM capturas WHERE placa_detectada = %s", (placa,))
                    result = cursor.fetchone()
                    print(f"¿Registro existente en capturas? {'Sí' if result else 'No'}")

                    if not result:  # Si no existe, insertar
                        # Verificar si la placa está registrada en `vehiculos`
                        cursor.execute("SELECT * FROM vehiculos WHERE placa = %s", (placa,))
                        vehiculo = cursor.fetchone()
                        print(f"¿Placa registrada en vehículos? {'Sí' if vehiculo else 'No'}")

                        estado_identificado = 'SI' if vehiculo else 'NO'

                        # Insertar en la tabla `capturas`
                        cursor.execute("""
                            INSERT INTO capturas (placa_detectada, imagen_placa, estado_identificado, vehiculo_id)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            placa,
                            image_path,
                            estado_identificado,
                            vehiculo['id'] if vehiculo else None
                        ))
                        con.commit()
                        print(f"Registro insertado: Placa={placa}, Imagen={image_path}, Identificado={estado_identificado}")

        except Exception as e:
            print(f"Error al procesar imágenes: {e}")
        finally:
            con.close()
            
    # Función para ejecutar el procesador en un hilo

# Función para ejecutar el procesador en un hilo
def start_image_processor():
    processor = ImageProcessor()
    while True:
        processor.process_new_images()
        time.sleep(10)  # Revisar cada 10 segundos por nuevas imágenes
          
###### LOGIN ######
# Ruta inicial redirige al login
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/inactivo')
def inactivo():
    return render_template('login/inactivo.html')

# Ruta para el login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:  # Validar que ambos campos estén presentes
            flash('Debes ingresar un nombre de usuario y contraseña', 'danger')
            return redirect(url_for('login'))

        # Validar credenciales en la base de datos
        usuarios = db.read(None)  # Obtener todos los usuarios
        for user in usuarios:
            if user['username'] == username and user['password'] == password:  # username y password en la base de datos
                # Validar si el usuario está inactivo
                if user['estado'] == 'inactivo':  # user['estado'] es el campo `estado` en la base de datos
                    return redirect(url_for('inactivo'))  # Redirigir a la página de usuario inactivo
                
                # Si el usuario está activo
                session['username'] = username  # Guardar en la sesión
                db.update_ultimo_acceso(user['id'])  # Actualizar último acceso
                return redirect(url_for('usuarioTiempoReal'))

        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login/index.html')  # Mostrar formulario de login

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        username = request.form.get('username')
        contrasena = request.form.get('contrasena')
        repetir_contrasena = request.form.get('repetir_contrasena')

        # Validar que las contraseñas coincidan
        if contrasena != repetir_contrasena:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('register'))

        # Validar que el email y el username sean únicos
        usuarios = db.read(None)
        for user in usuarios:
            if user['email'] == email:
                flash('El correo electrónico ya está registrado', 'danger')
                return redirect(url_for('register'))
            if user['username'] == username:
                flash('El nombre de usuario ya está registrado', 'danger')
                return redirect(url_for('register'))

        # Crear un nuevo usuario
        data = {
            'nombre': nombre,
            'apellido': apellido,
            'email': email,
            'username': username,
            'password': contrasena  # Podrías agregar hashing para mayor seguridad
        }
        if db.insert(data):
            flash('Usuario registrado exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Hubo un error al registrar el usuario. Inténtalo de nuevo.', 'danger')
    
    return render_template('login/register.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('username', None)  # Eliminar la sesión
    return redirect(url_for('login'))
###### FIN LOGIN ######



###### USUARIO-Vehiculo ######
@app.route('/usuario/')
def usuarioTiempoReal():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session.get('username')
    user = db.read_by_username(username)  # Ahora es un diccionario

    if user:
        rol = user['rol']  # Accede al campo 'rol' como clave
    else:
        rol = None

    return render_template('usuario/tiempoReal.html', username=username, rol=rol)

@app.route('/usuario/tomar_captura', methods=['POST'])
def tomar_captura():
    # Simula la acción de capturar y actualizar la imagen
    camera_image_path = os.path.join(IMAGE_DIR, 'camara_tr.png')

    # Si el archivo no existe, usa uno por defecto
    if not os.path.exists(camera_image_path):
        # Asegúrate de tener una imagen de respaldo llamada default_camera.png
        camera_image_path = os.path.join(IMAGE_DIR, 'default_camera.png')

    # Aquí puedes agregar lógica para capturar una imagen real con la cámara
    # Por ejemplo: invocar un script que genere o actualice la imagen `camara_tr.png`

    flash('Imagen de la cámara actualizada.', 'success')
    return redirect(url_for('usuarioTiempoReal'))



@app.route('/usuario/imagenes/', methods=['GET'])
def usuarioImagenes():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    user = db.read_by_username(username)  # Obtener información del usuario, incluyendo el rol

    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('login'))

    rol = user['rol']  # Obtener el rol del usuario (admin, guard, user)

    # Recuperar parámetros de filtro
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    placa = request.args.get('placa')
    estado = request.args.get('estado')

    # Obtener capturas filtradas
    capturas = capturas_dao.get_filtered(fecha_inicio, fecha_fin, placa, estado)

    # Ajustar las rutas de imágenes para mostrar correctamente
    for captura in capturas:
        placa = captura['placa_detectada']
        png_path = f'static/images/placa_{placa}.png'
        jpg_path = f'static/images/placa_{placa}.jpg'

        if os.path.exists(png_path):
            captura['imagen_placa'] = f'static/images/placa_{placa}.png'
        elif os.path.exists(jpg_path):
            captura['imagen_placa'] = f'static/images/placa_{placa}.jpg'
        else:
            captura['imagen_placa'] = 'static/images/default.jpg'

    return render_template(
        'usuario/imagenes.html',
        username=username,
        rol=rol,  # Pasar el rol a la plantilla
        capturas=capturas
    )

def get_db_connection():
    connection = pymysql.connect(host='db',
                                  user='root',
                                  password='root',
                                  db='db_icc')
    return connection

@app.route('/atendido/<int:id>', methods=['POST'])
def atendido(id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Actualizar el estado a "SI" en la base de datos
    cursor.execute('UPDATE capturas SET estado_identificado = "SI" WHERE id = %s', (id,))
    connection.commit()

    cursor.close()
    connection.close()

    # Redirigir de nuevo a la página principal
    return redirect(url_for('usuarioAlertas'))

@app.route('/usuario/alertas/')
def usuarioAlertas():
    capturas=capturas_dao.read(solo_no_identificados=True)

    if 'username' not in session:
        return redirect(url_for('login'))
    username = session.get('username')  # Obtener el nombre de usuario de la sesión
    user = db.read_by_username(username)  # Ahora es un diccionario
    if user and user['estado'] == 'activo':
        placa_filter = request.args.get('placa', '')
        estado_filter = request.args.get('estado', '')

        vehiculos = vehiculos_dao.get_filtered(placa=placa_filter, estado=estado_filter)
    if user:
        rol = user['rol']  # Accede al campo 'rol' como clave
    else:
        rol = None

    return render_template('usuario/alertas.html', username=username, rol=rol,vehiculos=vehiculos,capturas=capturas)


@app.route('/usuario/registroVehiculos/', methods=['GET'])
def registroVehiculos():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    user = db.read_by_username(username)

    if user and user['estado'] == 'activo':
        placa_filter = request.args.get('placa', '')
        estado_filter = request.args.get('estado', '')

        vehiculos = vehiculos_dao.get_filtered(placa=placa_filter, estado=estado_filter)
        return render_template('usuario/registroVehiculos.html', username=username, rol=user['rol'], vehiculos=vehiculos)
    else:
        flash('No tienes permiso para acceder.', 'danger')
        return redirect(url_for('login'))

########### ADMINISTRADOR ###################

@app.route('/administrador/insertarVehiculos/', methods=['GET'])
def insertarVehiculos():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    user = db.read_by_username(username)

    if not user or user['rol'] != 'admin':
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('registroVehiculos'))

    return render_template('administrador/insertarVehiculos.html', username=username, rol=user['rol'])

@app.route('/administrador/guardarVehiculo/', methods=['POST'])
def guardarVehiculo():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    user = db.read_by_username(username)

    if not user or user['rol'] != 'admin':
        flash('No tienes permisos para realizar esta acción.', 'danger')
        return redirect(url_for('registroVehiculos'))

    # Obtener datos del formulario
    data = {
        'placa': request.form.get('placa'),
        'marca': request.form.get('marca'),
        'modelo': request.form.get('modelo'),
        'color': request.form.get('color'),
        'propietario': request.form.get('propietario'),
        'telefono_contacto': request.form.get('telefono_contacto'),
        'email_contacto': request.form.get('email_contacto'),
        'estado_ubicacion': request.form.get('estado_ubicacion', 'Afuera')
    }

    if vehiculos_dao.insert(data):  # Llama al método `insert` en DAOVehiculos
        flash('Vehículo agregado exitosamente.', 'success')
    else:
        flash('Error al agregar el vehículo.', 'danger')

    return redirect(url_for('registroVehiculos'))

@app.route('/administrador/inventarioUser/')
def inventarioUser():
    if 'username' not in session:
        flash('Debes iniciar sesión primero.', 'danger')
        return redirect(url_for('login'))

    username = session.get('username')
    user = db.read_by_username(username)

    if user and user['rol'] == 'admin':  # Ahora accedemos a 'rol' como clave
        usuarios = db.read()  # Obtener todos los usuarios como una lista de diccionarios
        return render_template('administrador/inventarioUser.html', usuarios=usuarios, username=username, rol=user['rol'])

    flash('No tienes permisos para acceder a esta página.', 'danger')
    return redirect(url_for('login'))




@app.route('/administrador/actualizarUsuario/<int:id>', methods=['GET', 'POST'])
def actualizarUsuario(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Obtener usuario logueado y verificar rol
    username = session.get('username')
    user_admin = db.read_by_username(username)

    if not user_admin or user_admin['rol'] != 'admin':
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('login'))

    user = db.read(id)  # Obtener datos del usuario a editar

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        rol = request.form.get('rol')
        estado = request.form.get('estado')

        # Manejar la subida de imagen
        imagen = request.files.get('foto_perfil')
        foto_perfil = user['foto_perfil']  # Mantener la foto actual por defecto

        if imagen and imagen.filename != '':
            carpeta_imagenes = os.path.join('static/images')  # Cambiar ruta aquí
            if not os.path.exists(carpeta_imagenes):
                os.makedirs(carpeta_imagenes)
            ruta_imagen = os.path.join(carpeta_imagenes, imagen.filename)
            imagen.save(ruta_imagen)
            foto_perfil = f'static/images/{imagen.filename}'

        # Actualizar los datos en la base de datos
        data = {
            'id': id,
            'nombre': nombre,
            'apellido': apellido,
            'email': email,
            'username': username,
            'password': password,
            'telefono': telefono,
            'direccion': direccion,
            'rol': rol,
            'estado': estado,
            'foto_perfil': foto_perfil
        }

        if db.update(data):
            flash('Usuario actualizado exitosamente.', 'success')
            return redirect(url_for('inventarioUser'))
        else:
            flash('Error al actualizar el usuario.', 'danger')

    return render_template('administrador/actualizarUsuario.html', usuario=user, username=username, rol=user_admin['rol'])

@app.route('/administrador/guardarUsuario/', methods=['POST'])
def guardarUsuario():
    if 'username' not in session:
        return redirect(url_for('login'))

    username_admin = session.get('username')

    data = {
        'nombre': request.form['nombre'],
        'apellido': request.form['apellido'],
        'email': request.form['email'],
        'username': request.form['username'],
        'password': request.form['password'],
        'telefono': request.form['telefono'],
        'direccion': request.form['direccion'],
        'rol': request.form['rol'],
        'estado': request.form['estado']
    }

    # Manejar la subida de la imagen
    imagen = request.files.get('foto_perfil')
    if imagen and imagen.filename != '':
        carpeta_imagenes = os.path.join('static', 'images')
        if not os.path.exists(carpeta_imagenes):
            os.makedirs(carpeta_imagenes)

        ruta_imagen = os.path.join(carpeta_imagenes, imagen.filename)
        imagen.save(ruta_imagen)
        data['foto_perfil'] = f'static/images/{imagen.filename}'
    else:
        data['foto_perfil'] = None

    if db.insert(data):
        flash(f'Usuario {data["username"]} creado exitosamente por {username_admin}.', 'success')
    else:
        flash(f'Error al crear el usuario {data["username"]}.', 'danger')

    return redirect(url_for('inventarioUser'))

@app.route('/administrador/eliminarUsuario/<int:id>', methods=['POST'])
def eliminarUsuario(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Verificar si el usuario tiene privilegios
    username = session.get('username')
    user = db.read_by_username(username)

    if user and user['rol'] == 'admin':  # Asegurar que solo admin pueda eliminar
        if db.delete(id):  # Llama al método delete en el DAO
            flash(f'Usuario con ID {id} eliminado exitosamente.', 'success')
        else:
            flash(f'Error al eliminar el usuario con ID {id}.', 'danger')
    else:
        flash('No tienes permisos para realizar esta acción.', 'danger')

    return redirect(url_for('inventarioUser'))

@app.route('/administrador/insertarUsuario/', methods=['GET', 'POST'])
def insertarUsuario():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session.get('username')
    user_admin = db.read_by_username(username)

    if not user_admin or user_admin['rol'] != 'admin':
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        return guardarUsuario()

    return render_template('administrador/insertarUsuario.html', username=username, rol=user_admin['rol'])

@app.route('/administrador/')
def administrador():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('administrador/actualizarUsuario.html')

########### FIN ADMINISTRADOR ###################
### POR SI HAY ERROR ###
#@app.errorhandler(404)
#def page_not_found(error):
#   return render_template('error.html')

########### PROCESAMIENTO DE LA CÁMARA ###################

# Configurar cliente de inferencia y OCR
# Configuración del cliente de inferencia
"""
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="rgQrPQMGYFteBv9TbWdo"
)
reader = easyocr.Reader(['en', 'es'])
# Configuración de la cámara
url = "http://192.168.137.146:81/stream"
cap = cv2.VideoCapture(url)
cap.set(3, 640)
cap.set(4, 480)

# Variables globales
plate_texts = []
most_common_plate_img = None
most_common_text = None

# Función para inferir placas
def infer_plate(frame):
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    try:
        result = CLIENT.infer(image, model_id="yolo-plate/3")
        return result
    except Exception as e:
        print(f"Ocurrió un error durante la inferencia: {e}")
        return None

# Extraer texto de la placa
def extract_text(image):
    h, w = image.shape[:2]
    cropped_img = image[int(h * 0.25):int(h * 0.8), :]
    results = reader.readtext(cropped_img)
    plate_text = ' '.join([result[1] for result in results]).upper()
    return plate_text.strip()

# Generar frames procesados
def generate_frames():
    global plate_texts, most_common_plate_img, most_common_text
    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            result = infer_plate(frame)

            if result and 'predictions' in result:
                for detection in result['predictions']:
                    x_min = int(detection['x'] - detection['width'] / 2)
                    y_min = int(detection['y'] - detection['height'] / 2)
                    x_max = int(detection['x'] + detection['width'] / 2)
                    y_max = int(detection['y'] + detection['height'] / 2)

                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

                    plate_img = frame[y_min:y_max, x_min:x_max]
                    plate_text = extract_text(plate_img)

                    if plate_text:
                        plate_texts.append(plate_text)
                        if most_common_text is None or plate_text == most_common_text:
                            most_common_plate_img = plate_img

            if len(plate_texts) >= 10:
                most_common_text = Counter(plate_texts).most_common(1)[0][0]
                print(f"Texto de placa más frecuente: {most_common_text}")
                if most_common_plate_img is not None:
                    os.makedirs("static/images", exist_ok=True)
                    image_name = os.path.join("static/images", f"placa_{most_common_text}.jpg")
                    cv2.imwrite(image_name, most_common_plate_img)
                    print(f"Imagen guardada: {image_name}")
                plate_texts = []
                most_common_plate_img = None
                most_common_text = None

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
"""
if __name__ == '__main__':
    # Iniciar el procesador de imágenes en un hilo separado
    threading.Thread(target=start_image_processor, daemon=True).start()

    # Ejecutar la app Flask
    app.run(debug=True, port=5000)