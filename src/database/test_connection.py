import sys
import os

# Agregamos la carpeta 'src' al path de python para que pueda encontrar el módulo 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import obtener_conexion, validar_credenciales

def probar_conexion():
    print("=== INICIANDO PRUEBA DE CONEXIÓN CON MYSQL ===")
    try:
        # Intentar conectar
        print("Intentando conectar con los parámetros en connection.py...")
        conn = obtener_conexion()
        print("¡CONEXIÓN EXITOSA!")
        
        # Validar información de versión del servidor
        print(f"Versión del Servidor MySQL: {conn.get_server_info()}")
        
        # Probar consulta a la tabla EMPLEADO
        print("\nVerificando si existen empleados cargados en la tabla...")
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idEmpleado, nombre, documento, correo FROM EMPLEADO")
        empleados = cursor.fetchall()
        
        if empleados:
            print(f"¡Éxito! Se encontraron {len(empleados)} empleado(s) en la base de datos:")
            for emp in empleados:
                print(f" - ID: {emp['idEmpleado']} | Nombre: {emp['nombre']} | Documento: {emp['documento']} | Correo: {emp['correo']}")
        else:
            print("Conexión exitosa, pero la tabla EMPLEADO está vacía. Recuerda ejecutar el script de Inserts.sql.")
            
        cursor.close()
        conn.close()
        print("\nLa conexión se ha cerrado correctamente.")
        
    except Exception as e:
        print("\n[ERROR] No se pudo establecer la conexión.")
        print(f"Detalle del error: {e}")
        print("\n--- PASOS DE DIAGNÓSTICO ---")
        print("1. Verifica que tu servidor local MySQL (XAMPP, WAMP o MySQL Server) esté encendido.")
        print("2. Abre 'src/database/connection.py' y revisa los datos en 'DB_CONFIG':")
        print("   - ¿El usuario es 'root'?")
        print("   - ¿La contraseña está vacía o tiene un valor específico?")
        print("   - ¿El puerto es 3306?")
        print("3. Asegúrate de haber ejecutado 'DesarrolloBD.sql' para crear la base de datos 'BD_Tienda'.")

if __name__ == "__main__":
    probar_conexion()
