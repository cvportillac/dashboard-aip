# -*- coding: utf-8 -*-
"""
Dashboard de Proyectos Fundación AIP - Versión Móvil
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
app = Dash(__name__, 
           title="Dashboard Fundación AIP", 
           suppress_callback_exceptions=True,
           meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}])
server = app.server

# Carga de datos
shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
municipios_gdf = gpd.read_file(shapefile_path)

aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
aip_locations_gdf = gpd.read_file(aip_locations_path)

# Cargar y codificar imágenes
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
    
    # Normalizar nombres para coincidencia
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
        'maxWidth': '100%',
        'margin': '0 auto',
        'padding': '10px',
        'fontFamily': '"Segoe UI", sans-serif',
        'backgroundColor': colors['background']
    },
    'header': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'marginBottom': '5px',
        'fontWeight': '600',
        'fontSize': '24px'
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
        'margin': '5px 0'
    },
    'logo': {
        'height': '80px',
        'margin': '5px',
        'objectFit': 'contain'
    },
    'huella-img': {
        'height': '50px',
        'marginLeft': '5px'
    },
    'section-title': {
        'textAlign': 'left',
        'color': colors['title-color'],
        'margin': '10px 0 5px 0',
        'fontWeight': '600',
        'fontSize': '18px',
        'paddingLeft': '10px',
        'borderLeft': f'3px solid {colors["title-color"]}'
    },
    'filters': {
        'backgroundColor': 'rgba(233, 245, 233, 0.9)',
        'padding': '10px',
        'borderRadius': '8px',
        'marginBottom': '10px'
    },
    'map-container': {
        'height': '400px',
        'marginBottom': '10px',
        'borderRadius': '8px',
        'overflow': 'hidden'
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
        'cursor': 'pointer'
    },
    'municipio-name': {
        'fontWeight': '600',
        'fontSize': '16px',
        'textAlign': 'center',
        'marginBottom': '5px'
    },
    'municipio-projects': {
        'fontSize': '14px',
        'textAlign': 'center',
        'backgroundColor': '#e6f3ff',
        'padding': '4px 8px',
        'borderRadius': '12px'
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
        'backgroundColor': colors['panel-general'],
        'minHeight': '80px'
    },
    'info-title': {
        'fontSize': '14px',
        'fontWeight': '600',
        'color': colors['title-color'],
        'textAlign': 'center',
        'marginBottom': '5px'
    },
    'info-value': {
        'fontSize': '16px',
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
        'marginBottom': '10px',
        'fontSize': '14px'
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
app.layout = html.Div(style=styles['container'], children=[
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
            marks={i: {'label': f"{i}", 'style': {'fontSize': '12px'}} for i in range(0, 7001, 1000)},
            step=50,
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        html.Label("RANGO DE AÑOS", style=styles['filter-label']),
        dcc.RangeSlider(
            id='year-slider',
            min=df['Fecha inicio'].dt.year.min(),
            max=df['Fecha inicio'].dt.year.max(),
            value=[df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()],
            marks={str(year): {'label': str(year), 'style': {'fontSize': '12px'}} for year in range(df['Fecha inicio'].dt.year.min(), df['Fecha inicio'].dt.year.max()+1)},
            step=None,
            tooltip={"placement": "bottom", "always_visible": True}
        )
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
        html.Div("MUNICIPIOS CON PROYECTOS", style={'textAlign': 'center', 'color': 'white', 'marginBottom': '10px'}),
        html.Div(id='municipios-cards-container')
    ]),
    
    # Panel de información
    html.Div(style=styles['info-panel'], children=[
        html.Div(style=styles['info-section-specific'], children=[
            html.Div("📍 MUNICIPIO", style=styles['info-title']),
            html.Div(id='municipio-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section-specific'], children=[
            html.Div("🏦 FINANCIADOR", style=styles['info-title']),
            html.Div(id='financiador-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section-specific'], children=[
            html.Div("⏳ DURACIÓN", style=styles['info-title']),
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
    
    # Panel de fotografías
    html.Div(style=styles['photo-panel'], children=[
        html.Div(style=styles['photo-selector-container'], children=[
            html.Div("SELECCIONAR PROYECTO", style=styles['info-title']),
            dcc.Dropdown(
                id='proyecto-selector',
                style=styles['dropdown']
            )
        ]),
        html.Div(style={'marginTop': '10px'}, children=[
            html.Div("EVIDENCIA FOTOGRÁFICA", style=styles['info-title']),
            html.Div(id='photo-buttons', style=styles['photo-button-container'])
        ])
    ]),
    
    # Modal para fotos
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
        'padding': '10px',
        'borderTop': f'1px solid {colors["title-color"]}'
    }, children=[
        html.P("© 2025 Fundación AIP - Todos los derechos reservados"),
        html.P("Datos actualizados al " + datetime.now().strftime("%d/%m/%Y"))
    ]),
    
    # Almacenamiento
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio'),
    dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 5}),
    dcc.Store(id='photo-store')
])

# 5. Callbacks (se mantienen igual que en el original)
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
        return html.Span(selected_municipio, style={'color': colors['map-highlight']})
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
            title="No hay datos con los filtros aplicados",
            center={"lat": 4.6, "lon": -74.1},
            zoom=5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        return (
            [],
            "0",
            "$0M",
            "0",
            "0 ha",
            fig,
            {'lat': 4.6, 'lon': -74.1, 'zoom': 5}
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
        map_center = current_map_center if current_map_center else {'lat': 4.6, 'lon': -74.1, 'zoom': 5}
    
    filtered_with_geometry = filtered_gdf[~filtered_gdf.geometry.isna()]
    
    if filtered_with_geometry.empty:
        fig = px.choropleth_mapbox(
            title="No hay datos geográficos",
            center={"lat": 4.6, "lon": -74.1},
            zoom=5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
    else:
        fig = px.choropleth_mapbox(
            filtered_with_geometry,
            geojson=filtered_with_geometry.geometry.__geo_interface__,
            locations=filtered_with_geometry.index,
            color="Tipo de proyecto",
            center={"lat": map_center['lat'], "lon": map_center['lon']},
            zoom=map_center['zoom'],
            custom_data=['MpNombre', 'Depto', 'Tipo de proyecto', 'ID']
        )
        
        fig.add_trace(
            px.scatter_mapbox(
                aip_locations_gdf,
                lat=aip_locations_gdf.geometry.y,
                lon=aip_locations_gdf.geometry.x,
                color_discrete_sequence=['#FFA500']
            ).update_traces(
                marker=dict(size=10, opacity=0.8),
                name="Cobertura AIP",
                customdata=aip_locations_gdf[["Municipio", "Departamen"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                showlegend=True
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
                            geojson=selected_municipio_geom.geometry.__geo_interface__,
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
            x=1
        )
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
            'color': 'white'
        })
    
    filtered_df = pd.DataFrame(filtered_data)
    municipios = filtered_df['Municipio'].unique()
    
    cards = []
    for municipio in sorted(municipios):
        count = len(filtered_df[filtered_df['Municipio'] == municipio])
        is_selected = municipio == selected_municipio
        
        card_style = styles['municipio-card-selected'] if is_selected else styles['municipio-card']
        name_style = styles['municipio-name']
        count_style = styles['municipio-projects']
        
        if is_selected:
            name_style = {**name_style, 'color': 'white'}
            count_style = {**count_style, 'backgroundColor': 'rgba(255,255,255,0.3)', 'color': 'white'}
        
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
        'color': 'white'
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
     State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def handle_municipio_selection(clicks, map_click, selected_proyecto, filtered_data, municipio_ids):
    ctx = callback_context
    
    if not ctx.triggered or not filtered_data:
        default_styles = [styles['municipio-card'] for _ in municipio_ids] if municipio_ids else []
        return [
            None, "Seleccione", "0", "N/A", "0", "0", "N/A", 
            default_styles,
            [], None, [], None
        ]
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point and len(point['customdata']) == 4:  # Es un polígono
                municipio = point['customdata'][0]
            else:  # Es un punto de ubicación AIP
                municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
        else:
            default_styles = [styles['municipio-card'] for _ in municipio_ids] if municipio_ids else []
            return [
                None, "Seleccione", "0", "N/A", "0", "0", "N/A", 
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
            None, "Seleccione", "0", "N/A", "0", "0", "N/A", 
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
    [State('photo-store', 'data')]
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
    [State('photo-store', 'data')]
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
if __name__ == '__main__':
    app.run_server(debug=True)
