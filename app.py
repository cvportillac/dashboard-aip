# -*- coding: utf-8 -*-
"""
Dashboard de Proyectos Fundación AIP - Versión Móvil Funcional con Datos Reales
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
from shapely.geometry import Polygon, Point
import base64

# 1. Configuración inicial móvil
app = Dash(__name__, 
           title="Dashboard Fundación AIP", 
           suppress_callback_exceptions=True, 
           meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}])
server = app.server

# Carga de datos reales
def cargar_datos_reales():
    # Cargar datos de proyectos (ajustar la ruta según tu estructura)
    try:
        df = pd.read_excel("data/proyectos.xlsx")
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
        df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
        
        # Cargar shapefiles (ajustar rutas según tu estructura)
        municipios_gdf = gpd.read_file("data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp")
        aip_locations_gdf = gpd.read_file("data/shapefiles/cobertura_trabajo_aip.shp")
        
        # Proyección de coordenadas
        if municipios_gdf.crs != "EPSG:4326":
            municipios_gdf = municipios_gdf.to_crs("EPSG:4326")
        if aip_locations_gdf.crs != "EPSG:4326":
            aip_locations_gdf = aip_locations_gdf.to_crs("EPSG:4326")
            
        # Calcular centroides
        municipios_gdf_projected = municipios_gdf.to_crs("EPSG:3116")
        municipios_gdf_projected['centroid'] = municipios_gdf_projected.geometry.centroid
        municipios_gdf['lon'] = municipios_gdf_projected.centroid.map(lambda p: p.x)
        municipios_gdf['lat'] = municipios_gdf_projected.centroid.map(lambda p: p.y)
        
        # Normalizar nombres para coincidencia
        df['Municipio'] = df['Municipio'].str.upper().str.strip()
        df['Departamento'] = df['Departamento'].str.upper().str.strip()
        municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].str.upper().str.strip()
        municipios_gdf['Depto'] = municipios_gdf['Depto'].str.upper().str.strip()
        
        return df, municipios_gdf, aip_locations_gdf
        
    except Exception as e:
        print(f"Error cargando datos: {str(e)}")
        raise PreventUpdate

# Cargar datos reales
try:
    df, municipios_gdf, aip_locations_gdf = cargar_datos_reales()
except:
    df = pd.DataFrame()
    municipios_gdf = gpd.GeoDataFrame()
    aip_locations_gdf = gpd.GeoDataFrame()

# Codificar imágenes reales
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    except:
        return None

logo_encoded = encode_image("assets/logo.png")
huella_encoded = encode_image("assets/Figura_huella_aip.png")

# 2. Esquema de colores optimizado
colors = {
    'background': '#e8f5e9',
    'text': '#333333',
    'primary': '#2e5d2e',
    'panel-general': 'rgba(72, 139, 72, 0.8)',
    'panel-municipios': 'rgba(139, 90, 43, 0.8)',
    'title-color': '#2e7d32',
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
        'padding': '5px',
        'fontFamily': '"Segoe UI", sans-serif',
        'backgroundColor': colors['background']
    },
    'header': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'margin': '5px 0',
        'fontWeight': '600',
        'fontSize': '20px'
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
        'height': '60px',
        'margin': '5px'
    },
    'huella-img': {
        'height': '40px',
        'marginLeft': '5px'
    },
    'section-title': {
        'textAlign': 'left',
        'color': colors['title-color'],
        'margin': '10px 0 5px 0',
        'fontWeight': '600',
        'fontSize': '16px',
        'paddingLeft': '8px',
        'borderLeft': f'3px solid {colors["title-color"]}'
    },
    'filters': {
        'backgroundColor': 'rgba(233, 245, 233, 0.9)',
        'padding': '8px',
        'borderRadius': '8px',
        'marginBottom': '10px'
    },
    'map-container': {
        'height': '300px',
        'backgroundColor': 'white',
        'borderRadius': '8px',
        'marginBottom': '10px'
    },
    'municipios-list': {
        'height': '200px',
        'overflowY': 'auto',
        'padding': '8px',
        'backgroundColor': colors['panel-municipios'],
        'borderRadius': '8px',
        'marginBottom': '10px'
    },
    'municipio-card': {
        'padding': '8px',
        'marginBottom': '6px',
        'borderRadius': '6px',
        'backgroundColor': colors['card-bg'],
        'cursor': 'pointer'
    },
    'municipio-card-selected': {
        'padding': '8px',
        'marginBottom': '6px',
        'borderRadius': '6px',
        'backgroundColor': colors['selected-card-bg'],
        'color': 'white',
        'cursor': 'pointer'
    },
    'municipio-name': {
        'fontWeight': '600',
        'fontSize': '14px',
        'textAlign': 'center',
        'marginBottom': '4px'
    },
    'municipio-projects': {
        'fontSize': '12px',
        'textAlign': 'center',
        'backgroundColor': '#e6f3ff',
        'padding': '3px 6px',
        'borderRadius': '10px'
    },
    'info-panel': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': '8px',
        'marginBottom': '10px'
    },
    'info-section-specific': {
        'padding': '8px',
        'borderRadius': '6px',
        'backgroundColor': colors['panel-general'],
        'minHeight': '70px'
    },
    'info-title': {
        'fontSize': '12px',
        'fontWeight': '600',
        'color': colors['title-color'],
        'textAlign': 'center',
        'marginBottom': '4px'
    },
    'info-value': {
        'fontSize': '14px',
        'fontWeight': '600',
        'textAlign': 'center'
    },
    'filter-label': {
        'fontWeight': '600',
        'marginBottom': '4px',
        'color': colors['title-color'],
        'fontSize': '12px'
    },
    'dropdown': {
        'width': '100%',
        'marginBottom': '8px',
        'fontSize': '12px'
    },
    'summary': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': '8px',
        'marginBottom': '10px'
    },
    'card': {
        'backgroundColor': colors['panel-general'],
        'borderRadius': '6px',
        'padding': '8px',
        'minHeight': '70px'
    },
    'kpi-title': {
        'fontSize': '12px',
        'marginBottom': '4px',
        'color': colors['title-color'],
        'fontWeight': '600'
    },
    'kpi-value': {
        'fontSize': '16px',
        'fontWeight': '700'
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
            options=[{'label': t, 'value': t} for t in sorted(df['Tipo de proyecto'].unique())] if not df.empty else [],
            multi=True,
            placeholder="Seleccione tipos...",
            style=styles['dropdown']
        ),
        html.Label("DEPARTAMENTO", style=styles['filter-label']),
        dcc.Dropdown(
            id='departamento-dropdown',
            options=[{'label': d, 'value': d} for d in sorted(df['Departamento'].unique())] if not df.empty else [],
            multi=True,
            placeholder="Seleccione departamentos...",
            style=styles['dropdown']
        ),
        html.Label("COMUNIDAD BENEFICIARIA", style=styles['filter-label']),
        dcc.Dropdown(
            id='comunidad-dropdown',
            options=[{'label': c, 'value': c} for c in sorted(df['Comunidad beneficiaria'].unique())] if not df.empty else [],
            multi=True,
            placeholder="Seleccione comunidades...",
            style=styles['dropdown']
        ),
        html.Label("RANGO DE AÑOS", style=styles['filter-label']),
        dcc.RangeSlider(
            id='year-slider',
            min=df['Fecha inicio'].dt.year.min() if not df.empty else 2020,
            max=df['Fecha inicio'].dt.year.max() if not df.empty else 2025,
            value=[df['Fecha inicio'].dt.year.min() if not df.empty else 2020, 
                   df['Fecha inicio'].dt.year.max() if not df.empty else 2025],
            marks={str(year): str(year) for year in 
                   range(df['Fecha inicio'].dt.year.min() if not df.empty else 2020, 
                         df['Fecha inicio'].dt.year.max()+1 if not df.empty else 2026)},
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
        html.Div("MUNICIPIOS CON PROYECTOS", style={'textAlign': 'center', 'color': 'white', 'marginBottom': '8px'}),
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
        ])
    ]),
    
    # Almacenamiento
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio'),
    dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 5})
])

# 5. Callbacks para la funcionalidad con datos reales
@app.callback(
    [Output('filtered-data', 'data'),
     Output('total-proyectos', 'children'),
     Output('total-inversion', 'children'),
     Output('total-beneficiarios', 'children'),
     Output('total-area', 'children'),
     Output('mapa', 'figure')],
    [Input('tipo-dropdown', 'value'),
     Input('departamento-dropdown', 'value'),
     Input('comunidad-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_data(tipos, departamentos, comunidades, anos):
    if df.empty:
        raise PreventUpdate
    
    filtered = df[
        (df['Fecha inicio'].dt.year >= anos[0]) & 
        (df['Fecha inicio'].dt.year <= anos[1])
    ]
    
    if tipos:
        filtered = filtered[filtered['Tipo de proyecto'].isin(tipos)]
    if departamentos:
        filtered = filtered[filtered['Departamento'].isin(departamentos)]
    if comunidades:
        filtered = filtered[filtered['Comunidad beneficiaria'].isin(comunidades)]
    
    # Unir con datos geográficos
    filtered_with_geom = pd.merge(
        filtered,
        municipios_gdf[['MpNombre', 'Depto', 'geometry', 'lon', 'lat']],
        left_on=['Municipio', 'Departamento'],
        right_on=['MpNombre', 'Depto'],
        how='left'
    )
    
    filtered_gdf = gpd.GeoDataFrame(filtered_with_geom)
    filtered_with_geometry = filtered_gdf[~filtered_gdf.geometry.isna()]
    
    # Crear figura del mapa
    if not filtered_with_geometry.empty:
        fig = px.choropleth_mapbox(
            filtered_with_geometry,
            geojson=filtered_with_geometry.geometry.__geo_interface__,
            locations=filtered_with_geometry.index,
            color="Tipo de proyecto",
            center={"lat": 4.6, "lon": -74.1},
            zoom=5,
            mapbox_style="carto-positron",
            opacity=0.8,
            custom_data=['MpNombre', 'Depto', 'Tipo de proyecto', 'ID']
        )
        
        # Agregar puntos de ubicaciones AIP
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
                hovertemplate="<b>Municipio: %{customdata[0]}</b><br>Departamento: %{customdata[1]}<extra></extra>",
                showlegend=True
            ).data[0]
        )
    else:
        fig = px.choropleth_mapbox(
            title="No hay datos geográficos",
            center={"lat": 4.6, "lon": -74.1},
            zoom=5
        )
    
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        clickmode='event+select'
    )
    
    total_proyectos = len(filtered)
    total_inversion = f"${filtered['Costo total ($COP)'].sum()/1000000:,.0f}M" if not filtered.empty else "$0M"
    total_beneficiarios = f"{filtered['Beneficiarios totales'].sum():,}" if not filtered.empty else "0"
    total_area = f"{filtered['Área intervenida (ha)'].sum():,.1f} ha" if not filtered.empty else "0 ha"
    
    return (
        filtered.to_dict('records'),
        total_proyectos,
        total_inversion,
        total_beneficiarios,
        total_area,
        fig
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
     Output('financiador-value', 'children'),
     Output('duracion-value', 'children'),
     Output('beneficiarios-value', 'children')],
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State('filtered-data', 'data'),
     State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def update_municipio_info(clicks, map_click, filtered_data, municipio_ids):
    ctx = callback_context
    if not ctx.triggered or not filtered_data:
        return [None, "Seleccione", "N/A", "0", "0"]
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point and len(point['customdata']) == 4:  # Es un polígono
                municipio = point['customdata'][0]
            else:  # Es un punto de ubicación AIP
                municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
        else:
            return [None, "Seleccione", "N/A", "0", "0"]
    else:
        municipio = json.loads(trigger_id.split('.')[0].replace("'", '"'))['index']
    
    filtered_df = pd.DataFrame(filtered_data)
    municipio_data = filtered_df[filtered_df['Municipio'] == municipio]
    
    if not municipio_data.empty:
        proyecto_data = municipio_data.iloc[0]
        return [
            municipio,
            municipio,
            proyecto_data['Entidad financiadora'],
            f"{proyecto_data['Duración del proyecto (meses)']}",
            f"{proyecto_data['Beneficiarios totales']:,}"
        ]
    
    return [None, "Seleccione", "N/A", "0", "0"]

# 6. Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
