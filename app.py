# -*- coding: utf-8 -*-
"""
Dashboard Fundación AIP - Versión Completa y Corregida
"""

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, callback_context, ALL
import geopandas as gpd
from datetime import datetime
import json
import dash
import os
from dash.exceptions import PreventUpdate
from shapely.geometry import Polygon
import base64
import io

# Solución para el error de PIL
try:
    from PIL import Image
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

os.environ['USE_PYGEOS'] = '0'

# Configuración inicial
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True)
server = app.server

# Función para codificar imágenes con transparencia
def encode_image(image_path, mobile=False):
    """Codifica imágenes optimizadas para móviles manteniendo transparencia"""
    try:
        if os.path.exists(image_path):
            with Image.open(image_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                transparent_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
                transparent_img.paste(img, (0, 0), img)
                
                if mobile:
                    transparent_img.thumbnail((400, 400))
                
                buffered = io.BytesIO()
                transparent_img.save(buffered, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
    except Exception as e:
        print(f"Error procesando imagen: {e}")
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    return None

# Carga de datos con manejo de errores
try:
    # Cargar shapefiles
    shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
    municipios_gdf = gpd.read_file(shapefile_path)
    
    aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
    aip_locations_gdf = gpd.read_file(aip_locations_path)

    # Codificar imágenes con transparencia
    logo_path = "assets/logo.png"
    huella_path = "assets/Figura_huella_aip.png"
    logo_encoded = encode_image(logo_path, mobile=True)
    huella_encoded = encode_image(huella_path, mobile=True)

    # Procesamiento de datos geoespaciales
    if municipios_gdf.crs != "EPSG:4326":
        municipios_gdf = municipios_gdf.to_crs("EPSG:4326")
    if aip_locations_gdf.crs != "EPSG:4326":
        aip_locations_gdf = aip_locations_gdf.to_crs("EPSG:4326")

    municipios_gdf_projected = municipios_gdf.to_crs("EPSG:3116")
    municipios_gdf_projected['centroid'] = municipios_gdf_projected.geometry.centroid
    municipios_gdf['lon'] = municipios_gdf_projected.centroid.map(lambda p: p.x)
    municipios_gdf['lat'] = municipios_gdf_projected.centroid.map(lambda p: p.y)

    # Cargar datos de proyectos
    def cargar_base_datos():
        df = pd.read_excel("data/proyectos.xlsx")
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
        df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
        
        # Normalización de nombres para asegurar coincidencia exacta
        df['Municipio'] = df['Municipio'].str.strip().str.upper()
        df['Departamento'] = df['Departamento'].str.strip().str.upper()
        
        return df

    df = cargar_base_datos()

    # Procesar nombres en el shapefile para coincidencia exacta
    municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].str.strip().str.upper()
    municipios_gdf['Depto'] = municipios_gdf['Depto'].str.strip().str.upper()

    # Verificación de coincidencias
    municipios_en_shapefile = set(zip(municipios_gdf['MpNombre'], municipios_gdf['Depto']))
    municipios_en_proyectos = set(zip(df['Municipio'], df['Departamento']))
    
    # Identificar municipios sin coincidencia
    no_encontrados = municipios_en_proyectos - municipios_en_shapefile
    if no_encontrados:
        print(f"Advertencia: {len(no_encontrados)} municipios no encontrados en shapefile:")
        for mun, depto in sorted(no_encontrados):
            print(f" - {mun} ({depto})")

except Exception as e:
    print(f"Error cargando datos: {e}")
    # Datos de ejemplo para evitar errores
    df = pd.DataFrame({
        'Municipio': ['EJEMPLO'],
        'Departamento': ['EJEMPLO'],
        'Tipo de proyecto': ['Ejemplo'],
        'Fecha inicio': [datetime.now()],
        'Fecha fin': [datetime.now()],
        'Costo total ($COP)': [0],
        'Beneficiarios directos': [0],
        'Beneficiarios indirectos': [0],
        'Beneficiarios totales': [0],
        'Área intervenida (ha)': [0],
        'Entidad financiadora': ['Ejemplo'],
        'Duración del proyecto (meses)': [0],
        'Producto principal generado': ['Ejemplo'],
        'Comunidad beneficiaria': ['Ejemplo'],
        'ID': [0]
    })
    logo_encoded = None
    huella_encoded = None

# Esquema de colores
colors = {
    'background': '#e8f5e9',
    'text': '#333333',
    'primary': '#2e5d2e',
    'secondary': '#4a7c4a',
    'accent': '#8b5a2b',
    'panel-general': 'rgba(72, 139, 72, 0.8)',
    'panel-especifico': 'rgba(102, 187, 106, 0.8)',
    'panel-municipios': 'rgba(139, 90, 43, 0.8)',
    'title-color': '#2e7d32',
    'value-color': '#333333',
    'text-color': '#333333',
    'card-border': '#a5d6a7',
    'hover-color': '#81c784',
    'selected-color': '#8B0000',
    'border-color': '#a5d6a7',
    'filter-bg': 'rgba(233, 245, 233, 0.9)',
    'slider-track': '#81c784',
    'slider-handle': '#8b5a2b',
    'verde-amarillento': '#CDDC39',
    'verde-amarillento-oscuro': '#AFB42B',
    'panel-azul-1': 'rgba(79, 195, 247, 0.8)',
    'panel-azul-2': 'rgba(129, 212, 250, 0.8)',
    'panel-azul-3': 'rgba(179, 229, 252, 0.8)',
    'panel-azul-4': 'rgba(207, 239, 253, 0.8)',
    'panel-verde-cana-1': 'rgba(100, 120, 60, 0.8)',
    'panel-verde-cana-2': 'rgba(120, 140, 80, 0.8)',
    'panel-verde-cana-3': 'rgba(140, 160, 95, 0.8)',
    'panel-verde-cana-4': 'rgba(160, 180, 110, 0.8)',
    'panel-verde-cana-5': 'rgba(180, 200, 130, 0.8)',
    'panel-verde-cana-6': 'rgba(200, 220, 160, 0.8)',
    'card-bg': 'rgba(255, 255, 255, 0.9)',
    'selected-card-bg': '#8B0000',
    'map-highlight': '#8B0000',
    'positive-accent': '#4caf50',
    'negative-accent': '#8b5a2b',
    'photo-panel': 'rgba(233, 245, 233, 0.9)',
    'modal-bg': 'rgba(0,0,0,0.85)',
    'aip-locations': '#FFA500',
    'map-title-bg': 'rgba(46, 125, 50, 0.85)'
}

# Estilos responsivos mejorados
styles = {
    'container': {
        'display': 'grid',
        'gridTemplateColumns': '1fr',
        'gap': '15px',
        'width': '100%',
        'maxWidth': '100%',
        'margin': '0 auto',
        'padding': '10px',
        'fontFamily': '"Segoe UI", "Open Sans", sans-serif',
        'backgroundColor': colors['background'],
        'overflowX': 'hidden',
        'boxSizing': 'border-box'
    },
    'responsive-grid': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(300px, 1fr))',
        'gap': '15px',
        'width': '100%'
    },
    'header': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'marginBottom': '0',
        'fontWeight': '700',
        'fontSize': 'clamp(22px, 4vw, 28px)',
        'paddingBottom': '10px',
        'textShadow': '2px 2px 4px rgba(0,0,0,0.5)',
        'borderBottom': f'2px solid {colors["title-color"]}',
        'display': 'inline-block',
        'verticalAlign': 'middle',
        'width': '100%'
    },
    'header-container': {
        'display': 'flex',
        'flexDirection': 'column',
        'gap': '15px',
        'alignItems': 'center',
        'marginBottom': '20px',
        'width': '100%'
    },
    'logo-container': {
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
        'paddingRight': '0',
        'width': '100%',
        'maxWidth': '100%'
    },
    'logo': {
        'height': '120px',
        'maxHeight': '20vw',
        'margin': '10px',
        'objectFit': 'contain',
        'maxWidth': '100%',
        'background': 'transparent',
    },
    'huella-img': {
        'height': '80px',
        'maxHeight': '15vw',
        'verticalAlign': 'middle',
        'marginLeft': '10px',
        'marginBottom': '5px',
        'background': 'transparent',
    },
    'section-title': {
        'textAlign': 'left',
        'color': colors['title-color'],
        'margin': '10px 0',
        'fontWeight': '600',
        'fontSize': 'clamp(18px, 3.5vw, 20px)',
        'paddingLeft': '10px',
        'borderLeft': f'4px solid {colors["title-color"]}',
        'backgroundColor': 'rgba(0,0,0,0.2)',
        'padding': '6px 8px',
        'borderRadius': '4px',
        'width': '100%'
    },
    'filters': {
        'backgroundColor': colors['filter-bg'],
        'padding': '15px',
        'borderRadius': '12px',
        'marginBottom': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}',
        'width': '100%'
    },
    'map-container': {
        'position': 'relative',
        'height': '400px',
        'minHeight': '300px',
        'width': '100%',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'border': f'1px solid {colors["border-color"]}',
        'marginBottom': '15px',
        'overflow': 'hidden'
    },
    'municipios-list': {
        'height': '400px',
        'overflowY': 'auto',
        'padding': '10px',
        'backgroundColor': colors['panel-municipios'],
        'borderRadius': '12px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["panel-municipios"]}',
        'width': '100%',
        '-webkitOverflowScrolling': 'touch'
    },
    'municipio-card': {
        'padding': '10px',
        'marginBottom': '10px',
        'borderRadius': '8px',
        'backgroundColor': colors['card-bg'],
        'cursor': 'pointer',
        'transition': 'all 0.3s ease',
        'border': f'1px solid {colors["panel-municipios"]}',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.15)',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minWidth': '0',
        'wordWrap': 'break-word',
        'width': '100%',
        'overflow': 'hidden'
    },
    'municipio-card-selected': {
        'padding': '10px',
        'marginBottom': '10px',
        'borderRadius': '8px',
        'backgroundColor': colors['selected-card-bg'],
        'color': 'white',
        'cursor': 'pointer',
        'border': '3px solid white',
        'boxShadow': '0 4px 8px rgba(255, 0, 0, 0.6)',
        'transform': 'scale(1.02)',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'minWidth': '0',
        'wordWrap': 'break-word',
        'width': '100%',
        'overflow': 'hidden'
    },
    'municipio-name': {
        'fontWeight': '600',
        'fontSize': 'clamp(14px, 3vw, 18px)',
        'marginBottom': '6px',
        'textAlign': 'center',
        'color': '#333333',
        'width': '100%',
        'textOverflow': 'ellipsis',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'municipio-name-selected': {
        'fontWeight': '600',
        'fontSize': 'clamp(16px, 3.5vw, 20px)',
        'marginBottom': '6px',
        'textAlign': 'center',
        'color': 'white',
        'width': '100%',
        'textShadow': '1px 1px 3px rgba(0,0,0,0.7)',
        'textOverflow': 'ellipsis',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'municipio-projects': {
        'fontSize': 'clamp(14px, 2.5vw, 16px)',
        'fontWeight': '600',
        'textAlign': 'center',
        'backgroundColor': '#e6f3ff',
        'color': colors['panel-municipios'],
        'padding': '4px 8px',
        'borderRadius': '12px',
        'minWidth': '60px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.15)',
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    'municipio-projects-selected': {
        'fontSize': 'clamp(14px, 2.5vw, 16px)',
        'fontWeight': '600',
        'textAlign': 'center',
        'backgroundColor': 'rgba(255,255,255,0.3)',
        'color': 'white',
        'padding': '4px 8px',
        'borderRadius': '12px',
        'minWidth': '60px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.3)',
        'border': '2px solid white',
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    'municipios-title': {
        'textAlign': 'center',
        'color': 'white',
        'fontWeight': '600',
        'fontSize': 'clamp(16px, 3vw, 20px)',
        'marginBottom': '15px',
        'padding': '8px',
        'borderRadius': '6px',
        'backgroundColor': 'rgba(0,0,0,0.3)',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.15)',
        'textTransform': 'uppercase',
        'letterSpacing': '1px',
        'borderBottom': f'2px solid {colors["title-color"]}',
        'position': 'sticky',
        'top': '0',
        'zIndex': '1'
    },
    'info-panel': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
        'gap': '10px',
        'marginTop': '15px',
        'backgroundColor': colors['filter-bg'],
        'padding': '10px',
        'borderRadius': '12px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}',
        'width': '100%'
    },
    'info-section-specific': {
        'padding': '15px',
        'borderRadius': '8px',
        'height': '100%',
        'border': f'2px solid {colors["selected-color"]}',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'transition': 'all 0.3s ease',
        'minHeight': '100px',
        'width': '100%',
        'overflow': 'hidden'
    },
    'info-title': {
        'fontSize': 'clamp(14px, 2.5vw, 16px)',
        'fontWeight': '600',
        'color': colors['title-color'],
        'marginBottom': '8px',
        'paddingBottom': '6px',
        'borderBottom': f'2px solid {colors["title-color"]}',
        'textAlign': 'center',
        'textTransform': 'uppercase',
        'letterSpacing': '0.5px',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.5)',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'info-value': {
        'fontSize': 'clamp(18px, 4vw, 24px)',
        'fontWeight': '600',
        'color': colors['value-color'],
        'margin': 'auto 0',
        'textAlign': 'center',
        'flexGrow': '1',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'textShadow': '1px 1px 3px rgba(0,0,0,0.5)',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'info-text': {
        'fontSize': 'clamp(16px, 3.5vw, 20px)',
        'fontWeight': '600',
        'color': colors['value-color'],
        'margin': 'auto 0',
        'textAlign': 'center',
        'flexGrow': '1',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'lineHeight': '1.4',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.3)',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'filter-label': {
        'fontWeight': '600',
        'marginBottom': '8px',
        'color': colors['title-color'],
        'fontSize': 'clamp(14px, 3vw, 16px)',
        'textShadow': '1px 1px 1px rgba(0,0,0,0.3)',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'dropdown': {
        'width': '100%',
        'maxWidth': '100%',
        'borderRadius': '6px',
        'border': f'1px solid {colors["border-color"]}',
        'fontSize': 'clamp(14px, 2.5vw, 16px)',
        'backgroundColor': 'white',
        'color': '#333333',
    },
    'summary': {
        'backgroundColor': colors['filter-bg'],
        'padding': '10px',
        'borderRadius': '12px',
        'marginBottom': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}',
        'width': '100%'
    },
    'card': {
        'backgroundColor': colors['panel-general'],
        'borderRadius': '12px',
        'padding': '15px',
        'marginBottom': '0px',
        'height': '100%',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'textAlign': 'center',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'border': f'2px solid {colors["selected-color"]}',
        'width': '100%',
        'overflow': 'hidden'
    },
    'kpi-title': {
        'fontSize': 'clamp(16px, 3vw, 18px)',
        'marginBottom': '8px',
        'color': colors['title-color'],
        'fontWeight': '600',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.3)',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'kpi-value': {
        'fontSize': 'clamp(24px, 5vw, 32px)',
        'fontWeight': '700',
        'color': colors['value-color'],
        'marginTop': '8px',
        'textShadow': '1px 1px 3px rgba(0,0,0,0.5)',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'photo-panel': {
        'display': 'grid',
        'gridTemplateColumns': '1fr',
        'gap': '15px',
        'backgroundColor': colors['photo-panel'],
        'padding': '15px',
        'borderRadius': '12px',
        'marginTop': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}',
        'width': '100%'
    },
    'photo-selector-container': {
        'backgroundColor': colors['panel-especifico'],
        'padding': '15px',
        'borderRadius': '8px',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'marginBottom': '15px',
        'width': '100%'
    },
    'photo-content': {
        'display': 'flex',
        'flexDirection': 'column',
        'gap': '12px',
        'width': '100%'
    },
    'photo-title': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'fontWeight': '600',
        'fontSize': 'clamp(16px, 3vw, 20px)',
        'marginBottom': '8px',
        'textTransform': 'uppercase',
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'wordBreak': 'break-word'
    },
    'photo-dropdown': {
        'width': '100%',
        'padding': '8px',
        'borderRadius': '6px',
        'backgroundColor': colors['filter-bg'],
        'color': colors['text'],
        'fontSize': 'clamp(14px, 2.5vw, 16px)',
        'border': f'1px solid {colors["border-color"]}',
    },
    'photo-button-container': {
        'display': 'flex',
        'flexDirection': 'row',
        'gap': '10px',
        'justifyContent': 'center',
        'alignItems': 'center',
        'flexWrap': 'wrap',
        'width': '100%'
    },
    'photo-button': {
        'padding': '8px 12px',
        'borderRadius': '6px',
        'backgroundColor': colors['accent'],
        'color': colors['background'],
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': 'clamp(14px, 2.5vw, 16px)',
        'margin': '4px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.15)',
        'transition': 'all 0.3s ease',
        'minWidth': '120px',
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    'modal': {
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'width': '100%',
        'height': '100%',
        'backgroundColor': colors['modal-bg'],
        'zIndex': '1000',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center',
    },
    'modal-content': {
        'backgroundColor': colors['background'],
        'padding': '15px',
        'borderRadius': '8px',
        'maxWidth': '95%',
        'maxHeight': '95%',
        'overflow': 'auto',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.4)',
        'border': f'2px solid {colors["title-color"]}',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
    },
    'modal-image': {
        'maxWidth': '100%',
        'maxHeight': '80vh',
        'borderRadius': '6px',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.25)',
        'marginBottom': '15px',
    },
    'close-button': {
        'padding': '8px 16px',
        'borderRadius': '6px',
        'backgroundColor': colors['accent'],
        'color': colors['background'],
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '16px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.15)',
    },
    'year-slider-container': {
        'marginTop': '15px',
        'paddingBottom': '30px',
        'overflow': 'hidden',
        'width': '100%'
    },
    'year-slider-tooltip': {
        'fontSize': '14px',
        'color': colors['text'],
        'backgroundColor': colors['filter-bg'],
        'whiteSpace': 'nowrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': '100px',
        'transform': 'translateY(20px)'
    }
}

# Layout de la aplicación mejorado
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'minHeight': '100vh',
    'padding': '10px',
    'margin': '0',
    'overflowX': 'hidden',
    'width': '100%',
    'boxSizing': 'border-box'
}, children=[
    html.Meta(name="viewport", content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"),
    
    html.Div(style=styles['container'], children=[
        # Encabezado
        html.Div(style=styles['header-container'], children=[
            html.Div(
                html.Div([
                    html.Span("NUESTRA HUELLA EN COLOMBIA ", style=styles['header']),
                    html.Img(
                        src=huella_encoded,
                        style=styles['huella-img']
                    ) if huella_encoded else html.Div()
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'flexWrap': 'wrap',
                    'justifyContent': 'center',
                    'width': '100%'
                }),
            ),
            html.Div(style=styles['logo-container'], children=[
                html.Img(
                    src=logo_encoded,
                    style=styles['logo']
                ) if logo_encoded else html.Div("Logo no encontrado")
            ])
        ]),
        
        # Filtros
        html.Div(style=styles['filters'], children=[
            html.Div(style={
                'display': 'grid',
                'gridTemplateColumns': '1fr',
                'gap': '15px',
                'width': '100%'
            }, children=[
                html.Div([
                    html.Label("TIPO DE PROYECTO", style=styles['filter-label']),
                    dcc.Dropdown(
                        id='tipo-dropdown',
                        options=[{'label': t, 'value': t} for t in sorted(df['Tipo de proyecto'].unique())],
                        multi=True,
                        placeholder="Seleccione tipos...",
                        style=styles['dropdown']
                    )
                ]),
                html.Div([
                    html.Label("DEPARTAMENTO", style=styles['filter-label']),
                    dcc.Dropdown(
                        id='departamento-dropdown',
                        options=[{'label': d, 'value': d} for d in sorted(df['Departamento'].unique())],
                        multi=True,
                        placeholder="Seleccione departamentos...",
                        style=styles['dropdown']
                    )
                ]),
                html.Div([
                    html.Label("COMUNIDAD BENEFICIARIA", style=styles['filter-label']),
                    dcc.Dropdown(
                        id='comunidad-dropdown',
                        options=[{'label': c, 'value': c} for c in sorted(df['Comunidad beneficiaria'].unique())],
                        multi=True,
                        placeholder="Seleccione comunidades...",
                        style=styles['dropdown']
                    )
                ]),
                html.Div([
                    html.Label("RANGO DE COSTOS (MILLONES $COP)", style=styles['filter-label']),
                    dcc.RangeSlider(
                        id='costo-slider',
                        min=0,
                        max=7000,
                        value=[0, 7000],
                        marks={i: {'label': f"{i}", 'style': {'fontSize': '14px', 'color': colors['text']}} 
                               for i in range(0, 7001, 1000)},
                        step=50,
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True,
                            "style": {
                                'fontSize': '16px',
                                'color': colors['text'],
                                'backgroundColor': colors['filter-bg']
                            }
                        },
                        updatemode='drag'
                    )
                ])
            ]),
            html.Div(style=styles['year-slider-container'], children=[
                html.Label("RANGO DE AÑOS", style=styles['filter-label']),
                dcc.RangeSlider(
                    id='year-slider',
                    min=df['Fecha inicio'].dt.year.min(),
                    max=df['Fecha inicio'].dt.year.max(),
                    value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
                    marks={str(year): {
                        'label': str(year), 
                        'style': {
                            'fontSize': '12px',
                            'color': colors['text'],
                            'whiteSpace': 'nowrap',
                            'transform': 'rotate(-45deg) translateX(-10px)',
                            'transformOrigin': 'bottom center'
                        }
                    } for year in range(df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()+1)},
                    step=None,
                    tooltip={
                        "placement": "bottom",
                        "always_visible": True,
                        "style": styles['year-slider-tooltip']
                    },
                    updatemode='drag'
                )
            ])
        ]),
        
        # Título sección general
        html.Div("INFORMACIÓN GENERAL DE LOS PROYECTOS", style=styles['section-title']),
        
        # KPIs
        html.Div(style=styles['summary'], children=[
            html.Div(style=styles['responsive-grid'], children=[
                html.Div(style={**styles['card'], 'backgroundColor': colors['panel-azul-1'], 'border':  f'2px solid #00CED1'}, children=[
                    html.Div("📌 TOTAL PROYECTOS", style=styles['kpi-title']),
                    html.Div(id='total-proyectos', style=styles['kpi-value'])
                ]),
                html.Div(style={**styles['card'], 'backgroundColor': colors['panel-azul-2'], 'border':  f'2px solid #00CED1'}, children=[
                    html.Div("💰 INVERSIÓN TOTAL", style=styles['kpi-title']),
                    html.Div(id='total-inversion', style=styles['kpi-value'])
                ]),
                html.Div(style={**styles['card'], 'backgroundColor': colors['panel-azul-3'], 'border':  f'2px solid #00CED1'}, children=[
                    html.Div("👥 BENEFICIARIOS", style=styles['kpi-title']),
                    html.Div(id='total-beneficiarios', style=styles['kpi-value'])
                ]),
                html.Div(style={**styles['card'], 'backgroundColor': colors['panel-azul-4'], 'border':  f'2px solid #00CED1'}, children=[
                    html.Div("🌿 ÁREA INTERVENIDA", style=styles['kpi-title']),
                    html.Div(id='total-area', style=styles['kpi-value'])
                ])
            ])
        ]),
        
        # Título sección específica
        html.Div("INFORMACIÓN ESPECÍFICA DE LOS PROYECTOS POR MUNICIPIO", style=styles['section-title']),
        
        # Mapa y lista de municipios - Reorganizado para móviles
        html.Div(style={
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '15px',
            'width': '100%'
        }, children=[
            # Mapa arriba en móviles
            html.Div(style=styles['map-container'], children=[
                html.Div(id='map-title', children=[
                    "Ubicación Geográfica de los Proyectos por Municipio",
                    html.Span(id='selected-municipio-title', style={'color': colors['map-highlight'], 'marginLeft': '8px', 'fontWeight': '600', 'fontSize': '18px'})
                ], style={
                    **styles['info-title'],
                    'textAlign': 'center',
                    'padding': '10px',
                    'backgroundColor': colors['map-title-bg'],
                    'color': 'white',
                    'marginBottom': '0',
                    'borderRadius': '12px 12px 0 0',
                    'fontSize': '18px',
                    'textShadow': '1px 1px 3px rgba(0,0,0,0.7)',
                    'borderBottom': f'2px solid {colors["title-color"]}'
                }),
                dcc.Graph(
                    id='mapa', 
                    config={
                        'displayModeBar': False,
                        'scrollZoom': True,
                        'responsive': True
                    },
                    style={'height': '100%', 'width': '100%'}
                ),
            ]),
            
            # Lista de municipios abajo en móviles
            html.Div(style=styles['municipios-list'], children=[
                html.Div("MUNICIPIOS CON PROYECTOS", style={
                    **styles['municipios-title'],
                    'position': 'sticky',
                    'top': '0',
                    'zIndex': '1',
                    'backgroundColor': colors['panel-municipios'],
                    'borderBottom': f'2px solid {colors["accent"]}'
                }),
                html.Div(id='municipios-cards-container', style={
                    'display': 'grid',
                    'gridTemplateColumns': '1fr',
                    'gap': '10px',
                    'padding': '5px',
                    'width': '100%',
                    'overflow': 'hidden'
                })
            ])
        ]),
        
        # Panel de información - Reorganizado para evitar superposiciones
        html.Div(style=styles['info-panel'], children=[
            html.Div(style={**styles['info-section-specific'], 
                           'backgroundColor': colors['panel-verde-cana-1'],
                           'border': f'2px solid {colors["map-highlight"]}'}, 
                children=[
                    html.Div("📍 MUNICIPIO SELECCIONADO", style=styles['info-title']),
                    html.Div(id='municipio-value', style={
                        **styles['info-value'],
                        'fontSize': '24px',
                        'color': colors['value-color'],
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-2'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                   html.Div("🏦 ENTIDAD FINANCIADORA", style=styles['info-title']),
                   html.Div(id='financiador-value', style={
                       **styles['info-text'],
                       'fontSize': '20px',
                   })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-3'],
                          'border': f'2px solid #00CED1'}, 
                children=[
                    html.Div("⏳ DURACIÓN (MESES)", style=styles['info-title']),
                    html.Div(id='duracion-value', style={
                        **styles['info-value'],
                        'color': colors['value-color'],
                        'fontSize': '24px',
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-4'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                    html.Div("👥 CANTIDAD BENEFICIARIOS", style=styles['info-title']),
                    html.Div(id='beneficiarios-value', style={
                        **styles['info-value'],
                        'color': colors['value-color'],
                        'fontSize': '24px',
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-5'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                    html.Div("🌳 HECTÁREAS INTERVENIDAS", style=styles['info-title']),
                    html.Div(id='area-value', style={
                        **styles['info-value'],
                        'color': colors['value-color'],
                        'fontSize': '24px',
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-6'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                    html.Div("📦 PRODUCTO PRINCIPAL", style=styles['info-title']),
                    html.Div(id='producto-value', style={
                        **styles['info-text'],
                        'fontSize': '20px',
                        'color': colors['value-color'],
                    })
            ])
        ]),
        
        # Panel de fotografías
        html.Div(style=styles['photo-panel'], children=[
            html.Div(style=styles['photo-selector-container'], children=[
                html.Div("SELECCIONAR UN PROYECTO", style=styles['photo-title']),
                dcc.Dropdown(
                    id='proyecto-selector',
                    style=styles['dropdown']
                )
            ]),
            
            html.Div(style=styles['photo-content'], children=[
                html.Div("EVIDENCIA FOTOGRÁFICA INICIAL Y FINAL DEL PROYECTO", style=styles['photo-title']),
                html.Div(id='photo-buttons', style=styles['photo-button-container'])
            ])
        ]),
        
        # Modal para fotografías
        html.Div(id='photo-modal', style={'display': 'none'}, children=[
            html.Div(style=styles['modal'], children=[
                html.Div(style=styles['modal-content'], children=[
                    html.Img(id='modal-image', style=styles['modal-image']),
                    html.Button("Cerrar", id='close-modal', style=styles['close-button'])
                ])
            ])
        ]),
        
        # Pie de página
        html.Div(style={
            'textAlign': 'center',
            'color': colors['title-color'],
            'marginTop': '15px',
            'fontSize': '16px',
            'padding': '10px',
            'borderTop': f'1px solid {colors["title-color"]}',
            'width': '100%'
        }, children=[
            html.P("© 2025 Fundación AIP - Todos los derechos reservados"),
            html.P("Datos actualizados al " + datetime.now().strftime("%d/%m/%Y"))
        ]),
        
        # Almacenamiento
        dcc.Store(id='filtered-data', data=None),
        dcc.Store(id='selected-municipio', data=None),
        dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 4.5}),
        dcc.Store(id='photo-store', data=None)
    ])
])

# Callbacks mejorados
@app.callback(
    Output('selected-municipio-title', 'children'),
    [Input('selected-municipio', 'data')]
)
def update_map_title(selected_municipio):
    if selected_municipio:
        return html.Div([
            " ",
            html.Span(selected_municipio, style={'color': colors['map-highlight']})
        ])
    return ""

@app.callback(
    [Output('filtered-data', 'data'),
     Output('total-proyectos', 'children'),
     Output('total-inversion', 'children'),
     Output('total-beneficiarios', 'children'),
     Output('total-area', 'children'),
     Output('mapa', 'figure'),
     Output('map-center', 'data')],
    [Input('tipo-dropdown', 'value'),
     Input('departamento-dropdown', 'value'),
     Input('comunidad-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('costo-slider', 'value'),
     Input('selected-municipio', 'data')],
    [State('map-center', 'data'),
     State('filtered-data', 'data')]
)
def update_filtered_data(tipos, departamentos, comunidades, anos, costos, selected_municipio, current_map_center, current_filtered_data):
    ctx = callback_context
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    filtered = df[
        (df['Fecha inicio'].dt.year >= anos[0]) & 
        (df['Fecha inicio'].dt.year <= anos[1]) &
        (df['Costo total ($COP)'] >= costos[0]*1000000) &
        (df['Costo total ($COP)'] <= costos[1]*1000000)
    ]
    
    if tipos:
        filtered = filtered[filtered['Tipo de proyecto'].isin(tipos)]
    if departamentos:
        filtered = filtered[filtered['Departamento'].isin(departamentos)]
    if comunidades:
        filtered = filtered[filtered['Comunidad beneficiaria'].isin(comunidades)]
    
    if filtered.empty:
        fig = px.choropleth_mapbox(
            title="No hay datos que coincidan con los filtros aplicados",
            center={"lat": 4.6, "lon": -74.1},
            zoom=4.5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":0,"l":0,"b":0},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(
                text="No hay municipios que coincidan con los filtros aplicados",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20)
            )]
        )
        
        return (
            [],
            "0",
            "$0M",
            "0",
            "0 ha",
            fig,
            {'lat': 4.6, 'lon': -74.1, 'zoom': 4.5}
        )
    
    # Unión con shapefile usando municipio y departamento
    filtered_with_geom = pd.merge(
        filtered,
        municipios_gdf[['MpNombre', 'Depto', 'geometry', 'lon', 'lat']],
        left_on=['Municipio', 'Departamento'],
        right_on=['MpNombre', 'Depto'],
        how='left'
    )
    
    filtered_gdf = gpd.GeoDataFrame(filtered_with_geom)
    
    if triggered_input == 'selected-municipio' and selected_municipio and current_filtered_data:
        filtered_df = pd.DataFrame(current_filtered_data)
        municipio_data = filtered_df[filtered_df['Municipio'] == selected_municipio]
        if not municipio_data.empty:
            departamento = municipio_data.iloc[0]['Departamento']
            bbox = get_municipio_bbox(selected_municipio, departamento)
            if bbox:
                map_center = bbox
            else:
                # Si no se puede calcular el bbox, centrar en las coordenadas del municipio
                municipio_geom = municipios_gdf[
                    (municipios_gdf['MpNombre'] == selected_municipio) & 
                    (municipios_gdf['Depto'] == departamento)
                ]
                if not municipio_geom.empty:
                    map_center = {
                        'lat': municipio_geom.iloc[0]['lat'],
                        'lon': municipio_geom.iloc[0]['lon'],
                        'zoom': 10  # Zoom por defecto para municipios
                    }
                else:
                    map_center = current_map_center
        else:
            map_center = current_map_center
    else:
        map_center = current_map_center if current_map_center else {'lat': 4.6, 'lon': -74.1, 'zoom': 4.5}
    
    filtered_with_geometry = filtered_gdf[~filtered_gdf.geometry.isna()]
    
    if filtered_with_geometry.empty:
        fig = px.choropleth_mapbox(
            title="No hay datos geográficos para los filtros aplicados",
            center={"lat": 4.6, "lon": -74.1},
            zoom=4.5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":0,"l":0,"b":0},
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(
                text="No se encontraron coincidencias geográficas para los municipios filtrados",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20)
            )]
        )
    else:
        # Crear figura base con los municipios
        fig = px.choropleth_mapbox(
            filtered_with_geometry,
            geojson=filtered_with_geometry.geometry,
            locations=filtered_with_geometry.index,
            color="Tipo de proyecto",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            center={"lat": map_center['lat'], "lon": map_center['lon']},
            zoom=map_center['zoom'],
            opacity=0.8,
            custom_data=['MpNombre', 'Depto', 'Tipo de proyecto', 'ID']
        )
        
        # Actualizar el hover template para los polígonos (municipios)
        fig.update_traces(
            hovertemplate="<b>Municipio: %{customdata[0]}</b><br>Departamento: %{customdata[1]}<br>Proyecto: %{customdata[2]}<br>ID: %{customdata[3]}<extra></extra>"
        )
        
        # Agregar puntos de ubicaciones AIP con información de Municipio y Departamento
        fig.add_trace(
            px.scatter_mapbox(
                aip_locations_gdf,
                lat=aip_locations_gdf.geometry.y,
                lon=aip_locations_gdf.geometry.x,
                color_discrete_sequence=['#90EE90']  # Verde claro notorio
            ).update_traces(
                marker=dict(size=10, opacity=0.8),
                name="Cobertura de trabajo AIP",  # Leyenda para los puntos
                hovertemplate="<b>Municipio: %{customdata[0]}</b><br>Departamento: %{customdata[1]}<extra></extra>",
                customdata=aip_locations_gdf[["Municipio", "Departamen"]],
                showlegend=True  # Asegurar que aparezca en la leyenda
            ).data[0]
        )
        
        if selected_municipio and current_filtered_data:
            filtered_df = pd.DataFrame(current_filtered_data)
            municipio_data = filtered_df[filtered_df['Municipio'] == selected_municipio]
            if not municipio_data.empty:
                departamento = municipio_data.iloc[0]['Departamento']
                selected_municipio_geom = municipios_gdf[
                    (municipios_gdf['MpNombre'] == selected_municipio) & 
                    (municipios_gdf['Depto'] == departamento)
                ]
                if not selected_municipio_geom.empty:
                    fig.add_trace(
                        px.choropleth_mapbox(
                            selected_municipio_geom,
                            geojson=selected_municipio_geom.geometry,
                            locations=selected_municipio_geom.index,
                            color_discrete_sequence=[colors['map-highlight']]
                        ).update_traces(
                            hovertemplate=None,
                            hoverinfo='skip'
                        ).data[0]
                    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=None,
            font=dict(size=14)),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        clickmode='event+select'
    )
    
    total_proyectos = len(filtered)
    total_inversion = f"${filtered['Costo total ($COP)'].sum()/1000000:,.0f}M"
    total_beneficiarios = f"{filtered['Beneficiarios totales'].sum():,}"
    total_area = f"{filtered['Área intervenida (ha)'].sum():,.1f} ha"
    
    return (
        filtered.to_dict('records'),
        total_proyectos,
        total_inversion,
        total_beneficiarios,
        total_area,
        fig,
        map_center
    )

@app.callback(
    Output('municipios-cards-container', 'children'),
    [Input('filtered-data', 'data')],
    [State('selected-municipio', 'data')]
)
def update_municipios_list(filtered_data, selected_municipio):
    if not filtered_data:
        return html.Div("No hay municipios con los filtros actuales", style={
            'textAlign': 'center', 
            'color': 'white', 
            'fontSize': '18px',
            'padding': '15px',
            'backgroundColor': 'rgba(0,0,0,0.2)',
            'borderRadius': '8px'
        })
    
    filtered_df = pd.DataFrame(filtered_data)
    municipios = filtered_df['Municipio'].unique()
    
    cards = []
    for municipio in sorted(municipios):
        count = len(filtered_df[filtered_df['Municipio'] == municipio])
        is_selected = municipio == selected_municipio
        
        card_style = styles['municipio-card-selected'] if is_selected else styles['municipio-card']
        name_style = styles['municipio-name-selected'] if is_selected else styles['municipio-name']
        count_style = styles['municipio-projects-selected'] if is_selected else styles['municipio-projects']
        
        cards.append(
            html.Div(
                [
                    html.Div(municipio, style=name_style),
                    html.Div(f"{count} proyecto{'s' if count > 1 else ''}", style=count_style)
                ],
                id={'type': 'municipio-card', 'index': municipio},
                style=card_style,
                n_clicks=0
            )
        )
    
    return cards if cards else html.Div("No hay municipios con los filtros actuales", style={
        'textAlign': 'center', 
        'color': 'white', 
        'fontSize': '18px',
        'padding': '15px',
        'backgroundColor': 'rgba(0,0,0,0.2)',
        'borderRadius': '8px'
    })

@app.callback(
    [Output('selected-municipio', 'data'),
     Output('municipio-value', 'children'),
     Output('beneficiarios-value', 'children'),
     Output('financiador-value', 'children'),
     Output('duracion-value', 'children'),
     Output('area-value', 'children'),
     Output('producto-value', 'children'),
     Output({'type': 'municipio-card', 'index': ALL}, 'style'),
     Output('proyecto-selector', 'options'),
     Output('proyecto-selector', 'value'),
     Output('photo-buttons', 'children'),
     Output('photo-store', 'data')],
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData'),
     Input('proyecto-selector', 'value')],
    [State('filtered-data', 'data'),
     State({'type': 'municipio-card', 'index': ALL}, 'id'),
     State('municipios-cards-container', 'children')],
    prevent_initial_call=True
)
def handle_municipio_selection(clicks, map_click, selected_proyecto, filtered_data, municipio_ids, municipios_cards):
    ctx = callback_context
    
    if not ctx.triggered or not filtered_data:
        default_styles = [styles['municipio-card'] for _ in municipio_ids] if municipio_ids else []
        return [
            None, "Seleccione un municipio", "0", "N/A", "0", "0", "N/A", 
            default_styles,
            [], None, [], None
        ]
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and 'points' in map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point and len(point['customdata']) == 4:  # Es un polígono
                municipio = point['customdata'][0]
            else:  # Es un punto de ubicación AIP
                municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
        else:
            default_styles = [styles['municipio-card'] for _ in municipio_ids] if municipio_ids else []
            return [
                None, "Seleccione un municipio", "0", "N/A", "0", "0", "N/A", 
                default_styles,
                [], None, [], None
            ]
    elif trigger_id == 'proyecto-selector.value':
        filtered_df = pd.DataFrame(filtered_data)
        municipio_data = filtered_df[filtered_df['ID'] == selected_proyecto]
        if not municipio_data.empty:
            municipio = municipio_data.iloc[0]['Municipio']
        else:
            raise PreventUpdate
    else:
        municipio = json.loads(trigger_id.split('.')[0].replace("'", '"'))['index']
    
    filtered_df = pd.DataFrame(filtered_data)
    municipio_data = filtered_df[filtered_df['Municipio'] == municipio]
    
    if trigger_id == 'proyecto-selector.value' and selected_proyecto:
        proyecto_data = municipio_data[municipio_data['ID'] == selected_proyecto].iloc[0]
    else:
        proyecto_data = municipio_data.iloc[0] if not municipio_data.empty else None
        selected_proyecto = proyecto_data['ID'] if proyecto_data is not None else None
    
    if proyecto_data is None:
        default_styles = [styles['municipio-card'] for _ in municipio_ids] if municipio_ids else []
        return [
            None, "Seleccione un municipio", "0", "N/A", "0", "0", "N/A", 
            default_styles,
            [], None, [], None
        ]
    
    beneficiarios = proyecto_data['Beneficiarios totales']
    financiador = proyecto_data['Entidad financiadora']
    duracion = f"{proyecto_data['Duración del proyecto (meses)']:.1f}"
    area = f"{proyecto_data['Área intervenida (ha)']:,.1f}"
    producto = proyecto_data['Producto principal generado']
    
    card_styles = []
    for m_id in municipio_ids:
        if m_id['index'] == municipio:
            card_styles.append(styles['municipio-card-selected'])
        else:
            card_styles.append(styles['municipio-card'])
    
    proyectos_options = [{'label': f"Proyecto {row['ID']} - {row['Tipo de proyecto']}", 'value': row['ID']} 
                        for _, row in municipio_data.iterrows()]
    
    foto_data = []
    buttons = []
    if selected_proyecto:
        for i in [1, 2]:
            foto_path = f"assets/fotos/Rf {i} proyecto {selected_proyecto}.jpg"
            if os.path.exists(foto_path):
                encoded_image = encode_image(foto_path, mobile=True)
                foto_data.append({
                    'photo_num': i,
                    'image': encoded_image
                })
                buttons.append(
                    html.Button(
                        f"Ver evidencia {i}",
                        id={'type': 'photo-button', 'index': i},
                        n_clicks=0,
                        style=styles['photo-button']
                    )
                )
    
    return [
        municipio, 
        municipio, 
        f"{beneficiarios:,}", 
        financiador, 
        duracion, 
        area, 
        producto, 
        card_styles,
        proyectos_options,
        selected_proyecto,
        buttons,
        foto_data
    ]

@app.callback(
    Output('photo-modal', 'style'),
    [Input({'type': 'photo-button', 'index': ALL}, 'n_clicks'),
     Input('close-modal', 'n_clicks')],
    [State('photo-store', 'data')],
    prevent_initial_call=True
)
def toggle_modal(photo_clicks, close_click, foto_data):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'close-modal' in trigger_id:
        return {'display': 'none'}
    
    if foto_data and any(photo_clicks):
        button_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
        photo_num = button_id['index']
        
        for foto in foto_data:
            if foto['photo_num'] == photo_num:
                return {'display': 'flex'}
    
    return {'display': 'none'}

@app.callback(
    Output('modal-image', 'src'),
    [Input({'type': 'photo-button', 'index': ALL}, 'n_clicks')],
    [State('photo-store', 'data')],
    prevent_initial_call=True
)
def update_modal_image(photo_clicks, foto_data):
    ctx = callback_context
    if not ctx.triggered or not foto_data:
        raise PreventUpdate
    
    button_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
    photo_num = button_id['index']
    
    for foto in foto_data:
        if foto['photo_num'] == photo_num:
            return foto['image']
    
    raise PreventUpdate

# Función mejorada para obtener bbox de municipio
def get_municipio_bbox(municipio_name, departamento_name):
    try:
        municipio = municipios_gdf[(municipios_gdf['MpNombre'] == municipio_name.upper().strip()) & 
                                  (municipios_gdf['Depto'] == departamento_name.upper().strip())]
        if municipio.empty:
            return None
        
        bounds = municipio.geometry.bounds
        minx, miny, maxx, maxy = bounds.iloc[0]
        padding = 0.1
        minx -= padding
        miny -= padding
        maxx += padding
        maxy += padding
        center_lon = (minx + maxx) / 2
        center_lat = (miny + maxy) / 2
        width = maxx - minx
        height = maxy - miny
        
        # Ajuste dinámico del zoom basado en el tamaño del municipio
        zoom = max(8 - max(width, height) * 5, 10)  # Zoom mínimo de 10
        
        return {
            'lat': center_lat,
            'lon': center_lon,
            'zoom': zoom
        }
    except Exception as e:
        print(f"Error calculando bbox para {municipio_name}: {e}")
        return None

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
