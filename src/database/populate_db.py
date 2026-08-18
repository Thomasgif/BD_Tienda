import sys
import os
from pathlib import Path

# Agregamos la carpeta 'src' al path de python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.base import obtener_conexion, liberar_conexion


def ejecutar_script_sql(ruta_archivo, nombre_script="Script"):
    if not os.path.exists(ruta_archivo):
        print(f"[ERROR] No se encontró el archivo SQL en: {ruta_archivo}")
        return False

    conn = None
    try:
        print(f"\n--- Ejecutando {nombre_script} ({os.path.basename(ruta_archivo)}) ---")
        conn = obtener_conexion()
        cursor = conn.cursor()

        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido_sql = f.read()

        cursor.execute(contenido_sql)
        conn.commit()
        cursor.close()
        print(f"[EXITO] {nombre_script} ejecutado correctamente en Supabase.")
        return True
    except Exception as e:
        print(f"[ERROR] Fallo al ejecutar {nombre_script}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            liberar_conexion(conn)


def inicializar_supabase():
    print("==========================================================")
    print("   INICIALIZACIÓN DE BASE DE DATOS EN SUPABASE (POSTGRESQL)")
    print("==========================================================")

    root_dir = Path(__file__).resolve().parent.parent.parent
    schema_path = root_dir / "Supabase_Schema.sql"
    seed_path = root_dir / "Supabase_Seed.sql"

    # 1. Ejecutar Schema
    ok_schema = ejecutar_script_sql(str(schema_path), "Esquema de Tablas e Índices (Schema)")
    if ok_schema:
        # 2. Ejecutar Seed
        ejecutar_script_sql(str(seed_path), "Datos Iniciales y de Prueba (Seed)")

    print("\nProceso de inicialización finalizado.")


if __name__ == "__main__":
    inicializar_supabase()
