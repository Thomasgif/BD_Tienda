"""
===================================================================
MÓDULO DE CONEXIÓN A SUPABASE (POSTGRESQL & SUPABASE CLIENT)
===================================================================
Este módulo gestiona el acceso a la base de datos en la nube de Supabase.

Proporciona:
1. Pool de Conexiones PostgreSQL (psycopg2) de alta velocidad para ejecutar
   consultas SQL relacionales, transacciones ACID, uniones (JOINs) y lotes (batches).
2. Cliente Oficial de Supabase (supabase-py) para operaciones vía API REST.
3. Diccionario inteligente (SmartDict) para garantizar compatibilidad con
   la interfaz gráfica (acceso a 'idEmpleado', 'idVenta', etc.).
===================================================================
"""

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

# 1. Librerías de conexión a Supabase / PostgreSQL
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# 2. Cliente oficial de Supabase (REST API SDK)
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
base_dir = Path(__file__).resolve().parent.parent.parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

_DB_POOL = None
_SUPABASE_CLIENT = None


# ===================================================================
# CLIENTE OFICIAL DE SUPABASE (REST API)
# ===================================================================
def get_supabase_client():
    """
    Retorna una instancia singleton del cliente oficial de Supabase.
    Requiere SUPABASE_URL y SUPABASE_KEY en el archivo .env.
    """
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if url and key and create_client:
            _SUPABASE_CLIENT = create_client(url, key)
    return _SUPABASE_CLIENT


# ===================================================================
# SMART DICT (COMPATIBILIDAD CASE-INSENSITIVE)
# ===================================================================
class SmartDict(dict):
    """
    Diccionario inteligente que permite acceso insensible a mayúsculas/minúsculas.
    Garantiza compatibilidad entre PostgreSQL (que devuelve nombres en minúsculas)
    y el código existente de la interfaz gráfica (que usa CamelCase como 'idEmpleado', 'idVenta').
    """
    def __getitem__(self, key):
        if super().__contains__(key):
            return super().__getitem__(key)
        key_lower = str(key).lower()
        for k, v in self.items():
            if str(k).lower() == key_lower:
                return v
        raise KeyError(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        if super().__contains__(key):
            return True
        key_lower = str(key).lower()
        return any(str(k).lower() == key_lower for k in self.keys())


def _convertir_filas(data):
    """Convierte listas de diccionarios o diccionarios individuales a SmartDict."""
    if data is None:
        return None
    if isinstance(data, list):
        return [SmartDict(row) if isinstance(row, dict) else row for row in data]
    if isinstance(data, dict):
        return SmartDict(data)
    return data


# ===================================================================
# POOL DE CONEXIONES POSTGRESQL (SUPABASE TRANSACTION POOLER)
# ===================================================================
def _get_connection_params():
    database_url = os.getenv("DATABASE_URL")
    if database_url and "yourprojectref" not in database_url and "yourpassword" not in database_url:
        return {"dsn": database_url}
    
    return {
        "host": os.getenv("SUPABASE_DB_HOST", "localhost"),
        "port": int(os.getenv("SUPABASE_DB_PORT", 6543)),
        "dbname": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": os.getenv("SUPABASE_DB_USER", "postgres"),
        "password": os.getenv("SUPABASE_DB_PASSWORD", "")
    }


def _inicializar_pool():
    global _DB_POOL
    if _DB_POOL is None or _DB_POOL.closed:
        params = _get_connection_params()
        min_conn = int(os.getenv("DB_POOL_MIN_CONN", 1))
        max_conn = int(os.getenv("DB_POOL_MAX_CONN", 10))
        try:
            if "dsn" in params:
                _DB_POOL = psycopg2.pool.ThreadedConnectionPool(
                    min_conn, max_conn, dsn=params["dsn"], connect_timeout=10
                )
            else:
                _DB_POOL = psycopg2.pool.ThreadedConnectionPool(
                    min_conn, max_conn, **params, connect_timeout=10
                )
        except Exception as e:
            raise Exception(f"Error al inicializar conexión con Supabase (PostgreSQL): {e}")


def obtener_conexion(rol=None):
    """
    Obtiene una conexión activa desde el pool persistente hacia Supabase.
    """
    global _DB_POOL
    _inicializar_pool()
    try:
        conn = _DB_POOL.getconn()
        if conn.closed:
            _DB_POOL.putconn(conn, close=True)
            conn = _DB_POOL.getconn()
        return conn
    except Exception as e:
        _DB_POOL = None
        _inicializar_pool()
        return _DB_POOL.getconn()


def liberar_conexion(conn, close=False):
    """Devuelve la conexión al pool para ser reutilizada inmediatamente sin reconectar."""
    global _DB_POOL
    if _DB_POOL and not _DB_POOL.closed and conn:
        try:
            _DB_POOL.putconn(conn, close=close)
        except Exception:
            pass


@contextmanager
def db_cursor(commit=False, dictionary=True):
    """
    Context manager de alta eficiencia para ejecutar consultas a Supabase.
    Garantiza manejo de errores, rollback automático, liberación inmediata de la conexión al pool
    y retorno de datos enriquecidos (SmartDict).
    """
    conn = obtener_conexion()
    cursor_factory = RealDictCursor if dictionary else None
    cursor = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield cursor, conn
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        liberar_conexion(conn)


def validar_credenciales(usuario, contrasena):
    """
    Valida credenciales de empleado en Supabase (tabla EMPLEADO).
    """
    try:
        with db_cursor(commit=False, dictionary=True) as (cursor, _):
            consulta = """
                SELECT idEmpleado, nombre, documento, correo, rol 
                FROM EMPLEADO 
                WHERE (correo = %s OR documento = %s) 
                  AND documento = %s
                LIMIT 1
            """
            cursor.execute(consulta, (usuario, usuario, contrasena))
            empleado = cursor.fetchone()
            if empleado:
                empleado = SmartDict(empleado)
                empleado['rol'] = int(empleado.get('rol', 0))
                return empleado
            return None
    except Exception as e:
        raise Exception(f"Error al validar credenciales en Supabase: {e}")
