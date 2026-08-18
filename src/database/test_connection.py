import sys
import os
import time
from pathlib import Path

# Agregamos la carpeta 'src' al path de python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.base import obtener_conexion, liberar_conexion, validar_credenciales
from database.clientes import obtener_clientes
from database.productos import obtener_productos
from database.cuentas import obtener_saldos_cuentas


def probar_conexion():
    print("==========================================================")
    print("   PRUEBA DE CONEXIÓN Y RENDIMIENTO A SUPABASE (POSTGRES)")
    print("==========================================================")

    t0 = time.time()
    conn = None
    try:
        print("\n1. Conectando al pool de Supabase...")
        conn = obtener_conexion()
        t_conn = (time.time() - t0) * 1000
        print(f"   [OK] Conexión establecida con éxito en {t_conn:.1f} ms.")

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        v = cursor.fetchone()
        print(f"   [INFO] Servidor PostgreSQL: {v[0] if v else 'N/A'}")
        cursor.close()
        liberar_conexion(conn)
        conn = None

        print("\n2. Probando consultas rápidas de catálogo...")
        t_prod = time.time()
        productos = obtener_productos()
        print(f"   [OK] Productos cargados ({len(productos)} items) en {(time.time() - t_prod) * 1000:.1f} ms.")

        t_cli = time.time()
        clientes = obtener_clientes()
        print(f"   [OK] Clientes cargados ({len(clientes)} items) en {(time.time() - t_cli) * 1000:.1f} ms.")

        t_cta = time.time()
        cuentas = obtener_saldos_cuentas()
        print(f"   [OK] Métodos de pago y saldos ({len(cuentas)} cuentas) en {(time.time() - t_cta) * 1000:.1f} ms.")

        print("\n3. Probando validación de credenciales (Login)...")
        t_auth = time.time()
        gerente = validar_credenciales("0315", "0315")
        if gerente:
            print(f"   [OK] Login Gerente exitoso: {gerente['nombre']} (Rol={gerente['rol']}) en {(time.time() - t_auth) * 1000:.1f} ms.")
        else:
            print("   [AVISO] No se encontró el usuario '0315'. Recuerda ejecutar populate_db.py o Supabase_Seed.sql.")

        print("\n==========================================================")
        print("   ¡TODAS LAS PRUEBAS DE SUPABASE SE COMPLETARON CON ÉXITO!")
        print("==========================================================")

    except Exception as e:
        print("\n[ERROR] No se pudo conectar a Supabase:")
        print(f"Detalle: {e}")
        print("\n--- PASOS DE DIAGNÓSTICO ---")
        print("1. Abre el archivo '.env' en la raíz del proyecto.")
        print("2. Pega tu cadena de conexión 'DATABASE_URL' de Supabase (Settings -> Database -> Connection URI).")
        print("3. Si tu contraseña tiene caracteres especiales, asegúrate de que esté codificada en URL o usa los campos individuales:")
        print("   - SUPABASE_DB_HOST")
        print("   - SUPABASE_DB_PORT (usualmente 6543 o 5432)")
        print("   - SUPABASE_DB_USER")
        print("   - SUPABASE_DB_PASSWORD")
        print("   - SUPABASE_DB_NAME")
        print("4. Ejecuta 'Supabase_Schema.sql' en el SQL Editor de tu panel de Supabase si aún no creas las tablas.")
    finally:
        if conn:
            liberar_conexion(conn)


if __name__ == "__main__":
    probar_conexion()
