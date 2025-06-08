# -*- coding: utf-8 -*-
"""
Dashboard Fundación AIP - Versión Optimizada
1. Solucionado problema de visualización de municipios
2. Mejorado el rendimiento y manejo de datos
3. Optimizado para producción
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
import base64
import io
import unicodedata

# Configuración inicial
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True)
server = app.server

# Función para normalizar texto (eliminar acentos y caracteres especiales)
def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).strip().upper()
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    return text

# Función para codificar imágenes
def encode_image(image_path):
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    except Exception as e:
        print(f"Error procesando imagen: {e}")
    return None

# Carga de datos con manejo robusto de errores
try:
    # Cargar shapefiles
    shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
    municipios_gdf = gpd.read_file(shapefile_path)
    
    aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
    aip_locations_gdf = gpd.read_file(aip_locations_path)

    # Codificar imágenes
    logo_path = "assets/logo.png"
    huella_path = "assets/Figura_huella_aip.png"
    logo_encoded = encode_image(logo_path)
    huella_encoded = encode_image(huella_path)

    # Procesamiento de datos geoespaciales
    if municipios_gdf.crs != "EPSG:4326":
        municipios_gdf = municipios_gdf.to_crs("EPSG:4326")
    if aip_locations_gdf.crs != "EPSG:4326":
        aip_locations_gdf = aip_locations_gdf.to_crs("EPSG:4326")

    # Calcular centroides
    municipios_gdf['centroid'] = municipios_gdf.geometry.centroid
    municipios_gdf['lon'] = municipios_gdf.centroid.map(lambda p: p.x)
    municipios_gdf['lat'] = municipios_gdf.centroid.map(lambda p: p.y)

    # Cargar y procesar datos de proyectos
    def cargar_base_datos():
        df = pd.read_excel("data/proyectos.xlsx")
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
        df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
        
        # Normalización de nombres
        df['Municipio'] = df['Municipio'].apply(normalize_text)
        df['Departamento'] = df['Departamento'].apply(normalize_text)
        
        return df

    df = cargar_base_datos()

    # Procesar nombres en el shapefile
    municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].apply(normalize_text)
    municipios_gdf['Depto'] = municipios_gdf['Depto'].apply(normalize_text)

    # Verificación de coincidencias con logging detallado
    municipios_en_shapefile = set(zip(municipios_gdf['MpNombre'], municipios_gdf['Depto']))
    municipios_en_proyectos = set(zip(df['Municipio'], df['Departamento']))
    
    no_encontrados = municipios_en_proyectos - municipios_en_shapefile
    if no_encontrados:
        print("\nMunicipios no encontrados en shapefile:")
        print("{:<30} {:<30}".format("Municipio", "Departamento"))
        for mun, depto in sorted(no_encontrados):
            print("{:<30} {:<30}".format(mun, depto))

except Exception as e:
    print(f"\nError crítico cargando datos: {str(e)}")
    # Datos de ejemplo para evitar fallos totales
    df = pd.DataFrame({
        'Municipio': ['EJEMPLO'],
        'Departamento': ['EJEMPLO'],
        'Tipo de proyecto': ['Ejemplo'],
        'ID': [0]
    })
    logo_encoded = huella_encoded = None

# Esquema de colores optimizado
colors = {
    'background': '#e8f5e9',
    'text': '#333333',
    'primary': '#2e5d2e',
    'panel-general': 'rgba(72, 139, 72, 0.8)',
    'panel-municipios': 'rgba(139, 90, 43, 0.8)',
    'title-color': '#2e7d32',
    'selected-color': '#8B0000',
    'map-highlight': '#8B0000'
}

# Estilos optimizados
styles = {
    'container': {
        'maxWidth': '100%',
        'padding': '10px',
        'backgroundColor': colors['background']
    },
    'header-container': {
        'textAlign': 'center',
        'marginBottom': '20px'
    },
    'header': {
        'color': colors['title-color'],
        'fontSize': 'clamp(22px, 4vw, 28px)'
    },
    'map-container': {
        'height': '500px',
        'marginBottom': '15px'
    },
    'municipio-card': {
        'padding': '10px',
        'marginBottom': '10px',
        'backgroundColor': 'white'
    },
    'municipio-card-selected': {
        'backgroundColor': colors['selected-color'],
        'color': 'white'
    }
}

# Layout simplificado y optimizado
app.layout = html.Div(style=styles['container'], children=[
    html.Div(style=styles['header-container'], children=[
        html.H1("NUESTRA HUELLA EN COLOMBIA", style=styles['header']),
        html.Img(src=logo_encoded, style={'height': '100px'}) if logo_encoded else None
    ]),
    
    # Filtros
    html.Div([
        dcc.Dropdown(
            id='departamento-dropdown',
            options=[{'label': depto, 'value': depto} for depto in sorted(df['Departamento'].unique())],
            multi=True,
            placeholder="Seleccione departamentos..."
        ),
        dcc.RangeSlider(
            id='year-slider',
            min=df['Fecha inicio'].dt.year.min(),
            max=df['Fecha inicio'].dt.year.max(),
            value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
            marks={str(year): str(year) for year in range(
                df['Fecha inicio'].dt.year.min(), 
                df['Fecha inicio'].dt.year.max()+1, 2)}
        )
    ]),
    
    # Mapa
    html.Div(style=styles['map-container'], children=[
        dcc.Graph(id='mapa', config={'displayModeBar': False})
    ]),
    
    # Información de municipios
    html.Div(id='municipios-cards-container'),
    
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio')
])

# Callbacks optimizados
@app.callback(
    [Output('filtered-data', 'data'),
     Output('mapa', 'figure')],
    [Input('departamento-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_map(departamentos, anos):
    filtered = df[
        (df['Fecha inicio'].dt.year >= anos[0]) & 
        (df['Fecha inicio'].dt.year <= anos[1])
    ]
    
    if departamentos:
        filtered = filtered[filtered['Departamento'].isin(departamentos)]
    
    # Unión robusta con shapefile
    merged = pd.merge(
        filtered,
        municipios_gdf,
        left_on=['Municipio', 'Departamento'],
        right_on=['MpNombre', 'Depto'],
        how='left'
    )
    
    # Filtrar solo los que tienen geometría
    merged = merged[~merged.geometry.isna()]
    
    if merged.empty:
        fig = px.choropleth_mapbox(
            center={"lat": 4.6, "lon": -74.1},
            zoom=4.5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            annotations=[dict(
                text="No hay datos para los filtros seleccionados",
                showarrow=False,
                font=dict(size=20)
            )]
        )
    else:
        fig = px.choropleth_mapbox(
            merged,
            geojson=merged.geometry,
            locations=merged.index,
            color="Tipo de proyecto",
            center={"lat": 4.6, "lon": -74.1},
            zoom=5,
            custom_data=['MpNombre', 'Depto', 'Tipo de proyecto']
        )
        
        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>%{customdata[2]}"
        )
    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return filtered.to_dict('records'), fig

@app.callback(
    Output('municipios-cards-container', 'children'),
    [Input('filtered-data', 'data'),
     Input('selected-municipio', 'data')]
)
def update_municipios_list(filtered_data, selected_municipio):
    if not filtered_data:
        return "No hay municipios con los filtros actuales"
    
    filtered_df = pd.DataFrame(filtered_data)
    municipios = filtered_df['Municipio'].unique()
    
    cards = []
    for municipio in sorted(municipios):
        count = len(filtered_df[filtered_df['Municipio'] == municipio])
        is_selected = municipio == selected_municipio
        
        card_style = {**styles['municipio-card'], 
                     **styles['municipio-card-selected']} if is_selected else styles['municipio-card']
        
        cards.append(
            html.Div(
                [
                    html.Div(municipio),
                    html.Div(f"{count} proyectos")
                ],
                id={'type': 'municipio-card', 'index': municipio},
                style=card_style,
                n_clicks=0
            )
        )
    
    return cards

@app.callback(
    Output('selected-municipio', 'data'),
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def select_municipio(clicks, map_click, municipio_ids):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'mapa.clickData' in trigger_id:
        if map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point:
                return point['customdata'][0]  # Retorna el nombre del municipio
    
    # Si se hizo clic en una tarjeta de municipio
    if clicks and any(clicks):
        clicked_index = clicks.index(max(clicks))
        return municipio_ids[clicked_index]['index']
    
    return None

if __name__ == '__main__':
    app.run_server(debug=False)
