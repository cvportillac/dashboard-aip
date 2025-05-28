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

# 1. Configuración inicial y carga de datos
shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
municipios_gdf = gpd.read_file(shapefile_path)

# Cargar shapefile de ubicaciones AIP
aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
aip_locations_gdf = gpd.read_file(aip_locations_path)

# Cargar y codificar el logo y la figura de huella
logo_path = "assets/logo.png"
huella_path = "assets/Figura_huella_aip.png"

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:image/jpeg;base64,{encoded_string}"

logo_encoded = encode_image(logo_path) if os.path.exists(logo_path) else None
huella_encoded = encode_image(huella_path) if os.path.exists(huella_path) else None

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
    
    # Normalizar nombres de municipios y departamentos para coincidencia exacta
    df['Municipio'] = df['Municipio'].str.upper().str.strip()
    df['Departamento'] = df['Departamento'].str.upper().str.strip()
    municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].str.upper().str.strip()
    municipios_gdf['Depto'] = municipios_gdf['Depto'].str.upper().str.strip()
    
    return df

df = cargar_base_datos()
app = Dash(__name__, title="Dashboard de Proyectos Fundación AIP", suppress_callback_exceptions=True)

# 2. Esquema de colores mejorado con gamas ordenadas
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
    'aip-locations': '#FFA500'
}

# 3. Estilos optimizados
styles = {
    'container': {
        'display': 'grid',
        'gridTemplateColumns': '70% 30%',
        'gap': '20px',
        'width': '100%',
        'maxWidth': '1800px',
        'margin': '0 auto',
        'padding': '20px',
        'fontFamily': '"Segoe UI", "Open Sans", sans-serif',
        'backgroundColor': colors['background']
    },
    'header': {
        'textAlign': 'left',
        'color': colors['title-color'],
        'marginBottom': '0',
        'fontWeight': '700',
        'fontSize': '52px',
        'paddingBottom': '15px',
        'textShadow': '2px 2px 4px rgba(0,0,0,0.5)',
        'borderBottom': f'2px solid {colors["title-color"]}',
        'marginLeft': '20px',
        'display': 'inline-block',
        'verticalAlign': 'middle'
    },
    'header-container': {
        'gridColumn': '1 / span 2',
        'display': 'grid',
        'gridTemplateColumns': '1fr auto',
        'alignItems': 'center',
        'marginBottom': '20px'
    },
    'logo-container': {
        'display': 'flex',
        'justifyContent': 'flex-end',
        'alignItems': 'center',
        'paddingRight': '20px',
        'width': 'auto'
    },
    'logo': {
        'height': '200px',
        'margin': '10px',
        'objectFit': 'contain',
        'maxWidth': '100%'
    },
    'huella-img': {
        'height': '150px',
        'verticalAlign': 'middle',
        'marginLeft': '15px',
        'marginBottom': '5px'
    },
    'section-title': {
        'gridColumn': '1 / span 2',
        'textAlign': 'left',
        'color': colors['title-color'],
        'margin': '15px 0 10px 0',
        'fontWeight': '600',
        'fontSize': '30px',
        'paddingLeft': '15px',
        'borderLeft': f'4px solid {colors["title-color"]}',
        'backgroundColor': 'rgba(0,0,0,0.2)',
        'padding': '8px 10px',
        'borderRadius': '4px'
    },
    'filters': {
        'gridColumn': '1 / span 2',
        'backgroundColor': colors['filter-bg'],
        'padding': '20px',
        'borderRadius': '12px',
        'marginBottom': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}'
    },
    'map-container': {
        'position': 'relative',
        'height': '600px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'border': f'1px solid {colors["border-color"]}'
    },
    'municipios-list': {
        'height': '600px',
        'overflowY': 'auto',
        'padding': '15px',
        'backgroundColor': colors['panel-municipios'],
        'borderRadius': '12px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["panel-municipios"]}'
    },
    'municipio-card': {
        'padding': '15px',
        'marginBottom': '12px',
        'borderRadius': '10px',
        'backgroundColor': colors['card-bg'],
        'cursor': 'pointer',
        'transition': 'all 0.3s ease',
        'border': f'1px solid {colors["panel-municipios"]}',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.15)',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center'
    },
    'municipio-card-selected': {
        'padding': '15px',
        'marginBottom': '12px',
        'borderRadius': '10px',
        'backgroundColor': colors['selected-card-bg'],
        'color': 'white',
        'cursor': 'pointer',
        'border': '3px solid white',
        'boxShadow': '0 4px 8px rgba(255, 0, 0, 0.6)',
        'transform': 'scale(1.02)',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center'
    },
    'municipio-name': {
        'fontWeight': '600',
        'fontSize': '24px',
        'marginBottom': '8px',
        'textAlign': 'center',
        'color': '#333333',
        'width': '100%'
    },
    'municipio-name-selected': {
        'fontWeight': '600',
        'fontSize': '26px',
        'marginBottom': '8px',
        'textAlign': 'center',
        'color': 'white',
        'width': '100%',
        'textShadow': '1px 1px 3px rgba(0,0,0,0.7)'
    },
    'municipio-projects': {
        'fontSize': '22px',
        'fontWeight': '600',
        'textAlign': 'center',
        'backgroundColor': '#e6f3ff',
        'color': colors['panel-municipios'],
        'padding': '6px 12px',
        'borderRadius': '18px',
        'minWidth': '90px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.15)'
    },
    'municipio-projects-selected': {
        'fontSize': '22px',
        'fontWeight': '600',
        'textAlign': 'center',
        'backgroundColor': 'rgba(255,255,255,0.3)',
        'color': 'white',
        'padding': '6px 12px',
        'borderRadius': '18px',
        'minWidth': '90px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.3)',
        'border': '2px solid white'
    },
    'municipios-title': {
        'textAlign': 'center',
        'color': 'white',
        'fontWeight': '600',
        'fontSize': '28px',
        'marginBottom': '20px',
        'padding': '12px',
        'borderRadius': '6px',
        'backgroundColor': 'rgba(0,0,0,0.3)',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.15)',
        'textTransform': 'uppercase',
        'letterSpacing': '1px',
        'borderBottom': f'2px solid {colors["title-color"]}'
    },
    'info-panel': {
        'gridColumn': '1 / span 2',
        'display': 'grid',
        'gridTemplateColumns': 'repeat(6, 1fr)',
        'gap': '15px',
        'marginTop': '15px',
        'backgroundColor': colors['filter-bg'],
        'padding': '15px',
        'borderRadius': '12px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}'
    },
    'info-section-specific': {
        'padding': '20px',
        'borderRadius': '10px',
        'height': '100%',
        'border': f'2px solid {colors["selected-color"]}',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'transition': 'all 0.3s ease',
        'minHeight': '130px'
    },
    'info-title': {
        'fontSize': '24px',
        'fontWeight': '600',
        'color': colors['title-color'],
        'marginBottom': '12px',
        'paddingBottom': '8px',
        'borderBottom': f'2px solid {colors["title-color"]}',
        'textAlign': 'center',
        'textTransform': 'uppercase',
        'letterSpacing': '0.5px',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.5)'
    },
    'info-value': {
        'fontSize': '36px',
        'fontWeight': '600',
        'color': colors['value-color'],
        'margin': 'auto 0',
        'textAlign': 'center',
        'flexGrow': '1',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'
    },
    'info-text': {
        'fontSize': '30px',
        'fontWeight': '600',
        'color': colors['value-color'],
        'margin': 'auto 0',
        'textAlign': 'center',
        'flexGrow': '1',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'lineHeight': '1.4',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.3)'
    },
    'filter-label': {
        'fontWeight': '600',
        'marginBottom': '10px',
        'color': colors['title-color'],
        'fontSize': '22px',
        'textShadow': '1px 1px 1px rgba(0,0,0,0.3)'
    },
    'dropdown': {
        'width': '100%',
        'borderRadius': '6px',
        'border': f'1px solid {colors["border-color"]}',
        'fontSize': '20px',
        'backgroundColor': 'white',
        'color': '#333333'
    },
    'summary': {
        'gridColumn': '1 / span 2',
        'backgroundColor': colors['filter-bg'],
        'padding': '15px',
        'borderRadius': '12px',
        'marginBottom': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}'
    },
    'card': {
        'backgroundColor': colors['panel-general'],
        'borderRadius': '12px',
        'padding': '20px',
        'marginBottom': '0px',
        'height': '100%',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'textAlign': 'center',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'border': f'2px solid {colors["selected-color"]}'
    },
    'kpi-title': {
        'fontSize': '26px',
        'marginBottom': '12px',
        'color': colors['title-color'],
        'fontWeight': '600',
        'textShadow': '1px 1px 2px rgba(0,0,0,0.3)'
    },
    'kpi-value': {
        'fontSize': '48px',
        'fontWeight': '700',
        'color': colors['value-color'],
        'marginTop': '8px',
        'textShadow': '1px 1px 3px rgba(0,0,0,0.5)'
    },
    'arrow': {
        'position': 'absolute',
        'width': '40px',
        'height': '40px',
        'zIndex': '1001',
        'display': 'none',
        'backgroundImage': 'url("data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'40\' height=\'40\' viewBox=\'0 0 40 40\'><path d=\'M10,20 L30,20 M30,20 L25,15 M30,20 L25,25\' stroke=\'%23d4af37\' stroke-width=\'2\' fill=\'none\'/></svg>")',
        'backgroundRepeat': 'no-repeat'
    },
    'photo-panel': {
        'gridColumn': '1 / span 2',
        'display': 'grid',
        'gridTemplateColumns': '30% 70%',
        'gap': '15px',
        'backgroundColor': colors['photo-panel'],
        'padding': '15px',
        'borderRadius': '12px',
        'marginTop': '15px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'border': f'1px solid {colors["border-color"]}'
    },
    'photo-selector-container': {
        'backgroundColor': colors['panel-especifico'],
        'padding': '15px',
        'borderRadius': '8px',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center'
    },
    'photo-content': {
        'display': 'flex',
        'flexDirection': 'column',
        'gap': '12px'
    },
    'photo-title': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'fontWeight': '600',
        'fontSize': '26px',
        'marginBottom': '8px',
        'textTransform': 'uppercase'
    },
    'photo-dropdown': {
        'width': '100%',
        'padding': '8px',
        'borderRadius': '6px',
        'backgroundColor': colors['filter-bg'],
        'color': colors['text'],
        'fontSize': '20px',
        'border': f'1px solid {colors["border-color"]}'
    },
    'photo-button-container': {
        'display': 'flex',
        'flexDirection': 'row',
        'gap': '15px',
        'justifyContent': 'center',
        'alignItems': 'center',
        'flexWrap': 'wrap'
    },
    'photo-button': {
        'padding': '8px 16px',
        'borderRadius': '6px',
        'backgroundColor': colors['accent'],
        'color': colors['background'],
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '18px',
        'margin': '4px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.15)',
        'transition': 'all 0.3s ease'
    },
    'photo-button:hover': {
        'backgroundColor': colors['hover-color'],
        'transform': 'scale(1.05)'
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
        'alignItems': 'center'
    },
    'modal-content': {
        'backgroundColor': colors['background'],
        'padding': '15px',
        'borderRadius': '8px',
        'maxWidth': '90%',
        'maxHeight': '90%',
        'overflow': 'auto',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.4)',
        'border': f'2px solid {colors["title-color"]}',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center'
    },
    'modal-image': {
        'maxWidth': '100%',
        'maxHeight': '80vh',
        'borderRadius': '6px',
        'boxShadow': '0 3px 6px rgba(0,0,0,0.25)',
        'marginBottom': '15px'
    },
    'close-button': {
        'padding': '8px 16px',
        'borderRadius': '6px',
        'backgroundColor': colors['accent'],
        'color': colors['background'],
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '18px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.15)'
    },
    'proyecto-selector-label': {
        'color': colors['text'],
        'fontSize': '20px',
        'marginBottom': '8px',
        'textAlign': 'center',
        'fontWeight': '600'
    }
}

# 4. Layout de la aplicación
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'minHeight': '100vh',
    'padding': '15px',
    'margin': '0'
}, children=[
    html.Div(style=styles['container'], children=[
        # Encabezado con título, huella y logo
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
                    'flexWrap': 'wrap'
                }),
            ),
            html.Div(style=styles['logo-container'], children=[
                html.Img(
                    src=logo_encoded,
                    style=styles['logo']
                ) if logo_encoded else html.Div("Logo no encontrado")
            ])
        ]),
        
        # Fila 1: Filtros
        html.Div(style=styles['filters'], children=[
            html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px'}, children=[
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
                        marks={i: {'label': f"{i}", 'style': {'fontSize': '18px', 'color': colors['text']}} 
                               for i in range(0, 7001, 1000)},
                        step=50,
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True,
                            "style": {
                                'fontSize': '20px',
                                'color': colors['text'],
                                'backgroundColor': colors['filter-bg']
                            }
                        },
                        updatemode='drag'
                    )
                ])
            ]),
            html.Div(style={'marginTop': '15px'}, children=[
                html.Label("RANGO DE AÑOS", style=styles['filter-label']),
                dcc.RangeSlider(
                    id='year-slider',
                    min=df['Fecha inicio'].dt.year.min(),
                    max=df['Fecha inicio'].dt.year.max(),
                    value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
                    marks={str(year): {'label': str(year), 'style': {'fontSize': '18px', 'color': colors['text']}} 
                           for year in range(df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()+1)},
                    step=None,
                    tooltip={
                        "placement": "bottom",
                        "always_visible": True,
                        "style": {
                            'fontSize': '20px',
                            'color': colors['text'],
                            'backgroundColor': colors['filter-bg']
                        }
                    },
                    updatemode='drag'
                )
            ])
        ]),
        
        # Título sección general
        html.Div("INFORMACIÓN GENERAL DE LOS PROYECTOS", style=styles['section-title']),
        
        # Fila 2: KPIs con gama ordenada de azules
        html.Div(style=styles['summary'], children=[
            html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)', 'gap': '15px', 'height': '100%'}, children=[
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
        
        # Fila 3: Mapa y Lista de Municipios
        html.Div(style=styles['map-container'], children=[
            html.Div(id='map-title', children=[
                "Ubicación Geográfica de los Proyectos por Municipio",
                html.Span(id='selected-municipio-title', style={'color': colors['map-highlight'], 'marginLeft': '8px', 'fontWeight': '600', 'fontSize': '24px'})
            ], style={
                **styles['info-title'],
                'textAlign': 'center',
                'padding': '12px',
                'backgroundColor': colors['panel-especifico'],
                'marginBottom': '0',
                'borderRadius': '12px 12px 0 0'
            }),
            dcc.Graph(
                id='mapa', 
                config={'displayModeBar': False},
                style={'height': '540px'},
                clickData=None
            ),
            html.Div(id='arrow-1', style=styles['arrow']),
            html.Div(id='arrow-2', style=styles['arrow']),
            html.Div(id='arrow-3', style=styles['arrow']),
            html.Div(id='arrow-4', style=styles['arrow'])
        ]),
        
        html.Div(style=styles['municipios-list'], children=[
            html.Div("MUNICIPIOS CON PROYECTOS", style=styles['municipios-title']),
            html.Div(id='municipios-cards-container', style={
                'display': 'grid',
                'gridTemplateColumns': '1fr',
                'gap': '12px',
                'padding': '8px',
            })
        ]),
        
        # Fila 4: Panel de información con gama ordenada de café
        html.Div(style=styles['info-panel'], children=[
            html.Div(style={**styles['info-section-specific'], 
                           'backgroundColor': colors['panel-verde-cana-1'],
                           'border': f'2px solid {colors["map-highlight"]}'}, 
                children=[
                    html.Div("📍 MUNICIPIO SELECCIONADO", style=styles['info-title'], ),
                    html.Div(id='municipio-value', style={
                        **styles['info-value'],
                        'fontSize': '36px',
                        'color': colors['value-color']
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-2'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                   html.Div("🏦 ENTIDAD FINANCIADORA", style=styles['info-title']),
                   html.Div(id='financiador-value', style={
                       **styles['info-text'],
                       'fontSize': '32px'
                   })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-3'],
                          'border': f'2px solid #00CED1'}, 
                children=[
                    html.Div("⏳ DURACIÓN (MESES)", style=styles['info-title']),
                    html.Div(id='duracion-value', style={
                        **styles['info-value'],
                        'color': colors['value-color']
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-4'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                    html.Div("👥 CANTIDAD BENEFICIARIOS", style=styles['info-title']),
                    html.Div(id='beneficiarios-value', style={
                        **styles['info-value'],
                        'color': colors['value-color']
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-5'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                    html.Div("🌳 HECTÁREAS INTERVENIDAS", style=styles['info-title']),
                    html.Div(id='area-value', style={
                        **styles['info-value'],
                        'color': colors['value-color']
                    })
            ]),
            html.Div(style={**styles['info-section-specific'], 
                          'backgroundColor': colors['panel-verde-cana-6'],
                          'border':  f'2px solid #00CED1'}, 
                children=[
                    html.Div("📦 PRODUCTO PRINCIPAL", style=styles['info-title']),
                    html.Div(id='producto-value', style={
                        **styles['info-text'],
                        'fontSize': '32px',
                        'color': colors['value-color']
                    })
            ])
        ]),
        
        # Panel para visualización de fotografías
        html.Div(style=styles['photo-panel'], children=[
            # Sección izquierda - Selector de proyectos
            html.Div(style=styles['photo-selector-container'], children=[
                html.Div("SELECCIONAR UN PROYECTO", style=styles['photo-title']),
                dcc.Dropdown(
                    id='proyecto-selector',
                    style={
                        'width': '100%',
                        'borderRadius': '6px',
                        'border': f'1px solid {colors["border-color"]}',
                        'fontSize': '20px',
                        'backgroundColor': 'white',
                        'color': '#333333'
                    }
                )
            ]),
            
            # Sección derecha - Fotografías
            html.Div(style=styles['photo-content'], children=[
                html.Div("EVIDENCIA FOTOGRÁFICA INICIAL Y FINAL DEL PROYECTO", style=styles['photo-title']),
                html.Div(id='photo-buttons', style=styles['photo-button-container'])
            ])
        ]),
        
        # Modal para mostrar las fotografías
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
            'gridColumn': '1 / span 2',
            'textAlign': 'center',
            'color': colors['title-color'],
            'marginTop': '15px',
            'fontSize': '20px',
            'padding': '15px',
            'borderTop': f'1px solid {colors["title-color"]}'
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

# 5. Funciones de callback (sin cambios)
def get_municipio_bbox(municipio_name, departamento_name):
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
    zoom = 8 - max(width, height) * 5
    
    return {
        'lat': center_lat,
        'lon': center_lon,
        'zoom': max(zoom, 10)
    }

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
                    (municipios_gdf['MpNombre'] == selected_municipio.upper().strip()) & 
                    (municipios_gdf['Depto'] == departamento.upper().strip())
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
            'fontSize': '22px',
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
        'fontSize': '22px',
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
                encoded_image = encode_image(foto_path)
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

# 6. Ejecutar la aplicación
server = app.server
if __name__ == '__main__':
    print("\n✅ Dashboard listo! Accede en: http://127.0.0.1:8050\n")
    app.run(debug=True, dev_tools_ui=False)