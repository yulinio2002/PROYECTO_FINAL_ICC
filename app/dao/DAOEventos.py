import pymysql

class DAOEventos:
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
            cursor.execute("SELECT * FROM eventos ORDER BY fecha_evento DESC")
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener eventos: {e}")
            return []
        finally:
            con.close()

    def insert(self, data):
        con = self.connect()
        cursor = con.cursor()
        try:
            cursor.execute("""
                INSERT INTO eventos (tipo_evento, descripcion, vehiculo_id)
                VALUES (%s, %s, %s)
            """, (
                data['tipo_evento'], data['descripcion'], data['vehiculo_id']
            ))
            con.commit()
            return True
        except Exception as e:
            print(f"Error al insertar evento: {e}")
            con.rollback()
            return False
        finally:
            con.close()