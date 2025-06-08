# -*- coding: utf-8 -*-
"""
Dashboard de Proyectos Fundación AIP - Versión Móvil Completa
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

# Carga de datos optimizada con manejo de errores
def cargar_datos():
    try:
        # Cargar datos de proyectos
        df = pd.read_excel("data/proyectos.xlsx")
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
        df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
        
        # Cargar shapefiles con verificación
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
        
        # Normalización de nombres
        df['Municipio'] = df['Municipio'].str.upper().str.strip()
        df['Departamento'] = df['Departamento'].str.upper().str.strip()
        municipios_gdf['MpNombre'] = municipios_gdf['MpNombre'].str.upper().str.strip()
        municipios_gdf['Depto'] = municipios_gdf['Depto'].str.upper().str.strip()
        
        return df, municipios_gdf, aip_locations_gdf
        
    except Exception as e:
        print(f"Error cargando datos: {str(e)}")
        # Retornar DataFrames vacíos para evitar caída de la app
        return pd.DataFrame(), gpd.GeoDataFrame(), gpd.GeoDataFrame()

# Cargar datos
df, municipios_gdf, aip_locations_gdf = cargar_datos()

# Codificación de imágenes con verificación
def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        print(f"Error cargando imagen {image_path}: {str(e)}")
        return None

logo_encoded = encode_image("assets/logo.png")
huella_encoded = encode_image("assets/Figura_huella_aip.png")

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

# 5. Callbacks para funcionalidad completa

@app.callback(
    [Output('filtered-data', 'data'),
     Output('total-proyectos', 'children'),
     Output('total-inversion', 'children'),
     Output('total-beneficiarios', 'children'),
     Output('total-area', 'children'),
     Output('mapa', 'figure'),
     Output('proyecto-selector', 'options')],
    [Input('tipo-dropdown', 'value'),
     Input('departamento-dropdown', 'value'),
     Input('comunidad-dropdown', 'value'),
     Input('costo-slider', 'value'),
     Input('year-slider', 'value')]
)
def update_data(tipos, departamentos, comunidades, costos, anos):
    if df.empty:
        raise PreventUpdate
    
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
            zoom=4.5,
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
                color_discrete_sequence=[colors['aip-locations']]
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
            zoom=4.5
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
    
    # Opciones para selector de proyectos
    proyecto_options = [{'label': f"{row['ID']} - {row['Municipio']}", 'value': row['ID']} 
                       for _, row in filtered.iterrows()]
    
    return (
        filtered.to_dict('records'),
        total_proyectos,
        total_inversion,
        total_beneficiarios,
        total_area,
        fig,
        proyecto_options
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
     Output('beneficiarios-value', 'children'),
     Output('area-value', 'children'),
     Output('producto-value', 'children')],
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State('filtered-data', 'data'),
     State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def update_municipio_info(clicks, map_click, filtered_data, municipio_ids):
    ctx = callback_context
    if not ctx.triggered or not filtered_data:
        return [None, "Seleccione", "N/A", "0", "0", "0", "N/A"]
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point and len(point['customdata']) == 4:  # Es un polígono
                municipio = point['customdata'][0]
            else:  # Es un punto de ubicación AIP
                municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
        else:
            return [None, "Seleccione", "N/A", "0", "0", "0", "N/A"]
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
            f"{proyecto_data['Beneficiarios totales']:,}",
            f"{proyecto_data['Área intervenida (ha)']:,}",
            proyecto_data['Producto']
        ]
    
    return [None, "Seleccione", "N/A", "0", "0", "0", "N/A"]

@app.callback(
    Output('photo-buttons', 'children'),
    [Input('proyecto-selector', 'value'),
     Input('photo-store', 'data')],
    [State('filtered-data', 'data')]
)
def update_photo_buttons(proyecto_id, photo_data, filtered_data):
    if not proyecto_id or not filtered_data:
        return []
    
    filtered_df = pd.DataFrame(filtered_data)
    proyecto = filtered_df[filtered_df['ID'] == proyecto_id]
    
    if proyecto.empty:
        return []
    
    fotos = proyecto['Fotografías'].iloc[0]
    if pd.isna(fotos) or not fotos:
        return [html.Div("No hay fotografías disponibles", style={'textAlign': 'center'})]
    
    # Suponiendo que las fotos están en una cadena separada por comas
    fotos_list = [foto.strip() for foto in fotos.split(',')]
    
    buttons = []
    for i, foto in enumerate(fotos_list):
        buttons.append(
            html.Button(
                f"Foto {i+1}",
                id={'type': 'photo-button', 'index': foto},
                style=styles['photo-button']
            )
        )
    
    return buttons if buttons else [html.Div("No hay fotografías disponibles", style={'textAlign': 'center'})]

@app.callback(
    [Output('photo-modal', 'style'),
     Output('modal-image', 'src')],
    [Input({'type': 'photo-button', 'index': ALL}, 'n_clicks')],
    prevent_initial_call=True
)
def show_photo(clicks):
    if not any(clicks):
        raise PreventUpdate
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    photo_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0].replace("'", '"'))['index']
    
    # Aquí deberías implementar la lógica para obtener la imagen real
    # Por ahora simulamos con una imagen codificada
    return {'display': 'block'}, huella_encoded  # Reemplazar con la foto real

@app.callback(
    Output('photo-modal', 'style', allow_duplicate=True),
    Input('close-modal', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(n_clicks):
    if n_clicks:
        return {'display': 'none'}
    raise PreventUpdate

# 6. Ejecutar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)
