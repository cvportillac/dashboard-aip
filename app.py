# -*- coding: utf-8 -*-
"""
Dashboard de Proyectos Fundación AIP - Versión Corregida
"""

from dash import Dash, dcc, html, Input, Output, State, callback_context, ALL
import pandas as pd
import plotly.express as px
import geopandas as gpd
from datetime import datetime
import json
import os
from dash.exceptions import PreventUpdate
from shapely.geometry import Polygon
import base64

# 1. Configuración inicial
app = Dash(__name__, title="Dashboard de Proyectos Fundación AIP", suppress_callback_exceptions=True)
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

# 2. Esquema de colores
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

# 3. Estilos optimizados
styles = {
    'container': {
        'width': '100%',
        'margin': '0 auto',
        'padding': '10px',
        'fontFamily': '"Segoe UI", sans-serif',
        'backgroundColor': colors['background']
    },
    'header': {
        'textAlign': 'center',
        'color': colors['title-color'],
        'marginBottom': '10px',
        'fontWeight': '600',
        'fontSize': '24px'
    },
    'map-container': {
        'height': '400px',
        'marginBottom': '15px',
        'borderRadius': '8px'
    },
    'municipios-list': {
        'height': '300px',
        'overflowY': 'auto',
        'padding': '10px',
        'backgroundColor': colors['panel-municipios'],
        'borderRadius': '8px',
        'marginBottom': '15px'
    }
}

# 4. Layout de la aplicación
app.layout = html.Div(style=styles['container'], children=[
    html.Div(style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}, children=[
        html.Div("NUESTRA HUELLA EN COLOMBIA", style=styles['header']),
        html.Img(src=huella_encoded, style={'height': '50px', 'marginLeft': '10px'}) if huella_encoded else None
    ]),
    
    html.Img(src=logo_encoded, style={'height': '80px', 'margin': '0 auto', 'display': 'block'}) if logo_encoded else None,
    
    dcc.Store(id='filtered-data'),
    dcc.Store(id='selected-municipio'),
    dcc.Store(id='map-center', data={'lat': 4.6, 'lon': -74.1, 'zoom': 5}),
    dcc.Store(id='photo-store'),
    
    # Mapa
    html.Div(style=styles['map-container'], children=[
        dcc.Graph(
            id='mapa',
            config={'displayModeBar': False},
            style={'height': '100%'}
        )
    ]),
    
    # Lista de municipios
    html.Div(style=styles['municipios-list'], children=[
        html.Div("MUNICIPIOS CON PROYECTOS", style={
            'textAlign': 'center', 
            'color': 'white',
            'marginBottom': '10px',
            'fontWeight': '600'
        }),
        html.Div(id='municipios-cards-container')
    ]),
    
    # Panel de información
    html.Div(id='info-panel', style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(2, 1fr)',
        'gap': '10px',
        'marginBottom': '15px'
    })
])

# 5. Callbacks corregidos

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
        
        card_style = {
            'padding': '10px',
            'marginBottom': '8px',
            'borderRadius': '8px',
            'backgroundColor': colors['selected-card-bg'] if is_selected else colors['card-bg'],
            'cursor': 'pointer',
            'color': 'white' if is_selected else '#333333'
        }
        
        cards.append(
            html.Div(
                [
                    html.Div(municipio, style={
                        'fontWeight': '600',
                        'fontSize': '16px',
                        'textAlign': 'center',
                        'marginBottom': '5px'
                    }),
                    html.Div(f"{count} proyecto{'s' if count > 1 else ''}", style={
                        'fontSize': '14px',
                        'textAlign': 'center',
                        'backgroundColor': 'rgba(255,255,255,0.3)' if is_selected else '#e6f3ff',
                        'padding': '4px 8px',
                        'borderRadius': '12px',
                        'color': 'white' if is_selected else colors['panel-municipios']
                    })
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
     Output('info-panel', 'children')],
    [Input({'type': 'municipio-card', 'index': ALL}, 'n_clicks'),
     Input('mapa', 'clickData')],
    [State('filtered-data', 'data'),
     State({'type': 'municipio-card', 'index': ALL}, 'id')]
)
def handle_municipio_selection(clicks, map_click, filtered_data, municipio_ids):
    ctx = callback_context
    
    if not ctx.triggered or not filtered_data:
        return [None, []]
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    if trigger_id == 'mapa.clickData':
        if map_click and map_click['points']:
            point = map_click['points'][0]
            if 'customdata' in point and len(point['customdata']) == 4:  # Es un polígono
                municipio = point['customdata'][0]
            else:  # Es un punto de ubicación AIP
                municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
        else:
            return [None, []]
    else:
        municipio = json.loads(trigger_id.split('.')[0].replace("'", '"'))['index']
    
    filtered_df = pd.DataFrame(filtered_data)
    municipio_data = filtered_df[filtered_df['Municipio'] == municipio]
    
    if municipio_data.empty:
        return [None, []]
    
    proyecto_data = municipio_data.iloc[0]
    
    info_panel = [
        html.Div(style={
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': colors['panel-general']
        }, children=[
            html.Div("📍 MUNICIPIO", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': colors['title-color'],
                'textAlign': 'center',
                'marginBottom': '5px'
            }),
            html.Div(municipio, style={
                'fontSize': '16px',
                'fontWeight': '600',
                'textAlign': 'center'
            })
        ]),
        html.Div(style={
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': colors['panel-general']
        }, children=[
            html.Div("🏦 FINANCIADOR", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': colors['title-color'],
                'textAlign': 'center',
                'marginBottom': '5px'
            }),
            html.Div(proyecto_data['Entidad financiadora'], style={
                'fontSize': '16px',
                'fontWeight': '600',
                'textAlign': 'center'
            })
        ]),
        html.Div(style={
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': colors['panel-general']
        }, children=[
            html.Div("⏳ DURACIÓN", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': colors['title-color'],
                'textAlign': 'center',
                'marginBottom': '5px'
            }),
            html.Div(f"{proyecto_data['Duración del proyecto (meses)']:.1f} meses", style={
                'fontSize': '16px',
                'fontWeight': '600',
                'textAlign': 'center'
            })
        ]),
        html.Div(style={
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': colors['panel-general']
        }, children=[
            html.Div("👥 BENEFICIARIOS", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': colors['title-color'],
                'textAlign': 'center',
                'marginBottom': '5px'
            }),
            html.Div(f"{proyecto_data['Beneficiarios totales']:,}", style={
                'fontSize': '16px',
                'fontWeight': '600',
                'textAlign': 'center'
            })
        ]),
        html.Div(style={
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': colors['panel-general']
        }, children=[
            html.Div("🌳 HECTÁREAS", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': colors['title-color'],
                'textAlign': 'center',
                'marginBottom': '5px'
            }),
            html.Div(f"{proyecto_data['Área intervenida (ha)']:,.1f} ha", style={
                'fontSize': '16px',
                'fontWeight': '600',
                'textAlign': 'center'
            })
        ]),
        html.Div(style={
            'padding': '10px',
            'borderRadius': '8px',
            'backgroundColor': colors['panel-general']
        }, children=[
            html.Div("📦 PRODUCTO", style={
                'fontSize': '14px',
                'fontWeight': '600',
                'color': colors['title-color'],
                'textAlign': 'center',
                'marginBottom': '5px'
            }),
            html.Div(proyecto_data['Producto principal generado'], style={
                'fontSize': '16px',
                'fontWeight': '600',
                'textAlign': 'center'
            })
        ])
    ]
    
    return [municipio, info_panel]

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

if __name__ == '__main__':
    app.run_server(debug=True)
