# -*- coding: utf-8 -*-
"""
Dashboard Fundación AIP - Versión Completa
Características principales:
1. Sincronización perfecta entre mapa interactivo y lista de municipios
2. Normalización avanzada de nombres para matching preciso
3. Visualización de proyectos con filtros dinámicos
4. Panel de información detallada por municipio
5. Galería fotográfica de proyectos
6. Diseño completamente responsive
7. Optimizado para dispositivos móviles
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
import logging
from PIL import Image

# Configuración inicial
logging.basicConfig(level=logging.INFO)
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True)
server = app.server

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================

def normalize_name(name):
    """Normaliza nombres para matching consistente entre datasets"""
    if not isinstance(name, str):
        return ""
    name = name.upper().strip()
    replacements = (
        ("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"),
        ("Ñ", "N"), ("Ü", "U"), ("´", ""), ("'", ""), (".", ""),
        ("-", " "), ("  ", " "), ("SAN ", "SAN"), ("SANTA ", "SANTA")
    )
    for a, b in replacements:
        name = name.replace(a, b)
    return name

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
        logging.error(f"Error procesando imagen {image_path}: {e}")
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    return None

def get_municipio_bbox(municipio_name, departamento_name):
    """Calcula el bounding box para centrar el mapa en un municipio específico"""
    try:
        municipio_name = normalize_name(municipio_name)
        departamento_name = normalize_name(departamento_name)
        
        municipio = municipios_gdf[
            (municipios_gdf['MpNombre'] == municipio_name) & 
            (municipios_gdf['Depto'] == departamento_name)
        ]
        
        if municipio.empty:
            logging.warning(f"No se encontró geometría para {municipio_name}, {departamento_name}")
            return None
        
        bounds = municipio.geometry.bounds
        minx, miny, maxx, maxy = bounds.iloc[0]
        padding = 0.1
        minx -= padding
        miny -= padding
        maxx += padding
        maxy += padding
        
        return {
            'lat': (miny + maxy) / 2,
            'lon': (minx + maxx) / 2,
            'zoom': max(8 - max(maxx-minx, maxy-miny) * 5, 10)
        }
    except Exception as e:
        logging.error(f"Error calculando bbox: {e}")
        return None

# ==============================================
# CARGA Y PREPARACIÓN DE DATOS
# ==============================================

try:
    # Cargar shapefiles
    municipios_gdf = gpd.read_file("data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp")
    aip_locations_gdf = gpd.read_file("data/shapefiles/cobertura_trabajo_aip.shp")

    # Cargar y preparar datos de proyectos
    df = pd.read_excel("data/proyectos.xlsx")
    df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
    df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
    df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
    
    # Normalización de nombres
    df['Municipio'] = df['Municipio'].apply(normalize_name)
    df['Departamento'] = df['Departamento'].apply(normalize_name)
    df['Municipio_Depto'] = df['Municipio'] + "|" + df['Departamento']
    
    municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].apply(normalize_name)
    municipios_gdf['Depto'] = municipios_gdf['Depto'].apply(normalize_name)
    municipios_gdf['Municipio_Depto'] = municipios_gdf['MpNombre'] + "|" + municipios_gdf['Depto']

    # Verificar consistencia
    missing = set(df['Municipio_Depto']) - set(municipios_gdf['Municipio_Depto'])
    if missing:
        logging.warning(f"Municipios sin geometría: {missing}")

    # Procesamiento geoespacial
    for gdf in [municipios_gdf, aip_locations_gdf]:
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
    
    # Calcular centroides
    projected = municipios_gdf.to_crs("EPSG:3116")
    projected['centroid'] = projected.geometry.centroid
    municipios_gdf['lon'] = projected.centroid.map(lambda p: p.x)
    municipios_gdf['lat'] = projected.centroid.map(lambda p: p.y)

    # Codificar imágenes
    logo_encoded = encode_image("assets/logo.png", mobile=True)
    huella_encoded = encode_image("assets/Figura_huella_aip.png", mobile=True)

except Exception as e:
    logging.error(f"Error cargando datos: {e}")
    # Datos de ejemplo para evitar errores
    df = pd.DataFrame({
        'Municipio': ['EJEMPLO'], 'Departamento': ['EJEMPLO'],
        'Tipo de proyecto': ['EJEMPLO'], 'Fecha inicio': [datetime.now()],
        'Fecha fin': [datetime.now()], 'Costo total ($COP)': [0],
        'Beneficiarios totales': [0], 'Área intervenida (ha)': [0],
        'Entidad financiadora': ['EJEMPLO'], 'Duración del proyecto (meses)': [0],
        'Producto principal generado': ['EJEMPLO'], 'Comunidad beneficiaria': ['EJEMPLO'],
        'ID': [0], 'Municipio_Depto': ['EJEMPLO|EJEMPLO']
    })
    logo_encoded = huella_encoded = None

# ==============================================
# ESTILOS Y DISEÑO
# ==============================================

colors = {
    'background': '#e8f5e9', 'text': '#333333', 'primary': '#2e5d2e',
    'secondary': '#4a7c4a', 'accent': '#8b5a2b', 'title-color': '#2e7d32',
    'value-color': '#333333', 'selected-color': '#8B0000',
    'map-highlight': '#8B0000', 'aip-locations': '#FFA500'
}

styles = {
    'container': {
        'display': 'grid', 'gridTemplateColumns': '1fr', 'gap': '15px',
        'width': '100%', 'maxWidth': '100%', 'margin': '0 auto',
        'padding': '10px', 'fontFamily': '"Segoe UI", "Open Sans", sans-serif',
        'backgroundColor': colors['background'], 'overflowX': 'hidden'
    },
    'header': {
        'textAlign': 'center', 'color': colors['title-color'],
        'marginBottom': '0', 'fontWeight': '700', 'fontSize': 'clamp(22px, 4vw, 28px)',
        'paddingBottom': '10px', 'borderBottom': f'2px solid {colors["title-color"]}'
    },
    'map-container': {
        'position': 'relative', 'height': '400px', 'minHeight': '300px',
        'width': '100%', 'boxShadow': '0 4px 12px rgba(0,0,0,0.2)',
        'backgroundColor': 'white', 'borderRadius': '12px'
    },
    'municipios-list': {
        'height': '400px', 'overflowY': 'auto', 'padding': '10px',
        'backgroundColor': 'rgba(139, 90, 43, 0.8)', 'borderRadius': '12px'
    },
    'municipio-card': {
        'padding': '10px', 'marginBottom': '10px', 'borderRadius': '8px',
        'backgroundColor': 'rgba(255, 255, 255, 0.9)', 'cursor': 'pointer',
        'transition': 'all 0.3s ease', 'border': '1px solid rgba(139, 90, 43, 0.8)'
    },
    'municipio-card-selected': {
        'padding': '10px', 'marginBottom': '10px', 'borderRadius': '8px',
        'backgroundColor': colors['selected-color'], 'color': 'white',
        'border': '3px solid white', 'boxShadow': '0 4px 8px rgba(255, 0, 0, 0.6)'
    },
    'info-panel': {
        'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
        'gap': '10px', 'marginTop': '15px', 'backgroundColor': 'rgba(233, 245, 233, 0.9)',
        'padding': '10px', 'borderRadius': '12px'
    },
    'info-section-specific': {
        'padding': '15px', 'borderRadius': '8px', 'height': '100%',
        'border': f'2px solid {colors["selected-color"]}', 'display': 'flex',
        'flexDirection': 'column', 'justifyContent': 'center'
    },
    'info-title': {
        'fontSize': 'clamp(14px, 2.5vw, 16px)', 'fontWeight': '600',
        'color': colors['title-color'], 'marginBottom': '8px',
        'textAlign': 'center', 'textTransform': 'uppercase'
    },
    'info-value': {
        'fontSize': 'clamp(18px, 4vw, 24px)', 'fontWeight': '600',
        'color': colors['value-color'], 'textAlign': 'center'
    }
}

# ==============================================
# LAYOUT DE LA APLICACIÓN
# ==============================================

app.layout = html.Div(style=styles['container'], children=[
    html.Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
    
    # Encabezado
    html.Div([
        html.Div([
            html.Span("NUESTRA HUELLA EN COLOMBIA ", style=styles['header']),
            html.Img(src=huella_encoded, style={'height': '80px', 'marginLeft': '10px'}) if huella_encoded else None
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
        
        html.Div([
            html.Img(src=logo_encoded, style={'height': '120px'}) if logo_encoded else None
        ], style={'display': 'flex', 'justifyContent': 'center'})
    ]),
    
    # Filtros
    html.Div([
        html.Div([
            html.Label("TIPO DE PROYECTO", style={'fontWeight': '600'}),
            dcc.Dropdown(
                id='tipo-dropdown',
                options=[{'label': t, 'value': t} for t in sorted(df['Tipo de proyecto'].unique())],
                multi=True,
                placeholder="Seleccione tipos..."
            )
        ]),
        
        html.Div([
            html.Label("DEPARTAMENTO", style={'fontWeight': '600'}),
            dcc.Dropdown(
                id='departamento-dropdown',
                options=[{'label': d, 'value': d} for d in sorted(df['Departamento'].unique())],
                multi=True,
                placeholder="Seleccione departamentos..."
            )
        ]),
        
        html.Div([
            html.Label("RANGO DE AÑOS", style={'fontWeight': '600'}),
            dcc.RangeSlider(
                id='year-slider',
                min=df['Fecha inicio'].dt.year.min(),
                max=df['Fecha inicio'].dt.year.max(),
                value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
                marks={str(year): {'label': str(year)} for year in range(
                    df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()+1)},
                step=None
            )
        ])
    ], style={'backgroundColor': 'rgba(233, 245, 233, 0.9)', 'padding': '15px', 'borderRadius': '12px'}),
    
    # KPIs
    html.Div([
        html.Div([
            html.Div("📌 TOTAL PROYECTOS", style=styles['info-title']),
            html.Div(id='total-proyectos', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(79, 195, 247, 0.8)'}),
        
        html.Div([
            html.Div("💰 INVERSIÓN TOTAL", style=styles['info-title']),
            html.Div(id='total-inversion', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(129, 212, 250, 0.8)'}),
        
        html.Div([
            html.Div("👥 BENEFICIARIOS", style=styles['info-title']),
            html.Div(id='total-beneficiarios', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(179, 229, 252, 0.8)'}),
        
        html.Div([
            html.Div("🌿 ÁREA INTERVENIDA", style=styles['info-title']),
            html.Div(id='total-area', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(207, 239, 253, 0.8)'})
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 'gap': '15px'}),
    
    # Mapa y lista de municipios
    html.Div([
        html.Div([
            dcc.Graph(
                id='mapa',
                config={'displayModeBar': False},
                style={'height': '100%', 'width': '100%'}
            )
        ], style=styles['map-container']),
        
        html.Div([
            html.Div("MUNICIPIOS CON PROYECTOS", style={
                'textAlign': 'center', 'color': 'white', 'fontWeight': '600',
                'marginBottom': '15px', 'padding': '8px', 'backgroundColor': 'rgba(0,0,0,0.3)'
            }),
            html.Div(id='municipios-cards-container')
        ], style=styles['municipios-list'])
    ], style={'display': 'grid', 'gridTemplateColumns': '1fr', 'gap': '15px', 'marginTop': '20px'}),
    
    # Panel de información
    html.Div([
        html.Div([
            html.Div("📍 MUNICIPIO SELECCIONADO", style=styles['info-title']),
            html.Div(id='municipio-value', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(100, 120, 60, 0.8)'}),
        
        html.Div([
            html.Div("🏦 ENTIDAD FINANCIADORA", style=styles['info-title']),
            html.Div(id='financiador-value', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(120, 140, 80, 0.8)'}),
        
        html.Div([
            html.Div("⏳ DURACIÓN (MESES)", style=styles['info-title']),
            html.Div(id='duracion-value', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(140, 160, 95, 0.8)'}),
        
        html.Div([
            html.Div("👥 BENEFICIARIOS", style=styles['info-title']),
            html.Div(id='beneficiarios-value', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(160, 180, 110, 0.8)'}),
        
        html.Div([
            html.Div("🌳 HECTÁREAS", style=styles['info-title']),
            html.Div(id='area-value', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(180, 200, 130, 0.8)'}),
        
        html.Div([
            html.Div("📦 PRODUCTO PRINCIPAL", style=styles['info-title']),
            html.Div(id='producto-value', style=styles['info-value'])
        ], style={**styles['info-section-specific'], 'backgroundColor': 'rgba(200, 220, 160, 0.8)'})
    ], style=styles['info-panel']),
    
    # Panel de fotografías
    html.Div([
        html.Div([
            html.Div("SELECCIONAR UN PROYECTO", style=styles['info-title']),
            dcc.Dropdown(id='proyecto-selector')
        ], style={'backgroundColor': 'rgba(102, 187, 106, 0.8)', 'padding': '15px', 'borderRadius': '8px'}),
        
        html.Div([
            html.Div("EVIDENCIA FOTOGRÁFICA", style=styles['info-title']),
            html.Div(id='photo-buttons', style={'display': 'flex', 'gap': '10px', 'justifyContent': 'center'})
        ])
    ], style={'backgroundColor': 'rgba(233, 245, 233, 0.9)', 'padding': '15px', 'borderRadius': '12px', 'marginTop': '20px'}),
    
    # Modal para fotos
    html.Div(id='photo-modal', style={'display': 'none'}, children=[
        html.Div(style={
            'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.85)', 'zIndex': '1000',
            'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'
        }, children=[
            html.Div(style={
                'backgroundColor': colors['background'], 'padding': '15px',
                'borderRadius': '8px', 'maxWidth': '95%', 'maxHeight': '95%',
                'overflow': 'auto', 'border': f'2px solid {colors["title-color"]}'
            }, children=[
                html.Img(id='modal-image', style={'maxWidth': '100%', 'maxHeight': '80vh'}),
                html.Button("Cerrar", id='close-modal', style={
                    'padding': '8px 16px', 'borderRadius': '6px',
                    'backgroundColor': colors['accent'], 'color': 'white',
                    'border': 'none', 'cursor': 'pointer', 'marginTop': '15px'
                })
            ])
        ])
    ]),
    
    # Almacenamiento
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio'),
    dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 4.5}),
    dcc.Store(id='photo-store')
])

# ==============================================
# CALLBACKS
# ==============================================

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
     Input('year-slider', 'value')],
    [State('selected-municipio', 'data'),
     State('map-center', 'data'),
     State('filtered-data', 'data')]
)
def update_data(tipos, departamentos, anos, selected_municipio, current_map_center, current_data):
    filtered = df[
        (df['Fecha inicio'].dt.year >= anos[0]) & 
        (df['Fecha inicio'].dt.year <= anos[1])
    ]
    
    if tipos:
        filtered = filtered[filtered['Tipo de proyecto'].isin(tipos)]
    if departamentos:
        filtered = filtered[filtered['Departamento'].isin([normalize_name(d) for d in departamentos])]
    
    filtered = filtered[filtered['Municipio_Depto'].isin(municipios_gdf['Municipio_Depto'])]
    
    # Merge con geometrías
    merged = pd.merge(
        filtered,
        municipios_gdf[['Municipio_Depto', 'geometry', 'lon', 'lat']],
        on='Municipio_Depto',
        how='left'
    )
    filtered_gdf = gpd.GeoDataFrame(merged)
    
    # Manejar centro del mapa
    ctx = callback_context
    if not ctx.triggered or filtered_gdf.empty:
        map_center = current_map_center
    elif selected_municipio and any(t['prop_id'] == 'selected-municipio.data' for t in ctx.triggered):
        municipio_data = filtered_gdf[filtered_gdf['Municipio'] == selected_municipio].iloc[0]
        bbox = get_municipio_bbox(selected_municipio, municipio_data['Departamento'])
        map_center = bbox if bbox else current_map_center
    else:
        map_center = current_map_center
    
    # Crear mapa
    if filtered_gdf.empty:
        fig = px.choropleth_mapbox(
            center={"lat": 4.6, "lon": -74.1}, zoom=4.5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            annotations=[dict(
                text="No hay datos con los filtros actuales",
                x=0.5, y=0.5, showarrow=False, font=dict(size=20)
            )]
        )
    else:
        fig = px.choropleth_mapbox(
            filtered_gdf,
            geojson=filtered_gdf.geometry,
            locations=filtered_gdf.index,
            color="Tipo de proyecto",
            center={"lat": map_center['lat'], "lon": map_center['lon']},
            zoom=map_center['zoom'],
            custom_data=['Municipio', 'Departamento', 'Tipo de proyecto', 'ID']
        )
        
        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>Departamento: %{customdata[1]}<br>Proyecto: %{customdata[2]}"
        )
        
        if selected_municipio:
            selected_data = filtered_gdf[filtered_gdf['Municipio'] == selected_municipio]
            if not selected_data.empty:
                fig.add_trace(
                    px.choropleth_mapbox(
                        selected_data,
                        geojson=selected_data.geometry,
                        locations=selected_data.index,
                        color_discrete_sequence=[colors['map-highlight']]
                    ).update_traces(
                        hovertemplate=None, hoverinfo='skip'
                    ).data[0]
                )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False
    )
    
    return (
        filtered.to_dict('records'),
        len(filtered),
        f"${filtered['Costo total ($COP)'].sum()/1000000:,.0f}M",
        f"{filtered['Beneficiarios totales'].sum():,}",
        f"{filtered['Área intervenida (ha)'].sum():,.1f} ha",
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
            'textAlign': 'center', 'color': 'white', 'padding': '15px'
        })
    
    filtered_df = pd.DataFrame(filtered_data)
    municipios = filtered_df['Municipio'].unique()
    
    cards = []
    for municipio in sorted(municipios):
        count = len(filtered_df[filtered_df['Municipio'] == municipio])
        is_selected = municipio == selected_municipio
        
        card_style = styles['municipio-card-selected'] if is_selected else styles['municipio-card']
        
        cards.append(
            html.Div(
                [
                    html.Div(municipio, style={
                        'fontWeight': '600', 'textAlign': 'center',
                        'color': 'white' if is_selected else '#333333'
                    }),
                    html.Div(f"{count} proyecto{'s' if count > 1 else ''}", style={
                        'textAlign': 'center',
                        'backgroundColor': 'rgba(255,255,255,0.3)' if is_selected else '#e6f3ff',
                        'color': 'white' if is_selected else colors['panel-municipios'],
                        'padding': '4px 8px', 'borderRadius': '12px'
                    })
                ],
                id={'type': 'municipio-card', 'index': municipio},
                style=card_style,
                n_clicks=0
            )
        )
    
    return cards if cards else html.Div("No hay municipios con los filtros actuales", style={
        'textAlign': 'center', 'color': 'white', 'padding': '15px'
    })

@app.callback(
    [Output('selected-municipio', 'data'),
     Output('municipio-value', 'children'),
     Output('beneficiarios-value', 'children'),
     Output('financiador-value', 'children'),
     Output('duracion-value', 'children'),
     Output('area-value', 'children'),
     Output('producto-value', 'children'),
     Output('proyecto-selector', 'options'),
     Output('proyecto-selector', 'value'),
     Output('photo-buttons', 'children'),
     Output('photo-store', 'data')],
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State('filtered-data', 'data'),
     State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def handle_selection(clicks, map_click, filtered_data, municipio_ids):
    ctx = callback_context
    if not ctx.triggered or not filtered_data:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point:
                municipio = point['customdata'][0]
            else:
                return [dash.no_update] * 11
        else:
            return [dash.no_update] * 11
    else:
        municipio = json.loads(trigger_id.split('.')[0].replace("'", '"'))['index']
    
    filtered_df = pd.DataFrame(filtered_data)
    municipio_data = filtered_df[filtered_df['Municipio'] == municipio].iloc[0]
    
    proyectos_options = [{'label': f"Proyecto {row['ID']}", 'value': row['ID']} 
                        for _, row in filtered_df[filtered_df['Municipio'] == municipio].iterrows()]
    
    foto_data = []
    buttons = []
    for i in [1, 2]:
        foto_path = f"assets/fotos/Rf {i} proyecto {municipio_data['ID']}.jpg"
        if os.path.exists(foto_path):
            encoded_image = encode_image(foto_path)
            foto_data.append({'photo_num': i, 'image': encoded_image})
            buttons.append(
                html.Button(
                    f"Evidencia {i}",
                    id={'type': 'photo-button', 'index': i},
                    n_clicks=0,
                    style={
                        'padding': '8px 12px', 'borderRadius': '6px',
                        'backgroundColor': colors['accent'], 'color': 'white',
                        'border': 'none', 'cursor': 'pointer'
                    }
                )
            )
    
    return [
        municipio,
        municipio,
        f"{municipio_data['Beneficiarios totales']:,}",
        municipio_data['Entidad financiadora'],
        f"{municipio_data['Duración del proyecto (meses)']}",
        f"{municipio_data['Área intervenida (ha)']:,.1f}",
        municipio_data['Producto principal generado'],
        proyectos_options,
        municipio_data['ID'] if proyectos_options else None,
        buttons,
        foto_data
    ]

@app.callback(
    Output('photo-modal', 'style'),
    [Input({'type': 'photo-button', 'index': ALL}, 'n_clicks'),
     Input('close-modal', 'n_clicks')],
    [State('photo-store', 'data')]
)
def toggle_modal(photo_clicks, close_click, foto_data):
    ctx = callback_context
    if not ctx.triggered:
        return {'display': 'none'}
    
    if 'close-modal' in ctx.triggered[0]['prop_id']:
        return {'display': 'none'}
    
    if foto_data and any(photo_clicks):
        button_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
        return {'display': 'flex'}
    
    return {'display': 'none'}

@app.callback(
    Output('modal-image', 'src'),
    [Input({'type': 'photo-button', 'index': ALL}, 'n_clicks')],
    [State('photo-store', 'data')]
)
def update_modal_image(photo_clicks, foto_data):
    ctx = callback_context
    if not ctx.triggered or not foto_data:
        raise PreventUpdate
    
    button_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
    for foto in foto_data:
        if foto['photo_num'] == button_id['index']:
            return foto['image']
    
    raise PreventUpdate

# ==============================================
# EJECUCIÓN DE LA APLICACIÓN
# ==============================================

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
