import sys
import os

# Agregamos la carpeta 'src' al path de python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import obtener_conexion

def cargar_datos_prueba():
    print("=== CARGANDO DATOS DE PRUEBA DESDE InfoPrueba.sql ===")
    
    # Ruta absoluta al archivo InfoPrueba.sql
    ruta_sql = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../InfoPrueba.sql'))
    
    if not os.path.exists(ruta_sql):
        print(f"[ERROR] No se encontró el archivo SQL en: {ruta_sql}")
        return

    conexion = None
    try:
        # Conectarse a MySQL
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # Leer el contenido del archivo SQL
        with open(ruta_sql, 'r', encoding='utf-8') as archivo:
            contenido_sql = archivo.read()
        
        # Separar por punto y coma (;) para obtener sentencias individuales
        sentencias = contenido_sql.split(';')
        
        print("Ejecutando sentencias SQL...")
        for sentencia in sentencias:
            sentencia_limpia = sentencia.strip()
            # Ignorar sentencias vacías o líneas que sean solo comentarios de SQL
            if not sentencia_limpia:
                continue
            # Ejecutar cada sentencia individual
            cursor.execute(sentencia_limpia)
            
        conexion.commit()
        print(f"¡Éxito! Se ejecutaron los comandos de inserción.")
        
    except Exception as e:
        print(f"[ERROR] Ocurrió un error al insertar los datos: {e}")
        if conexion:
            conexion.rollback()
    finally:
        if conexion and conexion.is_connected():
            cursor.close()
            conexion.close()
            print("Conexión cerrada.")

if __name__ == "__main__":
    cargar_datos_prueba()
