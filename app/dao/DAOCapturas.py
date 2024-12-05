import pymysql

class DAOCapturas:
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
            cursor.execute("SELECT * FROM capturas ORDER BY fecha_captura DESC")
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener capturas: {e}")
            return []
        finally:
            con.close()
    def read(self, idCaptura=None, solo_no_identificados=False):
        """
        Lee capturas de la base de datos.

        :param idCaptura: ID específico de la captura, si se quiere obtener un único registro.
        :param solo_no_identificados: Si es True, solo retorna capturas con estado_identificado='NO'.
        :return: Un diccionario con los datos de la captura o una lista de diccionarios si no se especifica un ID.
        """
        try:
            with self.connect() as con:
                with con.cursor(pymysql.cursors.DictCursor) as cursor:  # Usar DictCursor para facilitar el acceso a los campos
                    if idCaptura:  # Filtra por un ID específico
                        cursor.execute("SELECT * FROM capturas WHERE id = %s", (idCaptura,))
                        row = cursor.fetchone()
                        if row:
                            return {
                                'id': row['id'],
                                'placa_detectada': row['placa_detectada'],
                                'imagen_placa': row['imagen_placa'],
                                'fecha_captura': row['fecha_captura'],
                                'estado_identificado': row['estado_identificado'],
                                'vehiculo_id': row['vehiculo_id']
                            }
                        return None
                    elif solo_no_identificados:  # Devuelve solo las capturas no identificadas
                        cursor.execute("SELECT * FROM capturas WHERE estado_identificado = 'NO' ORDER BY fecha_captura DESC")
                    else:  # Devuelve todas las capturas
                        cursor.execute("SELECT * FROM capturas ORDER BY fecha_captura DESC")
                    
                    result = cursor.fetchall()
                    return [
                        {
                            'id': row['id'],
                            'placa_detectada': row['placa_detectada'],
                            'imagen_placa': row['imagen_placa'],
                            'fecha_captura': row['fecha_captura'],
                            'estado_identificado': row['estado_identificado'],
                            'vehiculo_id': row['vehiculo_id']
                        }
                        for row in result
                    ]
        except pymysql.MySQLError as e:
            print(f"Error en la consulta: {e}")
            return None



    def insert(self, data):
        con = self.connect()
        cursor = con.cursor()
        try:
            cursor.execute("""
                INSERT INTO capturas 
                (placa_detectada, imagen_placa, estado_identificado, vehiculo_id)
                VALUES (%s, %s, %s, %s)
            """, (
                data['placa_detectada'], data['imagen_placa'], 
                data['estado_identificado'], data['vehiculo_id']
            ))
            con.commit()
            return True
        except Exception as e:
            print(f"Error al insertar captura: {e}")
            con.rollback()
            return False
        finally:
            con.close()


    def get_all_with_identification_status(self):
        con = self.connect()
        cursor = con.cursor()
        try:
            query = """
            SELECT 
                c.placa_detectada, 
                COALESCE(c.imagen_placa, 'default.png') AS imagen_placa,
                c.fecha_captura, 
                CASE 
                    WHEN v.placa IS NOT NULL THEN 'SI' 
                    ELSE 'NO' 
                END AS estado_identificado
            FROM capturas c
            LEFT JOIN vehiculos v ON c.placa_detectada = v.placa
            ORDER BY c.fecha_captura DESC;
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener capturas: {e}")
            return []
        finally:
            con.close()
            
    def get_filtered(self, fecha_inicio=None, fecha_fin=None, placa=None, estado=None):
        con = self.connect()
        cursor = con.cursor()
        try:
            query = """
            SELECT 
                c.placa_detectada, 
                COALESCE(c.imagen_placa, 'default.png') AS imagen_placa,
                c.fecha_captura, 
                CASE 
                    WHEN v.placa IS NOT NULL THEN 'SI' 
                    ELSE 'NO' 
                END AS estado_identificado
            FROM capturas c
            LEFT JOIN vehiculos v ON c.placa_detectada = v.placa
            WHERE 1=1
            """
            params = []

            # Filtros opcionales
            if fecha_inicio:
                query += " AND c.fecha_captura >= %s"
                params.append(fecha_inicio)
            if fecha_fin:
                query += " AND c.fecha_captura <= %s"
                params.append(fecha_fin)
            if placa:
                query += " AND c.placa_detectada LIKE %s"
                params.append(f"%{placa}%")
            if estado:
                query += " AND (CASE WHEN v.placa IS NOT NULL THEN 'SI' ELSE 'NO' END) = %s"
                params.append(estado)

            query += " ORDER BY c.fecha_captura DESC"
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error al obtener capturas filtradas: {e}")
            return []
        finally:
            con.close()