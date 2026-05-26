import mysql.connector
from mysql.connector import Error

# CONFIGURACIÓN DE LA BASE DE DATOS
# Puedes modificar estos valores según la configuración de tu MySQL local.
DB_CONFIG = {
    'host': 'localhost',       # Dirección del servidor de Base de Datos (en este caso local)
    'user': 'root',            # Usuario por defecto de MySQL (común en XAMPP, WAMP, etc.)
    'password': '123456',      # Contraseña de tu MySQL. Coloca aquí tu contraseña si la tienes.
    'database': 'bd_tienda',   # Nombre de la base de datos a la cual nos conectaremos
    'port': 3306               # Puerto por defecto de MySQL
}

def obtener_conexion():
    """

    Establece una conexión con la base de datos MySQL.
    
    ¿Cómo funciona?
    Usa la librería mysql-connector-python pasándole el diccionario DB_CONFIG con las credenciales.
    Retorna el objeto 'conexion' si fue exitoso, o lanza un error si falló.
    """
    try:
        # mysql.connector.connect desempaqueta el diccionario DB_CONFIG usando **
        conexion = mysql.connector.connect(**DB_CONFIG)
        
        # Si la conexión está activa, la retornamos
        if conexion.is_connected():
            return conexion
            
    except Error as e:
        # Si algo sale mal (servidor apagado, contraseña incorrecta, base de datos inexistente),
        # lanzamos el error para que la interfaz GUI pueda capturarlo e informar al usuario.
        raise Exception(f"Error al conectar a la base de datos: {e}")

def validar_credenciales(usuario, contrasena):
    """
    Valida si un empleado existe en la base de datos usando su correo o documento como
    identificador de usuario, y su documento como contraseña.
    
    Retorna:
        dict: Con los datos del empleado (id, nombre, correo) si la credencial es correcta.
        None: Si las credenciales no son válidas.
        Lanza Exception: Si ocurre un problema con la base de datos.
    """
    conexion = None
    cursor = None
    try:
        # 1. Obtener la conexión a la base de datos
        conexion = obtener_conexion()
        
        # 2. Crear un cursor
        # El cursor nos permite ejecutar instrucciones SQL y obtener los resultados.
        # Usamos dictionary=True para que el resultado nos sea devuelto como un diccionario de Python.
        cursor = conexion.cursor(dictionary=True)
        
        # 3. Definir la consulta SQL
        # NOTA DE SEGURIDAD IMPORTANTE:
        # Usamos '%s' como marcadores de posición (placeholders) en lugar de concatenar texto directo.
        # Esto previene un problema de seguridad grave llamado "Inyección SQL".
        # La consulta busca un empleado cuyo correo o documento sea el ingresado en 'usuario',
        # y cuyo documento coincida con la 'contrasena'.
        consulta = """
            SELECT idEmpleado, nombre, documento, correo 
            FROM EMPLEADO 
            WHERE (correo = %s OR documento = %s) 
              AND documento = %s
        """
        
        # 4. Ejecutar la consulta pasando los valores reales en una tupla
        # El conector se encarga de escapar y limpiar los valores de forma segura.
        valores = (usuario, usuario, contrasena)
        cursor.execute(consulta, valores)
        
        # 5. Obtener el primer resultado (fetchone)
        # Si no hay coincidencias, retornará None.
        empleado = cursor.fetchone()
        
        return empleado

    except Error as e:
        # Si ocurre un error en la consulta o conexión de base de datos
        raise Exception(f"Error de base de datos: {e}")
        
    finally:
        # 6. Limpieza y Cierre (Cláusula 'finally' siempre se ejecuta)
        # Es fundamental cerrar el cursor y la conexión para liberar recursos en el servidor MySQL.
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()
