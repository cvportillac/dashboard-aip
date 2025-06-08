# -*- coding: utf-8 -*-
"""
Created on Sat May 24 17:12:16 2025

@author: crisv
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

# 1. Configuración inicial móvil
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True, meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
])
server = app.server

# Carga de datos
shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
municipios_gdf = gpd.read_file(shapefile_path)

aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
aip_locations_gdf = gpd.read_file(aip_locations_path)

# Codificar imágenes
logo_path = "assets/logo.png"
huella_path = "assets/Figura_huella_aip.png"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded_string}"

logo_encoded = encode_image(logo_path) if os.path.exists(logo_path) else None
huella_encoded = encode_image(huella_path) if os.path.exists(huella_path) else None

# Proyección de coordenadas
if municipios_gdf.crs != "EPSG:4326":
    municipios_gdf = municipios_gdf.to_crs("EPSG:4326")
if aip_locations_gdf.crs != "EPSG:4326":
    aip_locations_gdf = aip_locations_gdf.to_crs("EPSG:4326")

municipios_gdf_projected = municipios_gdf.to_crs("EPSG:3116")
municipios_gdf_projected['centroid'] = municipios_gdf_projected.geometry.centroid
municipios_gdf['lon'] = municipios_gdf_projected.centroid.map(lambda p: p.x)
municipios_gdf['lat'] = municipios_gdf_projected.centroid.map(lambda p: p.y)

def cargar_base_datos():
    df = pd.read_excel("data/proyectos.xlsx")
    df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
    df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
    df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
    
    df['Municipio'] = df['Municipio'].str.upper().str.strip()
    df['Departamento'] = df['Departamento'].str.upper().str.strip()
    municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].str.upper().str.strip()
    municipios_gdf['Depto'] = municipios_gdf['Depto'].str.upper().str.strip()
    
    return df

df = cargar_base_datos()

# 2. Esquema de colores optimizado para móvil
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
    'card-bg': 'rgba(255, 255, 255, 0.9)',
    'selected-card-bg': '#8B0000',
    'map-highlight': '#8B0000',
    'aip-locations': '#FFA500'
}

# 3. Estilos optimizados para móvil
styles = {
    'container': {
        'width': '100%',
        'margin': '0 auto',
        'padding': '10px',
        'fontFamily': '"Segoe UI", "Open Sans", sans-serif',
        'backgroundColor': colors['background']
    },
    'header': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'marginBottom': '5px',
        'fontWeight': '600',
        'fontSize': '24px',
        'paddingBottom': '10px',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.3)'
    },
    'header-container': {
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'marginBottom': '10px'
    },
    'logo-container': {
        'display': 'flex',
        'justifyContent': 'center',
        'marginTop': '10px'
    },
    'logo': {
        'height': '80px',
        'margin': '5px',
        'objectFit': 'contain'
    },
    'huella-img': {
        'height': '50px',
        'marginLeft': '5px',
        'marginBottom': '5px'
    },
    'section-title': {
        'textAlign': 'left',
        'color': colors['title-color'],
        'margin': '10px 0',
        'fontWeight': '600',
        'fontSize': '18px',
        'paddingLeft': '10px',
        'borderLeft': f'3px solid {colors["title-color"]}'
    },
    'filters': {
        'backgroundColor': 'rgba(233, 245, 233, 0.9)',
        'padding': '10px',
        'borderRadius': '8px',
        'marginBottom': '10px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.1)'
    },
    'map-container': {
        'position': 'relative',
        'height': '400px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'marginBottom': '10px'
    },
    'municipios-list': {
        'height': '300px',
        'overflowY': 'auto',
        'padding': '10px',
        'backgroundColor': colors['panel-municipios'],
        'borderRadius': '8px',
        'marginBottom': '10px'
    },
    'municipio-card': {
        'padding': '10px',
        'marginBottom': '8px',
        'borderRadius': '8px',
        'backgroundColor': colors['card-bg'],
        'cursor': 'pointer'
    },
    'municipio-card-selected': {
        'padding': '10px',
        'marginBottom': '8px',
        'borderRadius': '8px',
        'backgroundColor': colors['selected-card-bg'],
        'color': 'white',
        'cursor': 'pointer',
        'border': '2px solid white'
    },
    'municipio-name': {
        'fontWeight': '600',
        'fontSize': '16px',
        'marginBottom': '5px',
        'textAlign': 'center'
    },
    'municipio-name-selected': {
        'fontWeight': '600',
        'fontSize': '16px',
        'marginBottom': '5px',
        'textAlign': 'center',
        'color': 'white'
    },
    'municipio-projects': {
        'fontSize': '14px',
        'textAlign': 'center',
        'backgroundColor': '#e6f3ff',
        'color': colors['panel-municipios'],
        'padding': '4px 8px',
        'borderRadius': '12px'
    },
    'municipio-projects-selected': {
        'fontSize': '14px',
        'textAlign': 'center',
        'backgroundColor': 'rgba(255,255,255,0.3)',
        'color': 'white',
        'padding': '4px 8px',
        'borderRadius': '12px'
    },
    'municipios-title': {
        'textAlign': 'center',
        'color': 'white',
        'fontWeight': '600',
        'fontSize': '16px',
        'marginBottom': '10px',
        'padding': '8px'
    },
    'info-panel': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': '10px',
        'marginBottom': '10px'
    },
    'info-section-specific': {
        'padding': '10px',
        'borderRadius': '8px',
        'border': f'1px solid {colors["map-highlight"]}',
        'minHeight': '80px'
    },
    'info-title': {
        'fontSize': '14px',
        'fontWeight': '600',
        'color': colors['title-color'],
        'marginBottom': '5px',
        'textAlign': 'center'
    },
    'info-value': {
        'fontSize': '18px',
        'fontWeight': '600',
        'textAlign': 'center'
    },
    'filter-label': {
        'fontWeight': '600',
        'marginBottom': '5px',
        'color': colors['title-color'],
        'fontSize': '14px'
    },
    'dropdown': {
        'width': '100%',
        'borderRadius': '4px',
        'fontSize': '14px',
        'marginBottom': '10px'
    },
    'summary': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': '10px',
        'marginBottom': '10px'
    },
    'card': {
        'backgroundColor': colors['panel-general'],
        'borderRadius': '8px',
        'padding': '10px',
        'textAlign': 'center',
        'minHeight': '80px'
    },
    'kpi-title': {
        'fontSize': '14px',
        'marginBottom': '5px',
        'color': colors['title-color'],
        'fontWeight': '600'
    },
    'kpi-value': {
        'fontSize': '20px',
        'fontWeight': '700'
    },
    'photo-panel': {
        'display': 'flex',
        'flexDirection': 'column',
        'gap': '10px',
        'marginBottom': '10px'
    },
    'photo-selector-container': {
        'backgroundColor': colors['panel-especifico'],
        'padding': '10px',
        'borderRadius': '8px'
    },
    'photo-title': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'fontWeight': '600',
        'fontSize': '14px',
        'marginBottom': '5px'
    },
    'photo-button-container': {
        'display': 'flex',
        'flexDirection': 'row',
        'gap': '10px',
        'justifyContent': 'center',
        'flexWrap': 'wrap'
    },
    'photo-button': {
        'padding': '6px 12px',
        'borderRadius': '4px',
        'backgroundColor': colors['accent'],
        'color': 'white',
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '12px'
    },
    'modal': {
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'width': '100%',
        'height': '100%',
        'backgroundColor': 'rgba(0,0,0,0.85)',
        'zIndex': '1000',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center'
    },
    'modal-content': {
        'backgroundColor': colors['background'],
        'padding': '10px',
        'borderRadius': '8px',
        'maxWidth': '90%',
        'maxHeight': '90%',
        'overflow': 'auto'
    },
    'modal-image': {
        'maxWidth': '100%',
        'maxHeight': '70vh',
        'borderRadius': '4px'
    },
    'close-button': {
        'padding': '6px 12px',
        'borderRadius': '4px',
        'backgroundColor': colors['accent'],
        'color': 'white',
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'marginTop': '10px'
    }
}

# 4. Layout móvil optimizado
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'padding': '5px',
    'margin': '0'
}, children=[
    html.Div(style=styles['container'], children=[
        # Encabezado
        html.Div(style=styles['header-container'], children=[
            html.Div(style={'display': 'flex', 'alignItems': 'center'}, children=[
                html.Div("NUESTRA HUELLA EN COLOMBIA", style=styles['header']),
                html.Img(src=huella_encoded, style=styles['huella-img']) if huella_encoded else None
            ]),
            html.Div(style=styles['logo-container'], children=[
                html.Img(src=logo_encoded, style=styles['logo']) if logo_encoded else None
            ])
        ]),
        
        # Filtros
        html.Div(style=styles['filters'], children=[
            html.Div([
                html.Label("TIPO DE PROYECTO", style=styles['filter-label']),
                dcc.Dropdown(
                    id='tipo-dropdown',
                    options=[{'label': t, 'value': t} for t in sorted(df['Tipo de proyecto'].unique())],
                    multi=True,
                    placeholder="Seleccione tipos...",
                    style=styles['dropdown']
                ),
                html.Label("DEPARTAMENTO", style=styles['filter-label']),
                dcc.Dropdown(
                    id='departamento-dropdown',
                    options=[{'label': d, 'value': d} for d in sorted(df['Departamento'].unique())],
                    multi=True,
                    placeholder="Seleccione departamentos...",
                    style=styles['dropdown']
                ),
                html.Label("COMUNIDAD BENEFICIARIA", style=styles['filter-label']),
                dcc.Dropdown(
                    id='comunidad-dropdown',
                    options=[{'label': c, 'value': c} for c in sorted(df['Comunidad beneficiaria'].unique())],
                    multi=True,
                    placeholder="Seleccione comunidades...",
                    style=styles['dropdown']
                ),
                html.Label("RANGO DE COSTOS (MILLONES $COP)", style=styles['filter-label']),
                dcc.RangeSlider(
                    id='costo-slider',
                    min=0,
                    max=7000,
                    value=[0, 7000],
                    marks={i: f"{i}" for i in range(0, 7001, 1000)},
                    step=50,
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Label("RANGO DE AÑOS", style=styles['filter-label']),
                dcc.RangeSlider(
                    id='year-slider',
                    min=df['Fecha inicio'].dt.year.min(),
                    max=df['Fecha inicio'].dt.year.max(),
                    value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
                    marks={str(year): str(year) for year in range(df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()+1)},
                    step=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ])
        ]),
        
        # KPIs
        html.Div("INFORMACIÓN GENERAL", style=styles['section-title']),
        html.Div(style=styles['summary'], children=[
            html.Div(style=styles['card'], children=[
                html.Div("📌 TOTAL PROYECTOS", style=styles['kpi-title']),
                html.Div(id='total-proyectos', style=styles['kpi-value'])
            ]),
            html.Div(style=styles['card'], children=[
                html.Div("💰 INVERSIÓN TOTAL", style=styles['kpi-title']),
                html.Div(id='total-inversion', style=styles['kpi-value'])
            ]),
            html.Div(style=styles['card'], children=[
                html.Div("👥 BENEFICIARIOS", style=styles['kpi-title']),
                html.Div(id='total-beneficiarios', style=styles['kpi-value'])
            ]),
            html.Div(style=styles['card'], children=[
                html.Div("🌿 ÁREA INTERVENIDA", style=styles['kpi-title']),
                html.Div(id='total-area', style=styles['kpi-value'])
            ])
        ]),
        
        # Mapa y Municipios
        html.Div("INFORMACIÓN POR MUNICIPIO", style=styles['section-title']),
        html.Div(style=styles['map-container'], children=[
            dcc.Graph(
                id='mapa', 
                config={'displayModeBar': False},
                style={'height': '100%'}
            )
        ]),
        
        html.Div(style=styles['municipios-list'], children=[
            html.Div("MUNICIPIOS CON PROYECTOS", style=styles['municipios-title']),
            html.Div(id='municipios-cards-container')
        ]),
        
        # Panel de información
        html.Div(style=styles['info-panel'], children=[
            html.Div(style=styles['info-section-specific'], children=[
                html.Div("📍 MUNICIPIO SELECCIONADO", style=styles['info-title']),
                html.Div(id='municipio-value', style=styles['info-value'])
            ]),
            html.Div(style=styles['info-section-specific'], children=[
                html.Div("🏦 ENTIDAD FINANCIADORA", style=styles['info-title']),
                html.Div(id='financiador-value', style=styles['info-value'])
            ]),
            html.Div(style=styles['info-section-specific'], children=[
                html.Div("⏳ DURACIÓN (MESES)", style=styles['info-title']),
                html.Div(id='duracion-value', style=styles['info-value'])
            ]),
            html.Div(style=styles['info-section-specific'], children=[
                html.Div("👥 BENEFICIARIOS", style=styles['info-title']),
                html.Div(id='beneficiarios-value', style=styles['info-value'])
            ]),
            html.Div(style=styles['info-section-specific'], children=[
                html.Div("🌳 HECTÁREAS", style=styles['info-title']),
                html.Div(id='area-value', style=styles['info-value'])
            ]),
            html.Div(style=styles['info-section-specific'], children=[
                html.Div("📦 PRODUCTO", style=styles['info-title']),
                html.Div(id='producto-value', style=styles['info-value'])
            ])
        ]),
        
        # Fotografías
        html.Div(style=styles['photo-panel'], children=[
            html.Div(style=styles['photo-selector-container'], children=[
                html.Div("SELECCIONAR PROYECTO", style=styles['photo-title']),
                dcc.Dropdown(
                    id='proyecto-selector',
                    style=styles['dropdown']
                )
            ]),
            html.Div(style={'marginTop': '10px'}, children=[
                html.Div("EVIDENCIA FOTOGRÁFICA", style=styles['photo-title']),
                html.Div(id='photo-buttons', style=styles['photo-button-container'])
            ])
        ]),
        
        # Modal
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
            'marginTop': '10px',
            'fontSize': '12px',
            'padding': '10px'
        }, children=[
            html.P("© 2025 Fundación AIP - Todos los derechos reservados"),
            html.P("Datos actualizados al " + datetime.now().strftime("%d/%m/%Y"))
        ]),
        
        # Almacenamiento
        dcc.Store(id='filtered-data'),
        dcc.Store(id='selected-municipio'),
        dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 4.5}),
        dcc.Store(id='photo-store')
    ])
])

# 5. Callbacks (se mantienen iguales que en el original)
# [Aquí irían todos los callbacks sin cambios, solo se modifica el layout]

# 6. Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
