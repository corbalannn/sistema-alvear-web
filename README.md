# Sistema de Gestión Textil Alvear

Sistema modular web para la gestión integral de inventario textil, desarrollado en Flask con interfaz moderna Bootstrap 5.

## 🚀 Características

### Módulo Depósito (Operativo)
- **Dashboard ejecutivo** con estadísticas en tiempo real
- **Gestión de stock** con sistema de tarjetas por proveedor
- **Sistema de reportes** con filtros y exportación
- **Control de umbrales** de stock crítico personalizable
- **Ingreso de productos** con validaciones automáticas

### Módulos en Desarrollo
- **Tejeduría**: Control de producción y calidad
- **Mecánica**: Mantenimiento de maquinaria
- **Gerencia**: Reportes ejecutivos y análisis

## 🛠️ Tecnologías

- **Backend**: Python 3.8+ con Flask
- **Frontend**: Bootstrap 5 + Bootstrap Icons
- **Gráficos**: Chart.js para visualizaciones
- **Base de datos**: JSON (migración a PostgreSQL planificada)
- **Despliegue**: Compatible con Render, Railway, Heroku

## 📋 Instalación

### Requisitos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación Local

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd sistema_alvear_web
```

2. **Crear entorno virtual**
```bash
python -m venv venv
```

3. **Activar entorno virtual**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Ejecutar la aplicación**
```bash
python app_modular.py
```

6. **Abrir en navegador**
```
http://localhost:5000
```

## 🔧 Configuración

### Variables de Entorno
- `FLASK_ENV`: `development` o `production`
- `PORT`: Puerto del servidor (por defecto 5000)

### Archivos de Datos
Los datos se almacenan en la carpeta `data/`:
- `stock.json`: Inventario de productos
- `umbrales_config.json`: Configuración de alertas de stock

## 📊 Estructura del Proyecto

```
sistema_alvear_web/
├── app_modular.py          # Aplicación principal
├── requirements.txt        # Dependencias Python
├── Procfile               # Configuración para Heroku/Render
├── data/                  # Datos de la aplicación
│   ├── stock.json
│   └── umbrales_config.json
├── static/                # Archivos estáticos
│   └── css/
├── templates/             # Plantillas HTML
│   ├── base_moderno.html
│   ├── selector_modulos.html
│   └── deposito/
└── README.md
```

## 🌐 Despliegue en Producción

### Render (Recomendado)

1. Conectar repositorio de GitHub
2. Configurar como Web Service
3. Usar `python app_modular.py` como comando de inicio
4. La aplicación estará disponible en la URL proporcionada

### Railway

1. Conectar repositorio
2. El `Procfile` configura automáticamente el despliegue
3. Variables de entorno se configuran desde el dashboard

## 📈 Uso del Sistema

### Acceso al Sistema
1. **Página principal**: Selector de módulos estilo Office 365
2. **Módulo Depósito**: Gestión completa de inventario
3. **Dashboard**: Estadísticas y gráficos en tiempo real

### Gestión de Stock
- **Visualización por tarjetas** organizadas por proveedor
- **Filtros dinámicos** por tipo, ubicación, estado
- **Acciones rápidas**: editar, eliminar, ajustar cantidad
- **Alertas automáticas** de stock crítico

### Sistema de Reportes
- **Reporte general** con todos los productos
- **Filtros avanzados** por tipo, estado, proveedor
- **Exportación** (en desarrollo)
- **Impresión optimizada**

## 🔐 Configuración de Umbrales

Los umbrales de stock se configuran por:
- **Tipo de hilado** (Algodón, Snow, Spun, etc.)
- **Formato** (cajas, Palletizado)
- **Niveles personalizables** para cada combinación

## 📞 Soporte

Sistema desarrollado para Alvear Textil.
Para soporte técnico, contactar al administrador del sistema.

## 📄 Licencia

Sistema propietario - Uso exclusivo Alvear Textil

---

**Versión**: 1.0  
**Última actualización**: Agosto 2025  
**Estado**: MVP Operativo - Módulo Depósito
