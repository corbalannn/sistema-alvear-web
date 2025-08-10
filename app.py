"""
Sistema de Gestión Textil Alvear - Aplicación Principal
======================================================

Sistema modular para gestión de stock, reportes y control de inventario textil.
Versión con API de movimientos funcionando - Deploy v1.1

Módulos incluidos:
- Depósito: Gestión de stock, ingresos, reportes
- Dashboard: Estadísticas y gráficos en tiempo real
- Configuración: Umbrales de stock y parámetros

Autor: Sistema Alvear
Versión: 1.1
Fecha: 2025
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
from collections import defaultdict
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# =====================================
# CONFIGURACIÓN DE LA APLICACIÓN
# =====================================

app = Flask(__name__)

# =====================================
# INICIALIZACIÓN AUTOMÁTICA PARA GUNICORN
# =====================================

def safe_init():
    """Inicialización segura que no bloquea el arranque"""
    try:
        print("🚀 [GUNICORN] Inicializando base de datos...")
        init_database()
        print("✅ [GUNICORN] Base de datos inicializada")
    except Exception as e:
        print(f"⚠️ [GUNICORN] Error en DB (continuando): {e}")
    
    try:
        verificar_archivos_datos()
        print("✅ [GUNICORN] Archivos verificados")
    except Exception as e:
        print(f"⚠️ [GUNICORN] Error en archivos (continuando): {e}")

# Configuración de base de datos
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_data.db')
print(f"🔄 DATABASE_URL obtenida: {DATABASE_URL[:80]}...")

# Si DATABASE_URL usa postgres://, convertir a postgresql://
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    print("🔄 Convertida postgres:// a postgresql://")

engine = None

def init_database():
    """Inicializar conexión a la base de datos"""
    global engine
    try:
        print(f"🔗 Intentando conectar a: {DATABASE_URL[:50]}...")
        
        if not DATABASE_URL or DATABASE_URL == 'sqlite:///local_data.db':
            print("❌ No hay DATABASE_URL válida - usando modo local")
            return
            
        print("🔧 Creando engine...")
        engine = create_engine(DATABASE_URL)
        print("✅ Engine creado exitosamente")
        
        # Probar conexión
        print("🔗 Probando conexión...")
        with engine.connect() as conn:
            print("✅ Conexión PostgreSQL exitosa")
        
        # Crear tablas si no existen
        print("📝 Creando tablas...")
        with engine.connect() as conn:
            # Tabla de stock
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stock (
                    codigo VARCHAR(255) PRIMARY KEY,
                    tipo VARCHAR(100),
                    titulo VARCHAR(50),
                    caracteristica VARCHAR(100),
                    color VARCHAR(50),
                    formato VARCHAR(20),
                    lote VARCHAR(50),
                    ubicacion VARCHAR(100),
                    proveedor VARCHAR(100),
                    cantidad INTEGER,
                    kilos_por_caja FLOAT,
                    conos_por_caja INTEGER,
                    descripcion_cono TEXT,
                    fecha_ingreso TIMESTAMP,
                    ultima_modificacion TIMESTAMP
                )
            """))
            
            # Tabla de movimientos
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS movimientos (
                    id SERIAL PRIMARY KEY,
                    fecha TIMESTAMP,
                    tipo VARCHAR(50),
                    codigo VARCHAR(255),
                    descripcion TEXT,
                    cantidad INTEGER,
                    ubicacion VARCHAR(100),
                    usuario VARCHAR(100)
                )
            """))
            
            conn.commit()
            print("✅ Base de datos PostgreSQL inicializada correctamente")
            print(f"🎯 Conectado a: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
            
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")
        print(f"🔄 DATABASE_URL: {DATABASE_URL[:80]}...")
        # Fallback a archivos JSON si falla la DB
        pass

# Configuración de rutas de datos
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
STOCK_FILE = os.path.join(DATA_DIR, 'stock.json')
STOCK_INICIAL_FILE = os.path.join(DATA_DIR, 'stock_inicial.json')
UMBRALES_FILE = os.path.join(DATA_DIR, 'umbrales_config.json')
MOVIMIENTOS_FILE = os.path.join(DATA_DIR, 'movimientos.json')

# =====================================
# CONFIGURACIÓN DE DATOS MAESTROS
# =====================================

# Configuración de umbrales por defecto
UMBRALES_STOCK_BAJO_DEFAULT = {
    "Algodón": {"cajas": 10, "Palletizado": 3},
    "Snow": {"cajas": 8, "Palletizado": 2},
    "Spun": {"cajas": 8, "Palletizado": 2},
    "Poal": {"cajas": 12, "Palletizado": 4},
    "Melange": {"cajas": 6, "Palletizado": 2},
    "Poliester": {"cajas": 5, "Palletizado": 1},
    "Elastano": {"cajas": 3, "Palletizado": 1}
}
 #as
# Catálogo completo de hilos
CATALOGO_DE_HILOS = {
    "Algodón": {
        "10/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "12/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "14/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "16/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "20/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "24/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "28/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
        "30/1": {"caracteristica": ["Peinado", "Cardado", "Super Cardado", "Open End"]},
    },
    "Snow": {
        "20/1": {"caracteristica": ["Estándar"]},
        "30/1": {"caracteristica": ["Estándar"]},
    },
    "Spun": {
        "24/1": {"caracteristica": ["Estándar"]},
        "30/1": {"caracteristica": ["Estándar"]},
    },
    "Poal": {
        "10/1": {"caracteristica": ["Estándar"]},
        "20/1": {"caracteristica": ["Estándar"]},
        "24/1": {"caracteristica": ["Estándar"]},
        "30/1": {"caracteristica": ["Estándar"]},
    },
    "Melange": {
        "20/1": {"caracteristica": ["6%", "15%", "25%", "50%", "75%", "100%"]},
        "24/1": {"caracteristica": ["6%", "15%", "25%", "50%", "75%", "100%"]},
        "30/1": {"caracteristica": ["6%", "15%", "25%", "50%", "75%", "100%"]},
    },
    "Poliester": {
        "75/72": {"caracteristica": ["Estándar"]},
        "75/36": {"caracteristica": ["Estándar"]},
        "150/48": {"caracteristica": ["Estándar"]},
        "150/144": {"caracteristica": ["Estándar"]},
    },
    "Elastano": {
        "20": {"caracteristica": ["Estándar"]},
        "40": {"caracteristica": ["Estándar"]},
        "70": {"caracteristica": ["Estándar"]},
    }
}

# Listas de datos maestros
LISTA_DE_COLORES = ["crudo", "blanco", "negro"]
LISTA_DE_FORMATOS = ["cajas", "Palletizado"]
LISTA_DE_UBICACIONES = [
    "deposito de descarga", 
    "deposito principal", 
    "deposito tejeduria", 
    "deposito auxiliar"
]

# Configuración de proveedores
LISTA_DE_PROVEEDORES = {
    "T&N Platex": {
        "nombre": "T&N Platex",
        "descripcion": "Empresa textil especializada en hilados de algodón",
        "logo_url": "/static/images/proveedores/tn_platex.png",
        "colores_corporativos": ["#4f46e5", "#ffffff"],
        "productos": ["Algodón", "Melange"]
    },
    "Tecotex": {
        "nombre": "Tecotex S.A.", 
        "descripcion": "Líderes en producción de hilado y tejido plano desde 1950",
        "logo_url": "/static/images/proveedores/tecotex.png",
        "colores_corporativos": ["#1a365d", "#ffffff"],
        "productos": ["Algodón", "Snow", "Spun", "Poliester"]
    },
    "Emilio Alal": {
        "nombre": "Emilio Alal S.A.",
        "descripcion": "Empresa textil argentina con tradición en hilados especiales",
        "logo_url": "/static/images/proveedores/emilio_alal.png",
        "colores_corporativos": ["#059669", "#ffffff"],
        "productos": ["Poal", "Elastano", "Melange"]
    }
}

# Parámetros de carga por defecto
PARAMETROS_CARGA_DEFAULT = {
    "cajas": {
        "kilos_por_caja": 25,
        "conos_por_caja": 12,
        "descripcion_cono": "Conos estándar"
    },
    "Palletizado": {
        "kilos_por_pallet": 500,
        "cajas_por_pallet": 20,
        "descripcion": "Pallet estándar"
    }
}

# =====================================
# FUNCIONES DE GESTIÓN DE DATOS
# =====================================

def verificar_archivos_datos():
    """Verificar y crear archivos de datos necesarios si no existen"""
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"📁 Directorio de datos: {DATA_DIR}")
    
    if not os.path.exists(DATA_DIR):
        print(f"📁 Creando directorio: {DATA_DIR}")
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(STOCK_FILE):
        print(f"📄 Creando stock.json vacío")
        with open(STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    
    if not os.path.exists(UMBRALES_FILE):
        print(f"📄 Creando umbrales_config.json")
        with open(UMBRALES_FILE, 'w', encoding='utf-8') as f:
            json.dump(UMBRALES_STOCK_BAJO_DEFAULT, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Archivos verificados")
    print(f"   - Stock: {os.path.exists(STOCK_FILE)}")
    print(f"   - Umbrales: {os.path.exists(UMBRALES_FILE)}")

def cargar_stock():
    """Cargar datos del stock desde PostgreSQL o JSON como fallback"""
    try:
        if engine:
            # Usar PostgreSQL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM stock"))
                rows = result.fetchall()
                
                stock_data = {}
                for row in rows:
                    stock_data[row.codigo] = {
                        'tipo': row.tipo,
                        'titulo': row.titulo,
                        'caracteristica': row.caracteristica,
                        'color': row.color,
                        'formato': row.formato,
                        'lote': row.lote,
                        'ubicacion': row.ubicacion,
                        'proveedor': row.proveedor,
                        'cantidad': row.cantidad,
                        'kilos_por_caja': row.kilos_por_caja,
                        'conos_por_caja': row.conos_por_caja,
                        'descripcion_cono': row.descripcion_cono,
                        'fecha_ingreso': row.fecha_ingreso.isoformat() if row.fecha_ingreso else None,
                        'ultima_modificacion': row.ultima_modificacion.isoformat() if row.ultima_modificacion else None
                    }
                
                print(f"✅ Stock cargado desde PostgreSQL: {len(stock_data)} productos")
                return stock_data
        
        # Fallback a JSON (desarrollo local)
        return cargar_stock_json()
        
    except Exception as e:
        print(f"❌ Error al cargar desde PostgreSQL, usando JSON: {e}")
        return cargar_stock_json()

def cargar_stock_json():
    """Cargar datos del stock desde JSON (fallback)"""
    try:
        # Primero intentar cargar stock.json
        if os.path.exists(STOCK_FILE):
            with open(STOCK_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Stock cargado desde JSON: {len(data)} productos")
                return data
        
        # Si no existe, usar stock_inicial.json
        elif os.path.exists(STOCK_INICIAL_FILE):
            with open(STOCK_INICIAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Stock inicial cargado: {len(data)} productos")
                return data
        
        # Si ninguno existe, usar datos por defecto embebidos
        else:
            print(f"⚠️ Usando datos por defecto embebidos")
            datos_por_defecto = {
                "Algodón_24/1_Peinado_crudo_y144p_deposito_de_descarga": {
                    "tipo": "Algodón",
                    "titulo": "24/1",
                    "caracteristica": "Peinado",
                    "color": "crudo",
                    "formato": "cajas",
                    "lote": "y144p",
                    "ubicacion": "deposito de descarga",
                    "proveedor": "T&N Platex",
                    "fecha_ingreso": "2025-08-09T15:29:06.544987",
                    "ultima_modificacion": "2025-08-09T15:43:43.641048",
                    "cantidad": 180,
                    "kilos_por_caja": 0.0,
                    "conos_por_caja": 0,
                    "descripcion_cono": ""
                },
                "Algodón_20/1_Peinado_crudo_6828_deposito_de_descarga": {
                    "tipo": "Algodón",
                    "titulo": "20/1", 
                    "caracteristica": "Peinado",
                    "color": "crudo",
                    "formato": "cajas",
                    "lote": "6828",
                    "ubicacion": "deposito de descarga",
                    "proveedor": "Tecotex",
                    "fecha_ingreso": "2025-08-09T16:17:40.101742",
                    "ultima_modificacion": "2025-08-09T16:17:40.101747",
                    "cantidad": 30,
                    "kilos_por_caja": 0.0,
                    "conos_por_caja": 0,
                    "descripcion_cono": ""
                }
            }
            if engine:
                # migrar_json_a_postgres(datos_por_defecto)  # Eliminado: no migrar datos preestablecidos
                pass
            else:
                # guardar_stock_json(datos_por_defecto)  # Eliminado: no migrar datos preestablecidos
                pass
            return datos_por_defecto
            
    except Exception as e:
        print(f"❌ Error al cargar stock JSON: {e}")
        return {}

def guardar_stock(stock_data):
    """Guardar datos del stock a PostgreSQL o JSON como fallback"""
    try:
        if engine:
            # Usar PostgreSQL con operaciones específicas
            with engine.connect() as conn:
                # Obtener productos existentes
                result = conn.execute(text("SELECT codigo FROM stock"))
                codigos_existentes = set(row.codigo for row in result)
                codigos_nuevos = set(stock_data.keys())
                
                # Eliminar productos que ya no están en stock_data
                codigos_a_eliminar = codigos_existentes - codigos_nuevos
                for codigo in codigos_a_eliminar:
                    conn.execute(text("DELETE FROM stock WHERE codigo = :codigo"), {'codigo': codigo})
                
                # Actualizar o insertar cada producto
                for codigo, item in stock_data.items():
                    if codigo in codigos_existentes:
                        # Actualizar producto existente
                        conn.execute(text("""
                            UPDATE stock SET 
                                tipo = :tipo, titulo = :titulo, caracteristica = :caracteristica,
                                color = :color, formato = :formato, lote = :lote,
                                ubicacion = :ubicacion, proveedor = :proveedor, cantidad = :cantidad,
                                kilos_por_caja = :kilos_por_caja, conos_por_caja = :conos_por_caja,
                                descripcion_cono = :descripcion_cono, ultima_modificacion = :ultima_modificacion
                            WHERE codigo = :codigo
                        """), {
                            'codigo': codigo,
                            'tipo': item.get('tipo'),
                            'titulo': item.get('titulo'),
                            'caracteristica': item.get('caracteristica'),
                            'color': item.get('color'),
                            'formato': item.get('formato'),
                            'lote': item.get('lote'),
                            'ubicacion': item.get('ubicacion'),
                            'proveedor': item.get('proveedor'),
                            'cantidad': item.get('cantidad', 0),
                            'kilos_por_caja': item.get('kilos_por_caja', 0.0),
                            'conos_por_caja': item.get('conos_por_caja', 0),
                            'descripcion_cono': item.get('descripcion_cono', ''),
                            'ultima_modificacion': datetime.now()
                        })
                    else:
                        # Insertar producto nuevo
                        conn.execute(text("""
                            INSERT INTO stock (codigo, tipo, titulo, caracteristica, color, formato, 
                                             lote, ubicacion, proveedor, cantidad, kilos_por_caja, 
                                             conos_por_caja, descripcion_cono, fecha_ingreso, ultima_modificacion)
                            VALUES (:codigo, :tipo, :titulo, :caracteristica, :color, :formato,
                                   :lote, :ubicacion, :proveedor, :cantidad, :kilos_por_caja,
                                   :conos_por_caja, :descripcion_cono, :fecha_ingreso, :ultima_modificacion)
                        """), {
                            'codigo': codigo,
                            'tipo': item.get('tipo'),
                            'titulo': item.get('titulo'),
                            'caracteristica': item.get('caracteristica'),
                            'color': item.get('color'),
                            'formato': item.get('formato'),
                            'lote': item.get('lote'),
                            'ubicacion': item.get('ubicacion'),
                            'proveedor': item.get('proveedor'),
                            'cantidad': item.get('cantidad', 0),
                            'kilos_por_caja': item.get('kilos_por_caja', 0.0),
                            'conos_por_caja': item.get('conos_por_caja', 0),
                            'descripcion_cono': item.get('descripcion_cono', ''),
                            'fecha_ingreso': datetime.fromisoformat(item['fecha_ingreso']) if item.get('fecha_ingreso') else datetime.now(),
                            'ultima_modificacion': datetime.now()
                        })
                
                conn.commit()
                print(f"✅ Stock guardado en PostgreSQL: {len(stock_data)} productos")
        else:
            # Fallback a JSON
            guardar_stock_json(stock_data)
            
    except Exception as e:
        print(f"❌ Error al guardar en PostgreSQL, usando JSON: {e}")
        guardar_stock_json(stock_data)

def guardar_stock_json(stock_data):
    """Guardar datos del stock a JSON (fallback)"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Stock guardado en JSON: {len(stock_data)} productos")
    except Exception as e:
        print(f"❌ Error guardando stock JSON: {e}")

def migrar_json_a_postgres(datos):
    """Migrar datos de JSON a PostgreSQL"""
    try:
        if engine:
            guardar_stock(datos)
            print(f"✅ Datos migrados a PostgreSQL: {len(datos)} productos")
    except Exception as e:
        print(f"❌ Error en migración: {e}")

def cargar_umbrales():
    """Cargar umbrales de stock desde JSON"""
    try:
        with open(UMBRALES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return UMBRALES_STOCK_BAJO_DEFAULT.copy()

def guardar_umbrales(umbrales_data):
    """Guardar umbrales de stock a JSON"""
    with open(UMBRALES_FILE, 'w', encoding='utf-8') as f:
        json.dump(umbrales_data, f, ensure_ascii=False, indent=2)

def cargar_movimientos():
    """Cargar historial de movimientos desde PostgreSQL o JSON como fallback"""
    try:
        if engine:
            # Usar PostgreSQL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM movimientos ORDER BY fecha DESC"))
                rows = result.fetchall()
                
                movimientos = []
                for row in rows:
                    movimientos.append({
                        'fecha': row.fecha.strftime('%Y-%m-%d %H:%M:%S') if row.fecha else '',
                        'tipo': row.tipo,
                        'codigo': row.codigo,
                        'descripcion': row.descripcion,
                        'cantidad': row.cantidad,
                        'ubicacion': row.ubicacion,
                        'usuario': row.usuario
                    })
                
                print(f"✅ Movimientos cargados desde PostgreSQL: {len(movimientos)}")
                return movimientos
        
        # Fallback a JSON (desarrollo local)
        return cargar_movimientos_json()
        
    except Exception as e:
        print(f"❌ Error al cargar movimientos desde PostgreSQL, usando JSON: {e}")
        return cargar_movimientos_json()

def cargar_movimientos_json():
    """Cargar historial de movimientos desde JSON"""
    try:
        with open(MOVIMIENTOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def guardar_movimiento(tipo, codigo, descripcion, cantidad, ubicacion, usuario="Sistema"):
    """Registrar un nuevo movimiento en el historial - PostgreSQL y JSON"""
    try:
        fecha_actual = datetime.now()
        
        # Guardar en PostgreSQL si está disponible
        if engine:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO movimientos (fecha, tipo, codigo, descripcion, cantidad, ubicacion, usuario)
                    VALUES (:fecha, :tipo, :codigo, :descripcion, :cantidad, :ubicacion, :usuario)
                """), {
                    'fecha': fecha_actual,
                    'tipo': tipo,
                    'codigo': codigo,
                    'descripcion': descripcion,
                    'cantidad': cantidad,
                    'ubicacion': ubicacion,
                    'usuario': usuario
                })
                conn.commit()
                print(f"✅ Movimiento guardado en PostgreSQL: {tipo} - {codigo}")
        
        # También guardar en JSON como backup (para desarrollo local)
        guardar_movimiento_json(tipo, codigo, descripcion, cantidad, ubicacion, usuario)
        
    except Exception as e:
        print(f"❌ Error guardando movimiento: {e}")
        # Fallback a JSON si falla PostgreSQL
        guardar_movimiento_json(tipo, codigo, descripcion, cantidad, ubicacion, usuario)

def guardar_movimiento_json(tipo, codigo, descripcion, cantidad, ubicacion, usuario="Sistema"):
    """Registrar un nuevo movimiento en el historial JSON"""
    try:
        movimientos = cargar_movimientos_json()
        
        nuevo_movimiento = {
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tipo': tipo,
            'codigo': codigo,
            'descripcion': descripcion,
            'cantidad': cantidad,
            'ubicacion': ubicacion,
            'usuario': usuario
        }
        
        # Agregar al inicio de la lista (más recientes primero)
        movimientos.insert(0, nuevo_movimiento)
        
        # Mantener solo los últimos 100 movimientos para no llenar el archivo
        if len(movimientos) > 100:
            movimientos = movimientos[:100]
        
        # Guardar al archivo
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MOVIMIENTOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(movimientos, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        print(f"Error guardando movimiento JSON: {e}")

def obtener_titulos(tipo_hilado):
    """Obtener títulos disponibles para un tipo de hilado"""
    hilado = CATALOGO_DE_HILOS.get(tipo_hilado)
    if hilado is None:
        return []
    if isinstance(hilado, dict):
        return list(hilado.keys())
    if isinstance(hilado, list):
        return hilado
    return []

def obtener_caracteristicas(tipo_hilado, titulo):
    """Obtener características disponibles para un hilo específico"""
    hilado = CATALOGO_DE_HILOS.get(tipo_hilado)
    if hilado is None:
        return []
    if tipo_hilado == "Melange":
        porcentajes = hilado.get(titulo, {}).get("Porcentaje", [])
        return porcentajes
    if isinstance(hilado, dict):
        return hilado.get(titulo, {}).get("caracteristica", [])
    return []

# =====================================
# RUTAS PRINCIPALES
# =====================================

@app.route('/')
def index():
    """Página principal con selector de módulos"""
    return render_template('selector_modulos.html')

# =====================================
# MÓDULO DEPÓSITO
# =====================================

@app.route('/deposito')
def deposito_dashboard():
    """Redirección al dashboard del depósito"""
    return redirect(url_for('deposito_dashboard_view'))

@app.route('/deposito/dashboard')
def deposito_dashboard_view():
    """Dashboard principal del depósito con estadísticas"""
    stock = cargar_stock()
    umbrales = cargar_umbrales()
    
    # Calcular estadísticas generales
    total_productos = len(stock)
    productos_criticos = 0
    valor_total_stock = 0
    productos_sin_stock = 0
    
    for codigo, item in stock.items():
        cantidad = item.get('cantidad', 0)
        if cantidad == 0:
            productos_sin_stock += 1
        
        # Obtener umbral según tipo de hilo y formato
        tipo_hilo = item.get('tipo', 'Algodón')
        formato = item.get('formato', 'cajas')
        umbral = umbrales.get(tipo_hilo, {}).get(formato, 0)
        
        if cantidad <= umbral:
            productos_criticos += 1
        
        # Calcular valor estimado
        if formato == "cajas":
            kilos_por_caja = item.get('kilos_por_caja', 0)
            valor_total_stock += cantidad * kilos_por_caja * 10  # Precio estimado por kg
        elif formato == "Palletizado":
            kilos_por_pallet = item.get('kilos_por_pallet', 0)
            valor_total_stock += cantidad * kilos_por_pallet * 10
        else:
            precio = item.get('precio_unitario', 0)
            valor_total_stock += cantidad * precio
    
    estadisticas = {
        'total_productos': total_productos,
        'productos_criticos': productos_criticos,
        'valor_total_stock': valor_total_stock,
        'productos_sin_stock': productos_sin_stock,
        'porcentaje_criticos': round((productos_criticos / total_productos * 100) if total_productos > 0 else 0, 1)
    }
    
    return render_template('deposito/dashboard_moderno.html', 
                         estadisticas=estadisticas, 
                         catalogo=CATALOGO_DE_HILOS,
                         colores=LISTA_DE_COLORES)

@app.route('/deposito/stock')
def deposito_stock():
    """Página principal de gestión de stock"""
    return render_template('deposito/stock_clean.html')

@app.route('/deposito/ingreso')
def deposito_ingreso():
    """Página de ingreso de productos"""
    return render_template('deposito/ingreso_moderno.html',
                         catalogo=CATALOGO_DE_HILOS,
                         colores=LISTA_DE_COLORES,
                         formatos=LISTA_DE_FORMATOS,
                         ubicaciones=LISTA_DE_UBICACIONES,
                         proveedores=LISTA_DE_PROVEEDORES,
                         parametros_carga=PARAMETROS_CARGA_DEFAULT)

@app.route('/deposito/reportes')
def deposito_reportes():
    """Página de reportes del depósito"""
    return render_template('deposito/reportes_moderno.html')

@app.route('/deposito/configuracion')
def deposito_configuracion():
    """Página de configuración del depósito"""
    umbrales = cargar_umbrales()
    return render_template('deposito/configuracion_moderno.html', 
                         umbrales=umbrales,
                         catalogo=CATALOGO_DE_HILOS,
                         umbrales_default=UMBRALES_STOCK_BAJO_DEFAULT)

# =====================================
# APIs DEL DASHBOARD
# =====================================

@app.route('/api/estadisticas')
def api_estadisticas():
    """API para obtener estadísticas del dashboard"""
    try:
        stock = cargar_stock()
        umbrales = cargar_umbrales()
        
        # Contadores iniciales
        total_productos = len(stock)
        total_kilos = 0
        productos_activos = 0
        ubicaciones = set()
        stock_critico = 0
        stock_bajo = 0
        stock_normal = 0
        stock_exceso = 0
        
        for codigo, item in stock.items():
            cantidad = item.get('cantidad', 0)
            ubicacion = item.get('ubicacion', '')
            tipo_hilo = item.get('tipo', 'Algodón')
            formato = item.get('formato', 'cajas')
            
            # Contar productos activos
            if cantidad > 0:
                productos_activos += 1
            
            # Agregar ubicaciones únicas
            if ubicacion:
                ubicaciones.add(ubicacion)
            
            # Calcular kilos totales
            if formato == "cajas":
                kilos_por_caja = item.get('kilos_por_caja', 0)
                if kilos_por_caja > 0:
                    total_kilos += cantidad * kilos_por_caja
                else:
                    total_kilos += cantidad * 25  # Estimación por defecto
            
            # Clasificar según umbrales
            umbral_bajo = umbrales.get(tipo_hilo, {}).get(formato, 10)
            umbral_critico = max(1, umbral_bajo // 2)
            umbral_exceso = umbral_bajo * 3
            
            if cantidad == 0 or cantidad <= umbral_critico:
                stock_critico += 1
            elif cantidad <= umbral_bajo:
                stock_bajo += 1
            elif cantidad >= umbral_exceso:
                stock_exceso += 1
            else:
                stock_normal += 1
        
        estadisticas = {
            'total_productos': total_productos,
            'total_kilos': round(total_kilos, 1),
            'productos_activos': productos_activos,
            'ubicaciones': len(ubicaciones),
            'stock_critico': stock_critico,
            'stock_bajo': stock_bajo,
            'stock_normal': stock_normal,
            'stock_exceso': stock_exceso
        }
        
        return jsonify(estadisticas)
        
    except Exception as e:
        print(f"Error en api_estadisticas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/graficos')
def api_graficos():
    """API para obtener datos de gráficos"""
    try:
        stock = cargar_stock()
        
        # Datos por tipo de hilado
        tipos_count = {}
        ubicaciones_count = {}
        
        for codigo, item in stock.items():
            tipo = item.get('tipo', 'Sin tipo')
            ubicacion = item.get('ubicacion', 'Sin ubicación')
            cantidad = item.get('cantidad', 0)
            
            tipos_count[tipo] = tipos_count.get(tipo, 0) + cantidad
            ubicaciones_count[ubicacion] = ubicaciones_count.get(ubicacion, 0) + cantidad
        
        # Preparar datos para Chart.js
        por_tipo = {
            'labels': list(tipos_count.keys()),
            'data': list(tipos_count.values())
        }
        
        por_ubicacion = {
            'labels': list(ubicaciones_count.keys()),
            'data': list(ubicaciones_count.values())
        }
        
        return jsonify({
            'por_tipo': por_tipo,
            'por_ubicacion': por_ubicacion
        })
        
    except Exception as e:
        print(f"Error en api_graficos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movimientos')
def api_movimientos():
    """API para obtener historial de movimientos de stock - DEPLOY v1.2"""
    try:
        movimientos = cargar_movimientos()
        
        # Si no hay movimientos, mostrar mensaje informativo
        if not movimientos:
            movimientos = [{
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tipo': 'INFO',
                'codigo': '-',
                'descripcion': 'No hay movimientos registrados aún. Los movimientos se registrarán automáticamente al agregar, editar o eliminar productos.',
                'cantidad': 0,
                'ubicacion': '-',
                'usuario': 'Sistema'
            }]
        
        # Aplicar límite si se especifica
        limit = request.args.get('limit', type=int)
        if limit and len(movimientos) > limit:
            movimientos = movimientos[:limit]
        
        return jsonify(movimientos)
        
    except Exception as e:
        print(f"Error en api_movimientos: {e}")
        return jsonify([]), 500

# =====================================
# APIs DE GESTIÓN DE STOCK
# =====================================

@app.route('/api/deposito/productos', methods=['GET'])
def api_deposito_obtener_productos():
    """API para obtener todos los productos del depósito"""
    print("🔍 API llamada - obteniendo productos...")
    stock = cargar_stock()
    print(f"📦 Stock cargado: {len(stock)} items")
    return jsonify(stock)

@app.route('/api/deposito/producto/<codigo>', methods=['GET'])
def api_deposito_obtener_producto(codigo):
    """API para obtener un producto específico"""
    stock = cargar_stock()
    if codigo in stock:
        return jsonify(stock[codigo])
    return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/api/deposito/producto/<codigo>', methods=['PUT'])
def api_deposito_actualizar_producto(codigo):
    """API para actualizar un producto específico"""
    try:
        data = request.get_json()
        stock = cargar_stock()
        
        if codigo not in stock:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        # Guardar valores anteriores para el log
        producto_anterior = stock[codigo].copy()
        cantidad_anterior = producto_anterior.get('cantidad', 0)
        
        # Actualizar campos proporcionados
        for key, value in data.items():
            if key in ['cantidad', 'precio_unitario']:
                stock[codigo][key] = float(value) if value is not None else stock[codigo].get(key, 0)
            else:
                stock[codigo][key] = value
        
        stock[codigo]['ultima_modificacion'] = datetime.now().isoformat()
        
        # Registrar movimiento si cambió la cantidad
        cantidad_nueva = stock[codigo].get('cantidad', 0)
        if cantidad_anterior != cantidad_nueva:
            diferencia = cantidad_nueva - cantidad_anterior
            descripcion = f"{producto_anterior.get('tipo', '')} {producto_anterior.get('titulo', '')} {producto_anterior.get('color', '')}".strip()
            tipo_movimiento = 'AJUSTE'
            
            guardar_movimiento(tipo_movimiento, codigo, f"Actualización de stock: {descripcion}", 
                             diferencia, producto_anterior.get('ubicacion', ''), 'Sistema')
        
        guardar_stock(stock)
        return jsonify({'success': True, 'message': 'Producto actualizado correctamente', 'producto': stock[codigo]})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/deposito/producto/<codigo>', methods=['DELETE'])
def api_deposito_eliminar_producto(codigo):
    """API para eliminar un producto específico"""
    try:
        stock = cargar_stock()
        
        if codigo not in stock:
            return jsonify({'error': 'Producto no encontrado'}), 404
        
        producto_eliminado = stock[codigo].copy()
        cantidad_eliminada = producto_eliminado.get('cantidad', 0)
        descripcion = f"{producto_eliminado.get('tipo', '')} {producto_eliminado.get('titulo', '')} {producto_eliminado.get('color', '')}".strip()
        
        # Registrar movimiento de eliminación
        guardar_movimiento('EGRESO', codigo, f"Eliminación de producto: {descripcion}", 
                         -cantidad_eliminada, producto_eliminado.get('ubicacion', ''), 'Sistema')
        
        del stock[codigo]
        guardar_stock(stock)
        
        print(f"🗑️ Producto eliminado: {codigo} - {descripcion}")
        
        return jsonify({'success': True, 'message': 'Producto eliminado correctamente'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/deposito/agregar-hilo', methods=['POST'])
def api_agregar_hilo():
    """API para agregar nuevo hilo al stock"""
    try:
        data = request.get_json()
        stock = cargar_stock()
        
        # Extraer datos del request
        tipo = data.get('tipo_hilado')
        titulo = data.get('titulo')
        caracteristica = data.get('caracteristica')
        color = data.get('color')
        lote = data.get('lote')
        formato = data.get('formato')
        ubicacion = data.get('ubicacion')
        proveedor = data.get('proveedor')
        
        if not all([tipo, titulo, caracteristica, color, lote, formato, ubicacion, proveedor]):
            return jsonify({'success': False, 'error': 'Complete todos los campos obligatorios'}), 400
        
        # Generar código único
        codigo = f"{tipo}_{titulo}_{caracteristica}_{color}_{lote}_{ubicacion}".replace(' ', '_').replace('&', 'y')
        
        # Crear item base
        item = {
            'tipo': tipo,
            'titulo': titulo,
            'caracteristica': caracteristica,
            'color': color,
            'formato': formato,
            'lote': lote,
            'ubicacion': ubicacion,
            'proveedor': proveedor,
            'fecha_ingreso': datetime.now().isoformat(),
            'ultima_modificacion': datetime.now().isoformat()
        }
        
        # Agregar campos específicos según formato
        if formato == "cajas":
            item.update({
                'cantidad': int(data.get('cantidad_cajas', 0)),
                'kilos_por_caja': float(data.get('kilos_por_caja', 0)),
                'conos_por_caja': int(data.get('conos_por_caja', 0)),
                'descripcion_cono': data.get('descripcion_cono', '')
            })
        elif formato == "Palletizado":
            item.update({
                'cantidad': int(data.get('cantidad_pallets', 0)),
                'kilos_por_pallet': float(data.get('kilos_por_pallet', 0)),
                'conos_por_pallet': int(data.get('conos_por_pallet', 0)),
                'descripcion_cono': data.get('descripcion_cono', '')
            })
        
        # Verificar si ya existe y sumar cantidades
        descripcion_movimiento = f"{tipo} {titulo} {caracteristica} {color}"
        cantidad_movimiento = item['cantidad']
        
        if codigo in stock:
            cantidad_anterior = stock[codigo]['cantidad']
            stock[codigo]['cantidad'] += item['cantidad']
            stock[codigo]['ultima_modificacion'] = datetime.now().isoformat()
            
            # Registrar movimiento de suma
            guardar_movimiento('AJUSTE', codigo, f"Suma a stock existente: {descripcion_movimiento}", 
                             cantidad_movimiento, ubicacion, 'Sistema')
        else:
            stock[codigo] = item
            
            # Registrar movimiento de ingreso nuevo
            guardar_movimiento('INGRESO', codigo, f"Nuevo ingreso: {descripcion_movimiento}", 
                             cantidad_movimiento, ubicacion, 'Sistema')
        
        guardar_stock(stock)
        return jsonify({'success': True, 'message': 'Hilo agregado correctamente', 'codigo': codigo})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# =====================================
# APIs DE REPORTES
# =====================================

@app.route('/api/reporte/stock-general')
def api_reporte_stock_general():
    """API para generar reporte general de stock"""
    try:
        stock = cargar_stock()
        umbrales = cargar_umbrales()
        
        reporte = []
        total_productos = 0
        total_cajas = 0
        productos_criticos = 0
        
        for codigo, item in stock.items():
            cantidad = item.get('cantidad', 0)
            tipo_hilo = item.get('tipo', 'Algodón')
            formato = item.get('formato', 'cajas')
            
            # Obtener umbrales
            umbral_bajo = umbrales.get(tipo_hilo, {}).get(formato, 10)
            umbral_critico = max(1, umbral_bajo // 2)
            
            # Determinar estado
            if cantidad <= umbral_critico:
                estado = 'Crítico'
                estado_color = 'danger'
                productos_criticos += 1
            elif cantidad <= umbral_bajo:
                estado = 'Bajo'
                estado_color = 'warning'
            else:
                estado = 'Normal'
                estado_color = 'success'
            
            # Calcular días en stock
            fecha_ingreso = item.get('fecha_ingreso', '')
            dias_stock = 0
            if fecha_ingreso:
                try:
                    fecha_ing = datetime.fromisoformat(fecha_ingreso.replace('Z', '+00:00'))
                    dias_stock = (datetime.now() - fecha_ing).days
                except:
                    dias_stock = 0
            
            producto_reporte = {
                'codigo': codigo,
                'tipo': item.get('tipo', ''),
                'titulo': item.get('titulo', ''),
                'caracteristica': item.get('caracteristica', ''),
                'color': item.get('color', ''),
                'cantidad': cantidad,
                'formato': formato,
                'ubicacion': item.get('ubicacion', ''),
                'proveedor': item.get('proveedor', ''),
                'lote': item.get('lote', ''),
                'fecha_ingreso': item.get('fecha_ingreso', ''),
                'dias_stock': dias_stock,
                'estado': estado,
                'estado_color': estado_color,
                'umbral_bajo': umbral_bajo,
                'umbral_critico': umbral_critico
            }
            
            reporte.append(producto_reporte)
            total_productos += 1
            total_cajas += cantidad
        
        # Ordenar por estado crítico primero
        reporte.sort(key=lambda x: (x['estado'] != 'Crítico', x['estado'] != 'Bajo', x['tipo'], x['titulo']))
        
        resumen = {
            'total_productos': total_productos,
            'total_cajas': total_cajas,
            'productos_criticos': productos_criticos,
            'fecha_reporte': datetime.now().isoformat(),
            'productos': reporte
        }
        
        return jsonify(resumen)
        
    except Exception as e:
        print(f"Error en api_reporte_stock_general: {e}")
        return jsonify({'error': str(e)}), 500

# =====================================
# APIs DE DATOS AUXILIARES
# =====================================

@app.route('/api/catalogo')
def api_catalogo():
    """API para obtener el catálogo completo de hilos"""
    return jsonify(CATALOGO_DE_HILOS)

@app.route('/api/tipos-hilo')
def api_tipos_hilo():
    """API para obtener los tipos de hilo disponibles"""
    return jsonify(list(CATALOGO_DE_HILOS.keys()))

@app.route('/api/titulos/<tipo_hilo>')
def api_titulos_hilo(tipo_hilo):
    """API para obtener títulos de un tipo de hilo específico"""
    titulos = obtener_titulos(tipo_hilo)
    return jsonify(titulos)

@app.route('/api/caracteristicas/<tipo_hilo>/<titulo>')
def api_caracteristicas_hilo(tipo_hilo, titulo):
    """API para obtener características de un hilo específico"""
    caracteristicas = obtener_caracteristicas(tipo_hilo, titulo)
    return jsonify(caracteristicas)

@app.route('/api/colores')
def api_colores():
    """API para obtener la lista de colores disponibles"""
    return jsonify(LISTA_DE_COLORES)

@app.route('/api/proveedores')
def api_proveedores():
    """API para obtener lista de proveedores"""
    return jsonify(LISTA_DE_PROVEEDORES)

@app.route('/api/umbrales', methods=['GET', 'POST'])
def api_umbrales():
    """API para gestionar umbrales de stock"""
    if request.method == 'GET':
        umbrales = cargar_umbrales()
        return jsonify(umbrales)
    else:
        try:
            data = request.get_json()
            guardar_umbrales(data)
            return jsonify({'success': True, 'message': 'Umbrales actualizados correctamente'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

# =====================================
# MÓDULOS ADICIONALES (PRÓXIMAMENTE)
# =====================================

@app.route('/tejeduria')
def tejeduria_dashboard():
    """Dashboard del módulo tejeduría"""
    return render_template('en_desarrollo.html', 
                         modulo_nombre="Tejeduría",
                         modulo_descripcion="Control de producción y calidad de tejidos")

@app.route('/mecanica')
def mecanica_dashboard():
    """Dashboard del módulo mecánica"""
    return render_template('en_desarrollo.html',
                         modulo_nombre="Mecánica",
                         modulo_descripcion="Mantenimiento y gestión de maquinaria")

@app.route('/gerencia')
def gerencia_dashboard():
    """Dashboard del módulo gerencia"""
    return render_template('en_desarrollo.html',
                         modulo_nombre="Gerencia",
                         modulo_descripcion="Reportes ejecutivos y análisis de negocio")

# =====================================
# MANEJO DE ERRORES
# =====================================

@app.errorhandler(404)
def page_not_found(e):
    """Manejo de páginas no encontradas"""
    return f"<h1>Página no encontrada</h1><p>La URL solicitada no existe.</p><a href='/'>Volver al inicio</a>", 404

@app.errorhandler(500)
def internal_server_error(e):
    """Manejo de errores internos del servidor"""
    return f"<h1>Error interno del servidor</h1><p>Ha ocurrido un error interno.</p><a href='/'>Volver al inicio</a>", 500

# =====================================
# RUTA DE DEBUG
# =====================================

@app.route('/debug/env')
def debug_env():
    """Devuelve información de la variable de entorno"""
    try:
        return jsonify({
            'DATABASE_URL_exists': bool(DATABASE_URL),
            'DATABASE_URL_length': len(DATABASE_URL) if DATABASE_URL else 0,
            'DATABASE_URL_starts_with': DATABASE_URL[:30] if DATABASE_URL else 'None',
            'engine_exists': engine is not None
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/stock')
def debug_stock():
    """Devuelve todos los productos actuales en la base de datos PostgreSQL (solo lectura)"""
    try:
        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM stock"))
                productos = [dict(row) for row in result]
                return jsonify(productos)
        else:
            return jsonify({'error': 'No hay conexión a PostgreSQL'})
    except Exception as e:
        return jsonify({'error': str(e)})

# =====================================
# INICIALIZACIÓN DE LA APLICACIÓN
# =====================================

# Ejecutar inicialización automática para Gunicorn
try:
    print("🚀 [GUNICORN] Iniciando inicialización segura...")
    safe_init()
    print("✅ [GUNICORN] Inicialización completada")
except Exception as e:
    print(f"⚠️ [GUNICORN] Error en inicialización (app continúa): {e}")
    import traceback
    traceback.print_exc()

if __name__ == '__main__':
    try:
        print("🚀 Sistema Alvear - Iniciando servidor...")
        
        # Inicializar base de datos PostgreSQL (no crítico)
        try:
            init_database()
            print("✅ Base de datos inicializada")
        except Exception as e:
            print(f"⚠️ Error en DB (continuando): {e}")
        
        # Verificar archivos (no crítico)
        try:
            verificar_archivos_datos()
            print("✅ Archivos de datos verificados")
        except Exception as e:
            print(f"⚠️ Error en archivos (continuando): {e}")
        
        # Configuración para desarrollo vs producción
        debug_mode = os.environ.get('FLASK_ENV') != 'production'
        port = int(os.environ.get('PORT', 5000))
        
        if debug_mode:
            print("🔧 Modo desarrollo - http://localhost:5000")
        else:
            print(f"🌐 Modo producción - Puerto {port}")
            
        print("🎯 INICIANDO SERVIDOR...")
        app.run(debug=debug_mode, host='0.0.0.0', port=port)
            
    except Exception as e:
        print(f"❌ Error CRÍTICO al iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        # Intentar iniciar en modo básico
        print("🆘 Intentando modo de emergencia...")
        app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))