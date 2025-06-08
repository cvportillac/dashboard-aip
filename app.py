# -*- coding: utf-8 -*-
"""
Dashboard móvil para Fundación AIP - Versión optimizada para dispositivos móviles
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

# 1. Configuración inicial móvil
app = Dash(__name__, title="Dashboard Móvil Fundación AIP", suppress_callback_exceptions=True, meta_tags=[
    {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5'}
])
server = app.server

# Carga de datos
shapefile_path = "data/shapefiles/municipio_distrito_y_area_no_municipalizada.shp"
municipios_gdf = gpd.read_file(shapefile_path)

aip_locations_path = "data/shapefiles/cobertura_trabajo_aip.shp"
aip_locations_gdf = gpd.read_file(aip_locations_path)

# Codificar imágenes
def encode_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    return None

logo_encoded = encode_image("assets/logo.png")
huella_encoded = encode_image("assets/Figura_huella_aip.png")

# Procesamiento de datos geoespaciales
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
    'background': '#f5f5f5',
    'text': '#333333',
    'primary': '#2e5d2e',
    'secondary': '#4a7c4a',
    'accent': '#8b5a2b',
    'panel-general': 'rgba(72, 139, 72, 0.8)',
    'panel-especifico': 'rgba(102, 187, 106, 0.8)',
    'panel-municipios': 'rgba(139, 90, 43, 0.8)',
    'title-color': '#D4AF37',  # Cambiado a dorado
    'gold': '#D4AF37',         # Color dorado añadido
    'card-bg': 'rgba(255, 255, 255, 0.95)',
    'selected-card-bg': '#8B0000',
    'map-highlight': '#8B0000',
    'aip-locations': '#FFA500',
    'filter-bg': 'rgba(233, 245, 233, 0.9)'
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
        'marginBottom': '10px',
        'fontWeight': '700',
        'fontSize': '24px',
        'paddingBottom': '10px',
        'borderBottom': f'2px solid {colors["title-color"]}',
        'textShadow': '0 1px 2px rgba(0,0,0,0.3)'  # Sombra para mejor legibilidad
    },
    'header-container': {
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'marginBottom': '15px'
    },
    'logo': {
        'height': '80px',
        'margin': '5px 0',
        'objectFit': 'contain'
    },
    'huella-img': {
        'height': '60px',
        'marginLeft': '10px'
    },
    'section-title': {
        'textAlign': 'left',
        'color': colors['gold'],  # Cambiado a dorado
        'margin': '10px 0',
        'fontWeight': '600',
        'fontSize': '18px',
        'paddingLeft': '10px',
        'borderLeft': f'3px solid {colors["gold"]}',  # Cambiado a dorado
        'textShadow': '0 1px 1px rgba(0,0,0,0.2)'  # Sombra sutil
    },
    'filters': {
        'backgroundColor': colors['filter-bg'],
        'padding': '10px',
        'borderRadius': '8px',
        'marginBottom': '10px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'map-container': {
        'height': '400px',
        'marginBottom': '10px',
        'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
        'borderRadius': '8px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'municipios-list': {
        'height': '300px',
        'overflowY': 'auto',
        'padding': '10px',
        'backgroundColor': colors['panel-municipios'],
        'borderRadius': '8px',
        'marginBottom': '10px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'municipio-card': {
        'padding': '10px',
        'marginBottom': '8px',
        'borderRadius': '8px',
        'backgroundColor': colors['card-bg'],
        'cursor': 'pointer',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'municipio-card-selected': {
        'padding': '10px',
        'marginBottom': '8px',
        'borderRadius': '8px',
        'backgroundColor': colors['selected-card-bg'],
        'color': 'white',
        'cursor': 'pointer',
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'border': f'2px solid {colors["gold"]}'  # Borde dorado más grueso
    },
    'municipio-name': {
        'fontWeight': '600',
        'fontSize': '16px',
        'marginBottom': '5px',
        'textAlign': 'center',
        'color': colors['gold']  # Texto en dorado
    },
    'municipio-name-selected': {
        'fontWeight': '600',
        'fontSize': '16px',
        'marginBottom': '5px',
        'textAlign': 'center',
        'color': 'white',
        'textShadow': '0 1px 2px rgba(0,0,0,0.5)'
    },
    'municipio-projects': {
        'fontSize': '14px',
        'fontWeight': '600',
        'textAlign': 'center',
        'backgroundColor': '#e6f3ff',
        'color': colors['panel-municipios'],
        'padding': '4px 8px',
        'borderRadius': '12px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'municipio-projects-selected': {
        'fontSize': '14px',
        'fontWeight': '600',
        'textAlign': 'center',
        'backgroundColor': 'rgba(255,255,255,0.3)',
        'color': 'white',
        'padding': '4px 8px',
        'borderRadius': '12px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'municipios-title': {
        'textAlign': 'center',
        'color': colors['gold'],  # Cambiado a dorado
        'fontWeight': '600',
        'fontSize': '16px',
        'marginBottom': '10px',
        'padding': '8px',
        'textShadow': '0 1px 1px rgba(0,0,0,0.3)',
        'borderBottom': f'2px solid {colors["gold"]}'  # Borde inferior dorado
    },
    'info-panel': {
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': '10px',
        'marginBottom': '10px'
    },
    'info-section': {
        'padding': '10px',
        'borderRadius': '8px',
        'backgroundColor': colors['panel-especifico'],
        'minHeight': '80px',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'info-title': {
        'fontSize': '12px',
        'fontWeight': '600',
        'color': colors['gold'],  # Cambiado a dorado
        'marginBottom': '5px',
        'textAlign': 'center',
        'textShadow': '0 1px 1px rgba(0,0,0,0.2)'
    },
    'info-value': {
        'fontSize': '16px',
        'fontWeight': '600',
        'color': 'white',
        'textAlign': 'center'
    },
    'filter-label': {
        'fontWeight': '600',
        'marginBottom': '5px',
        'color': colors['gold'],  # Cambiado a dorado
        'fontSize': '12px',
        'textShadow': '0 1px 1px rgba(0,0,0,0.1)'
    },
    'dropdown': {
        'width': '100%',
        'fontSize': '12px',
        'marginBottom': '10px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'card': {
        'backgroundColor': colors['panel-general'],
        'borderRadius': '8px',
        'padding': '10px',
        'marginBottom': '10px',
        'textAlign': 'center',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'kpi-title': {
        'fontSize': '12px',
        'marginBottom': '5px',
        'color': colors['gold'],  # Cambiado a dorado
        'fontWeight': '600',
        'textShadow': '0 1px 1px rgba(0,0,0,0.2)'
    },
    'kpi-value': {
        'fontSize': '20px',
        'fontWeight': '700',
        'color': 'white'
    },
    'photo-panel': {
        'backgroundColor': colors['filter-bg'],
        'padding': '10px',
        'borderRadius': '8px',
        'marginTop': '10px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'photo-title': {
        'textAlign': 'center',
        'color': colors['gold'],  # Cambiado a dorado
        'fontWeight': '600',
        'fontSize': '14px',
        'marginBottom': '8px',
        'textShadow': '0 1px 1px rgba(0,0,0,0.2)',
        'borderBottom': f'1px solid {colors["gold"]}'  # Borde inferior dorado
    },
    'photo-button': {
        'padding': '6px 12px',
        'borderRadius': '6px',
        'backgroundColor': colors['gold'],  # Fondo dorado
        'color': '#333',  # Texto oscuro para mejor contraste
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '12px',
        'margin': '4px',
        'boxShadow': '0 2px 3px rgba(0,0,0,0.2)'
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
        'width': '90%',
        'maxHeight': '90%',
        'overflow': 'auto',
        'border': f'2px solid {colors["gold"]}'  # Borde dorado
    },
    'modal-image': {
        'width': '100%',
        'borderRadius': '6px',
        'marginBottom': '10px',
        'border': f'1px solid {colors["gold"]}'  # Borde dorado
    },
    'close-button': {
        'padding': '6px 12px',
        'borderRadius': '6px',
        'backgroundColor': colors['gold'],  # Fondo dorado
        'color': '#333',  # Texto oscuro para mejor contraste
        'fontWeight': '600',
        'border': 'none',
        'cursor': 'pointer',
        'fontSize': '12px',
        'width': '100%',
        'boxShadow': '0 2px 3px rgba(0,0,0,0.2)'
    }
}

# 4. Layout móvil (resto del código permanece igual)
app.layout = html.Div(style=styles['container'], children=[
    # Encabezado
    html.Div(style=styles['header-container'], children=[
        html.Div([
            html.Img(src=huella_encoded, style=styles['huella-img']) if huella_encoded else None,
            html.H1("NUESTRA HUELLA EN COLOMBIA", style=styles['header'])
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Img(src=logo_encoded, style=styles['logo']) if logo_encoded else None
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
    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(2, 1fr)', 'gap': '10px'}, children=[
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
    
    # Mapa
    html.Div("UBICACIÓN DE PROYECTOS", style=styles['section-title']),
    html.Div(style=styles['map-container'], children=[
        dcc.Graph(
            id='mapa', 
            config={'displayModeBar': False},
            style={'height': '100%'}
        )
    ]),
    
    # Lista de municipios
    html.Div("MUNICIPIOS CON PROYECTOS", style=styles['section-title']),
    html.Div(style=styles['municipios-list'], children=[
        html.Div("SELECCIONE UN MUNICIPIO", style=styles['municipios-title']),
        html.Div(id='municipios-cards-container')
    ]),
    
    # Panel de información
    html.Div("INFORMACIÓN DEL MUNICIPIO", style=styles['section-title']),
    html.Div(style=styles['info-panel'], children=[
        html.Div(style=styles['info-section'], children=[
            html.Div("📍 MUNICIPIO", style=styles['info-title']),
            html.Div(id='municipio-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section'], children=[
            html.Div("🏦 ENTIDAD FINANCIADORA", style=styles['info-title']),
            html.Div(id='financiador-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section'], children=[
            html.Div("⏳ DURACIÓN (MESES)", style=styles['info-title']),
            html.Div(id='duracion-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section'], children=[
            html.Div("👥 BENEFICIARIOS", style=styles['info-title']),
            html.Div(id='beneficiarios-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section'], children=[
            html.Div("🌳 HECTÁREAS", style=styles['info-title']),
            html.Div(id='area-value', style=styles['info-value'])
        ]),
        html.Div(style=styles['info-section'], children=[
            html.Div("📦 PRODUCTO", style=styles['info-title']),
            html.Div(id='producto-value', style=styles['info-value'])
        ])
    ]),
    
    # Fotografías
    html.Div("EVIDENCIA FOTOGRÁFICA", style=styles['section-title']),
    html.Div(style=styles['photo-panel'], children=[
        html.Div("SELECCIONE UN PROYECTO", style=styles['photo-title']),
        dcc.Dropdown(
            id='proyecto-selector',
            style=styles['dropdown']
        ),
        html.Div(id='photo-buttons', style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})
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
        'color': colors['gold'],  # Cambiado a dorado
        'marginTop': '15px',
        'fontSize': '12px',
        'padding': '10px',
        'borderTop': f'1px solid {colors["gold"]}'  # Borde superior dorado
    }, children=[
        html.P("© 2025 Fundación AIP"),
        html.P(f"Datos actualizados al {datetime.now().strftime('%d/%m/%Y')}")
    ]),
    
    # Almacenamiento
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio'),
    dcc.Store(id='photo-store')
])

# 5. Callbacks (simplificados pero funcionales)
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
     Input('year-slider', 'value'),
     Input('costo-slider', 'value')]
)
def update_data(tipos, departamentos, comunidades, anos, costos):
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
            center={"lat": 4.6, "lon": -74.1},
            zoom=4.5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":0,"l":0,"b":0},
            annotations=[dict(
                text="No hay datos con los filtros aplicados",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14)
            )]
        )
        return [], "0", "$0M", "0", "0 ha", fig
    
    filtered_with_geom = pd.merge(
        filtered,
        municipios_gdf[['MpNombre', 'Depto', 'geometry', 'lon', 'lat']],
        left_on=['Municipio', 'Departamento'],
        right_on=['MpNombre', 'Depto'],
        how='left'
    )
    
    filtered_gdf = gpd.GeoDataFrame(filtered_with_geom)
    filtered_with_geometry = filtered_gdf[~filtered_gdf.geometry.isna()]
    
    if filtered_with_geometry.empty:
        fig = px.choropleth_mapbox(
            center={"lat": 4.6, "lon": -74.1},
            zoom=4.5
        )
        fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r":0,"t":0,"l":0,"b":0},
            annotations=[dict(
                text="No hay datos geográficos",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14)
            )]
        )
    else:
        fig = px.choropleth_mapbox(
            filtered_with_geometry,
            geojson=filtered_with_geometry.geometry,
            locations=filtered_with_geometry.index,
            color="Tipo de proyecto",
            center={"lat": 4.6, "lon": -74.1},
            zoom=4.5,
            opacity=0.7,
            custom_data=['MpNombre', 'Depto', 'Tipo de proyecto', 'ID']
        )
        
        fig.update_traces(
            hovertemplate="<b>%{customdata[0]}</b><br>Depto: %{customdata[1]}<br>Proyecto: %{customdata[2]}"
        )
        
        fig.add_trace(
            px.scatter_mapbox(
                aip_locations_gdf,
                lat=aip_locations_gdf.geometry.y,
                lon=aip_locations_gdf.geometry.x,
                color_discrete_sequence=[colors['aip-locations']]
            ).update_traces(
                marker=dict(size=8),
                name="Cobertura AIP",
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                customdata=aip_locations_gdf[["Municipio", "Departamen"]]
            ).data[0]
        )
    
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0,"t":0,"l":0,"b":0},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
            'color': 'white', 
            'padding': '10px'
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
        'padding': '10px'
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
     Input('mapa', 'clickData'),
     Input('proyecto-selector', 'value')],
    [State('filtered-data', 'data'),
     State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def handle_selection(clicks, map_click, selected_proyecto, filtered_data, municipio_ids):
    ctx = callback_context
    
    if not ctx.triggered or not filtered_data:
        return [None, "Seleccione", "0", "N/A", "0", "0", "N/A", [], None, [], None]
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and 'points' in map_click and map_click['points']:
            point = map_click['points'][0]
            municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
        else:
            return [None, "Seleccione", "0", "N/A", "0", "0", "N/A", [], None, [], None]
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
        return [None, "Seleccione", "0", "N/A", "0", "0", "N/A", [], None, [], None]
    
    proyectos_options = [{'label': f"Proyecto {row['ID']}", 'value': row['ID']} 
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
                        f"Evidencia {i}",
                        id={'type': 'photo-button', 'index': i},
                        n_clicks=0,
                        style=styles['photo-button']
                    )
                )
    
    return [
        municipio, 
        municipio, 
        f"{proyecto_data['Beneficiarios totales']:,}", 
        proyecto_data['Entidad financiadora'], 
        f"{proyecto_data['Duración del proyecto (meses)']:.1f}", 
        f"{proyecto_data['Área intervenida (ha)']:,.1f}", 
        proyecto_data['Producto principal generado'], 
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
    
    if 'close-modal' in ctx.triggered[0]['prop_id']:
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
    app.run(debug=True)
