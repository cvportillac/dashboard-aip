# -*- coding: utf-8 -*-
"""
Dashboard Fundación AIP - Versión Completa con:
1. Gestión automática de dependencias
2. Sincronización perfecta mapa-lista
3. Visualización interactiva de proyectos
"""

import sys
import subprocess
import pkg_resources

# Verificar e instalar dependencias necesarias
required = {
    'Pillow', 'pandas', 'plotly', 'dash', 'geopandas', 
    'gunicorn', 'shapely', 'numpy', 'openpyxl'
}

installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    print(f"Instalando paquetes faltantes: {missing}")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])

# Ahora importamos las librerías
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
import logging
from PIL import Image  # Ahora debería funcionar después de la instalación

# Configuración inicial
logging.basicConfig(level=logging.INFO)
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True)
server = app.server

# Función para normalizar nombres de municipios
def normalize_name(name):
    """Normaliza nombres para matching consistente"""
    if not isinstance(name, str):
        return ""
    name = name.upper().strip()
    replacements = (
        ("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"),
        ("Ñ", "N"), ("Ü", "U"), ("´", ""), ("'", ""), (".", ""),
        ("-", " "), ("  ", " ")
    )
    for a, b in replacements:
        name = name.replace(a, b)
    return name

# Función para codificar imágenes
def encode_image(image_path, mobile=False):
    """Codifica imágenes para la web"""
    try:
        if os.path.exists(image_path):
            with Image.open(image_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
    except Exception as e:
        logging.error(f"Error procesando imagen: {e}")
        return None

# Carga de datos
try:
    # Cargar shapefiles
    municipios_gdf = gpd.read_file("data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp")
    aip_locations_gdf = gpd.read_file("data/shapefiles/cobertura_trabajo_aip.shp")

    # Cargar datos de proyectos
    df = pd.read_excel("data/proyectos.xlsx")
    df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
    df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
    df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
    
    # Normalizar nombres
    df['Municipio'] = df['Municipio'].apply(normalize_name)
    df['Departamento'] = df['Departamento'].apply(normalize_name)
    df['Municipio_Depto'] = df['Municipio'] + "|" + df['Departamento']
    
    municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].apply(normalize_name)
    municipios_gdf['Depto'] = municipios_gdf['Depto'].apply(normalize_name)
    municipios_gdf['Municipio_Depto'] = municipios_gdf['MpNombre'] + "|" + municipios_gdf['Depto']

    # Procesamiento geoespacial
    for gdf in [municipios_gdf, aip_locations_gdf]:
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
    
    projected = municipios_gdf.to_crs("EPSG:3116")
    projected['centroid'] = projected.geometry.centroid
    municipios_gdf['lon'] = projected.centroid.map(lambda p: p.x)
    municipios_gdf['lat'] = projected.centroid.map(lambda p: p.y)

    # Codificar imágenes
    logo_encoded = encode_image("assets/logo.png", mobile=True)
    huella_encoded = encode_image("assets/Figura_huella_aip.png", mobile=True)

except Exception as e:
    logging.error(f"Error cargando datos: {e}")
    df = pd.DataFrame({
        'Municipio': ['EJEMPLO'], 'Departamento': ['EJEMPLO'],
        'Tipo de proyecto': ['EJEMPLO'], 'Fecha inicio': [datetime.now()],
        'Fecha fin': [datetime.now()], 'Beneficiarios totales': [0],
        'Municipio_Depto': ['EJEMPLO|EJEMPLO'], 'ID': [0]
    })
    logo_encoded = huella_encoded = None

# Estilos y diseño
colors = {
    'background': '#e8f5e9', 'primary': '#2e5d2e',
    'selected': '#8B0000', 'text': '#333333'
}

app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'padding': '20px'
}, children=[
    html.Div([
        html.Img(src=logo_encoded, style={'height': '100px'}) if logo_encoded else None,
        html.H1("Proyectos Fundación AIP", style={'color': colors['primary']})
    ], style={'textAlign': 'center'}),
    
    dcc.Graph(id='mapa'),
    
    html.Div(id='municipios-list', style={
        'marginTop': '20px',
        'padding': '15px',
        'backgroundColor': 'white',
        'borderRadius': '10px'
    }),
    
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio')
])

# Callbacks
@app.callback(
    [Output('filtered-data', 'data'),
     Output('mapa', 'figure')],
    [Input('selected-municipio', 'data')]
)
def update_map(selected_municipio):
    filtered = df.copy()
    
    # Crear mapa base
    fig = px.choropleth_mapbox(
        filtered,
        geojson=municipios_gdf.geometry,
        locations=municipios_gdf.index,
        hover_name="MpNombre",
        center={"lat": 4.6, "lon": -74.1},
        zoom=5,
        opacity=0.5
    )
    
    # Resaltar selección
    if selected_municipio:
        selected = municipios_gdf[municipios_gdf['MpNombre'] == selected_municipio]
        fig.add_trace(
            px.choropleth_mapbox(
                selected,
                geojson=selected.geometry,
                locations=selected.index
            ).data[0]
        )
    
    fig.update_layout(mapbox_style="carto-positron")
    return filtered.to_dict('records'), fig

@app.callback(
    Output('municipios-list', 'children'),
    [Input('filtered-data', 'data')],
    [State('selected-municipio', 'data')]
)
def update_list(filtered_data, selected):
    filtered_df = pd.DataFrame(filtered_data)
    municipios = filtered_df['Municipio'].unique()
    
    return [
        html.Div(
            html.Div(m, style={
                'padding': '10px',
                'margin': '5px',
                'backgroundColor': colors['selected'] if m == selected else 'white',
                'color': 'white' if m == selected else colors['text'],
                'cursor': 'pointer'
            }),
            id={'type': 'municipio-card', 'index': m},
            n_clicks=0
        ) for m in municipios
    ]

@app.callback(
    Output('selected-municipio', 'data'),
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def select_municipio(clicks, map_click, ids):
    ctx = callback_context
    if not ctx.triggered:
        return None
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and map_click['points']:
            return map_click['points'][0]['hovertext']
        return None
    
    button_id = json.loads(trigger_id.split('.')[0].replace("'", '"'))
    return button_id['index']

if __name__ == '__main__':
    app.run_server(debug=True)
