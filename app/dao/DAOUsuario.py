import pymysql
from datetime import datetime  # Importar datetime para manejar fechas y horas

class DAOUsuario:
    def connect(self):
        return pymysql.connect(
            host="db",
            user="root",
            password="root",
            db="db_icc",
            cursorclass=pymysql.cursors.DictCursor  # Esto devuelve resultados como diccionarios
        )

    def read(self, id=None):
        con = self.connect()
        cursor = con.cursor(pymysql.cursors.DictCursor)  # Usar DictCursor para devolver diccionarios
        try:
            if id is None:
                cursor.execute("SELECT * FROM usuario")
                return cursor.fetchall()  # Lista de diccionarios
            else:
                cursor.execute("SELECT * FROM usuario WHERE id = %s", (id,))
                return cursor.fetchone()  # Un diccionario
        except Exception as e:
            print(f"Error al leer usuarios: {e}")
            return None
        finally:
            con.close()


    def insert(self, data):
        con = self.connect()
        cursor = con.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO usuario (nombre, apellido, email, username, password, telefono, direccion, rol, estado, foto_perfil)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data['nombre'], data['apellido'], data['email'], data['username'], 
                    data['password'], data['telefono'], data['direccion'], 
                    data['rol'], data['estado'], data['foto_perfil']
                )
            )
            con.commit()
            return True
        except Exception as e:
            print(f"Error al insertar usuario: {e}")
            con.rollback()
            return False
        finally:
            con.close()
            
            
    def update_ultimo_acceso(self, id):
        con = self.connect()
        cursor = con.cursor()

        try:
            # Actualizar el campo ultimo_acceso con la hora actual
            cursor.execute("UPDATE usuario SET ultimo_acceso = %s WHERE id = %s", (datetime.now(), id))
            con.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar ultimo_acceso: {e}")
            con.rollback()
            return False
        finally:
            con.close()

    
    def read_by_username(self, username):
        con = self.connect()
        cursor = con.cursor()

        try:
            # Consulta para buscar un usuario por username
            cursor.execute("SELECT * FROM usuario WHERE username = %s", (username,))
            return cursor.fetchone()  # Devuelve un diccionario
        except Exception as e:
            print(f"Error al leer usuario por username: {e}")
            return None
        finally:
            con.close()

    def update(self, data):
        con = self.connect()
        cursor = con.cursor()
        try:
            cursor.execute("""
                UPDATE usuario SET 
                    nombre = %s, apellido = %s, email = %s, username = %s, 
                    password = %s, telefono = %s, direccion = %s, 
                    rol = %s, estado = %s, foto_perfil = %s
                WHERE id = %s
            """, (
                data['nombre'], data['apellido'], data['email'], data['username'], 
                data['password'], data['telefono'], data['direccion'], 
                data['rol'], data['estado'], data['foto_perfil'], data['id']
            ))
            con.commit()
            return True
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            con.rollback()
            return False
        finally:
            con.close()
            
            
    def delete(self, id):
        con = self.connect()
        cursor = con.cursor()
        try:
            cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
            con.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar usuario: {e}")
            con.rollback()
            return False
        finally:
            con.close()