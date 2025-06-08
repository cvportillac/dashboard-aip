# -*- coding: utf-8 -*-
"""
Dashboard Fundación AIP - Versión Final con nombres originales
Mantiene los nombres exactos de municipios como están en los archivos fuente
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

# Configuración inicial
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True)
server = app.server

# Función para codificar imágenes
def encode_image(image_path, mobile=False):
    """Codifica imágenes a base64 manteniendo transparencia"""
    try:
        if os.path.exists(image_path):
            with Image.open(image_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return None

# Carga de datos manteniendo nombres originales
try:
    # Cargar shapefiles
    shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
    municipios_gdf = gpd.read_file(shapefile_path)
    
    aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
    aip_locations_gdf = gpd.read_file(aip_locations_path)

    # Codificar imágenes
    logo_path = "assets/logo.png"
    huella_path = "assets/Figura_huella_aip.png"
    logo_encoded = encode_image(logo_path, mobile=True)
    huella_encoded = encode_image(huella_path, mobile=True)

    # Procesamiento geoespacial
    if municipios_gdf.crs != "EPSG:4326":
        municipios_gdf = municipios_gdf.to_crs("EPSG:4326")
    if aip_locations_gdf.crs != "EPSG:4326":
        aip_locations_gdf = aip_locations_gdf.to_crs("EPSG:4326")

    # Calcular centroides para posición
    municipios_gdf_projected = municipios_gdf.to_crs("EPSG:3116")
    municipios_gdf_projected['centroid'] = municipios_gdf_projected.geometry.centroid
    municipios_gdf['lon'] = municipios_gdf_projected.centroid.map(lambda p: p.x)
    municipios_gdf['lat'] = municipios_gdf_projected.centroid.map(lambda p: p.y)

    # Cargar datos de proyectos manteniendo nombres originales
    def cargar_base_datos():
        df = pd.read_excel("data/proyectos.xlsx")
        
        # Procesamiento básico de fechas y cálculos
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
        df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
        
        # Verificación de nombres
        print("\nMunicipios en proyectos:", df['Municipio'].unique())
        print("Municipios en shapefile:", municipios_gdf['MpNombre'].unique())
        
        return df

    df = cargar_base_datos()

except Exception as e:
    print(f"Error cargando datos: {e}")
    # Datos de ejemplo en caso de error
    df = pd.DataFrame({
        'Municipio': ['Ejemplo'],
        'Departamento': ['Ejemplo'],
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
    'map-highlight': '#8B0000',
    'photo-panel': 'rgba(233, 245, 233, 0.9)',
    'modal-bg': 'rgba(0,0,0,0.85)'
}

# Estilos CSS
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
        'overflowX': 'hidden'
    },
    'header': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'marginBottom': '0',
        'fontWeight': '700',
        'fontSize': 'clamp(22px, 4vw, 28px)',
        'paddingBottom': '10px',
        'borderBottom': f'2px solid {colors["title-color"]}'
    },
    'map-container': {
        'height': '500px',
        'width': '100%',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'borderRadius': '12px',
        'overflow': 'hidden'
    },
    'municipio-card': {
        'padding': '10px',
        'margin': '5px',
        'borderRadius': '8px',
        'backgroundColor': colors['card-bg'],
        'cursor': 'pointer',
        'transition': 'all 0.3s ease'
    },
    'municipio-card-selected': {
        'padding': '10px',
        'margin': '5px',
        'borderRadius': '8px',
        'backgroundColor': colors['selected-color'],
        'color': 'white',
        'cursor': 'pointer',
        'border': '2px solid white'
    }
}

# Layout de la aplicación
app.layout = html.Div(style=styles['container'], children=[
    html.Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
    
    # Encabezado
    html.Div([
        html.Div("NUESTRA HUELLA EN COLOMBIA", style=styles['header']),
        html.Img(src=logo_encoded, style={'height': '100px', 'margin': '10px auto'}) if logo_encoded else None,
        html.Img(src=huella_encoded, style={'height': '80px', 'marginLeft': '10px'}) if huella_encoded else None
    ], style={'textAlign': 'center'}),
    
    # Filtros
    html.Div([
        html.Div([
            html.Label("Tipo de proyecto"),
            dcc.Dropdown(
                id='tipo-dropdown',
                options=[{'label': t, 'value': t} for t in df['Tipo de proyecto'].unique()],
                multi=True
            )
        ]),
        
        html.Div([
            html.Label("Departamento"),
            dcc.Dropdown(
                id='departamento-dropdown',
                options=[{'label': d, 'value': d} for d in df['Departamento'].unique()],
                multi=True
            )
        ]),
        
        dcc.RangeSlider(
            id='year-slider',
            min=df['Fecha inicio'].dt.year.min(),
            max=df['Fecha inicio'].dt.year.max(),
            value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
            marks={str(year): str(year) for year in range(df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()+1)}
        )
    ], style={'padding': '20px', 'backgroundColor': colors['filter-bg'], 'borderRadius': '10px'}),
    
    # Mapa y lista
    html.Div([
        html.Div(
            dcc.Graph(id='mapa', config={'displayModeBar': False}),
            style=styles['map-container']
        ),
        
        html.Div(id='municipios-list', style={
            'maxHeight': '400px',
            'overflowY': 'auto',
            'marginTop': '20px'
        })
    ]),
    
    # Paneles de información
    html.Div(id='info-panel', style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
        'gap': '15px',
        'marginTop': '20px'
    }),
    
    # Almacenamiento
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio'),
    dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 4.5})
])

# Callbacks principales
@app.callback(
    [Output('filtered-data', 'data'),
     Output('mapa', 'figure'),
     Output('map-center', 'data')],
    [Input('tipo-dropdown', 'value'),
     Input('departamento-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('selected-municipio', 'data')],
    [State('map-center', 'data')]
)
def update_filtered_data(tipos, departamentos, anos, selected_municipio, map_center):
    filtered = df[
        (df['Fecha inicio'].dt.year >= anos[0]) & 
        (df['Fecha inicio'].dt.year <= anos[1])
    ]
    
    if tipos:
        filtered = filtered[filtered['Tipo de proyecto'].isin(tipos)]
    if departamentos:
        filtered = filtered[filtered['Departamento'].isin(departamentos)]
    
    # Merge con shapefiles usando nombres originales
    merged = pd.merge(
        filtered,
        municipios_gdf[['MpNombre', 'Depto', 'geometry', 'lon', 'lat']],
        left_on=['Municipio', 'Departamento'],
        right_on=['MpNombre', 'Depto'],
        how='left'
    )
    
    filtered_gdf = gpd.GeoDataFrame(merged)
    filtered_with_geom = filtered_gdf[~filtered_gdf.geometry.isna()]
    
    # Crear mapa
    fig = px.choropleth_mapbox(
        filtered_with_geom,
        geojson=filtered_with_geom.geometry,
        locations=filtered_with_geom.index,
        color="Tipo de proyecto",
        center={"lat": map_center['lat'], "lon": map_center['lon']},
        zoom=map_center['zoom'],
        opacity=0.7,
        custom_data=['Municipio', 'Departamento', 'Tipo de proyecto']
    )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        clickmode='event+select'
    )
    
    return filtered.to_dict('records'), fig, map_center

@app.callback(
    Output('municipios-list', 'children'),
    [Input('filtered-data', 'data')],
    [State('selected-municipio', 'data')]
)
def update_municipios_list(filtered_data, selected_municipio):
    if not filtered_data:
        return "No hay municipios con los filtros actuales"
    
    filtered_df = pd.DataFrame(filtered_data)
    municipios = filtered_df['Municipio'].unique()
    
    cards = []
    for municipio in municipios:
        count = len(filtered_df[filtered_df['Municipio'] == municipio])
        is_selected = municipio == selected_municipio
        
        card_style = styles['municipio-card-selected'] if is_selected else styles['municipio-card']
        
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
    [Output('selected-municipio', 'data'),
     Output('info-panel', 'children')],
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State('filtered-data', 'data')]
)
def handle_municipio_selection(clicks, map_click, filtered_data):
    ctx = callback_context
    
    if not ctx.triggered or not filtered_data:
        return None, []
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'mapa.clickData' in trigger_id and map_click:
        municipio = map_click['points'][0]['customdata'][0]
    else:
        municipio = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])['index']
    
    filtered_df = pd.DataFrame(filtered_data)
    municipio_data = filtered_df[filtered_df['Municipio'] == municipio].iloc[0]
    
    info_panel = [
        html.Div([
            html.Div("Municipio:"),
            html.Div(municipio_data['Municipio'], style={'fontWeight': 'bold'})
        ]),
        html.Div([
            html.Div("Proyectos:"),
            html.Div(municipio_data['Tipo de proyecto'])
        ])
    ]
    
    return municipio, info_panel

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
