import pymysql

class DAOVehiculos:
    def connect(self):
        return pymysql.connect(
            host="db",
            user="root",
            password="root",
            db="db_icc",
            cursorclass=pymysql.cursors.DictCursor  # Para devolver resultados como diccionarios
        )

    def get_all(self):
        con = self.connect()
        cursor = con.cursor()
        try:
            cursor.execute("SELECT * FROM vehiculos ORDER BY id ASC")
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener vehículos: {e}")
            return []
        finally:
            con.close()

    def get_by_id(self, id):
        con = self.connect()
        cursor = con.cursor()
        try:
            cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (id,))
            return cursor.fetchone()
        except Exception as e:
            print(f"Error al obtener vehículo por ID: {e}")
            return None
        finally:
            con.close()

    # Método para insertar un vehículo
    def insert(self, data):
        con = self.connect()
        cursor = con.cursor()
        try:
            query = """
            INSERT INTO vehiculos 
            (placa, marca, modelo, color, propietario, telefono_contacto, email_contacto, estado_ubicacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['placa'], data['marca'], data['modelo'], data['color'],
                data['propietario'], data['telefono_contacto'], data['email_contacto'],
                data['estado_ubicacion']
            ))
            con.commit()
            return True
        except Exception as e:
            print(f"Error al insertar vehículo: {e}")
            con.rollback()
            return False
        finally:
            con.close()

    def get_filtered(self, placa='', estado=''):
        connection = self.connect()
        cursor = connection.cursor()
        try:
            query = "SELECT * FROM vehiculos WHERE 1=1"
            params = []

            if placa:
                query += " AND placa LIKE %s"
                params.append(f"%{placa}%")
            
            if estado:
                query += " AND estado_ubicacion = %s"
                params.append(estado)

            print(f"Query ejecutada: {query}")  # Depuración
            print(f"Parámetros: {params}")  # Depuración

            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al filtrar vehículos: {e}")
            return []
        finally:
            connection.close()