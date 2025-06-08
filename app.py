# -*- coding: utf-8 -*-
"""
Dashboard Fundación AIP - Versión sin normalización de nombres
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

# Solución para el error de PIL
try:
    from PIL import Image
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

os.environ['USE_PYGEOS'] = '0'

# Configuración inicial
app = Dash(__name__, title="Dashboard Fundación AIP", suppress_callback_exceptions=True)
server = app.server

# Función para codificar imágenes
def encode_image(image_path, mobile=False):
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
        print(f"Error procesando imagen: {e}")
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
    return None

# Carga de datos sin normalización de nombres
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

    # Procesamiento de datos geoespaciales
    if municipios_gdf.crs != "EPSG:4326":
        municipios_gdf = municipios_gdf.to_crs("EPSG:4326")
    if aip_locations_gdf.crs != "EPSG:4326":
        aip_locations_gdf = aip_locations_gdf.to_crs("EPSG:4326")

    municipios_gdf_projected = municipios_gdf.to_crs("EPSG:3116")
    municipios_gdf_projected['centroid'] = municipios_gdf_projected.geometry.centroid
    municipios_gdf['lon'] = municipios_gdf_projected.centroid.map(lambda p: p.x)
    municipios_gdf['lat'] = municipios_gdf_projected.centroid.map(lambda p: p.y)

    # Cargar datos de proyectos sin normalización
    def cargar_base_datos():
        df = pd.read_excel("data/proyectos.xlsx")
        df['Fecha inicio'] = pd.to_datetime(df['Fecha inicio'])
        df['Fecha fin'] = pd.to_datetime(df['Fecha fin'])
        df['Beneficiarios totales'] = df['Beneficiarios directos'] + df['Beneficiarios indirectos']
        return df

    df = cargar_base_datos()

except Exception as e:
    print(f"Error cargando datos: {e}")
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

# Esquema de colores (igual que antes)
colors = {
    'background': '#e8f5e9',
    'text': '#333333',
    'primary': '#2e5d2e',
    'secondary': '#4a7c4a',
    'accent': '#8b5a2b',
    # ... (resto de colores igual)
}

# Estilos (igual que antes)
styles = {
    'container': {
        'display': 'grid',
        'gridTemplateColumns': '1fr',
        'gap': '15px',
        'width': '100%',
        # ... (resto de estilos igual)
    },
    # ... (todos los demás estilos igual)
}

# Layout (igual que antes)
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'minHeight': '100vh',
    'padding': '10px',
    'margin': '0',
    'overflowX': 'hidden',
    'width': '100%',
    'boxSizing': 'border-box'
}, children=[
    # ... (todo el layout igual)
])

# Callbacks modificados para evitar normalización

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
    
    # Merge sin normalización de nombres
    filtered_with_geom = pd.merge(
        filtered,
        municipios_gdf[['MpNombre', 'Depto', 'geometry', 'lon', 'lat']],
        left_on=['Municipio', 'Departamento'],
        right_on=['MpNombre', 'Depto'],
        how='left'
    )
    
    filtered_gdf = gpd.GeoDataFrame(filtered_with_geom)
    
    # Manejo del zoom automático
    if triggered_input == 'selected-municipio' and selected_municipio and current_filtered_data:
        filtered_df = pd.DataFrame(current_filtered_data)
        municipio_data = filtered_df[filtered_df['Municipio'] == selected_municipio]
        if not municipio_data.empty:
            departamento = municipio_data.iloc[0]['Departamento']
            bbox = get_municipio_bbox(selected_municipio, departamento)
            if bbox:
                map_center = bbox
            else:
                municipio_geom = municipios_gdf[
                    (municipios_gdf['MpNombre'] == selected_municipio) & 
                    (municipios_gdf['Depto'] == departamento)
                ]
                if not municipio_geom.empty:
                    map_center = {
                        'lat': municipio_geom.iloc[0]['lat'],
                        'lon': municipio_geom.iloc[0]['lon'],
                        'zoom': 10
                    }
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
        fig = px.choropleth_mapbox(
            filtered_with_geometry,
            geojson=filtered_with_geometry.geometry,
            locations=filtered_with_geometry.index,
            color="Tipo de proyecto",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            center={"lat": map_center['lat'], "lon": map_center['lon']},
            zoom=map_center['zoom'],
            opacity=0.8,
            custom_data=['Municipio', 'Departamento', 'Tipo de proyecto', 'ID']
        )
        
        fig.update_traces(
            hovertemplate="<b>Municipio: %{customdata[0]}</b><br>Departamento: %{customdata[1]}<br>Proyecto: %{customdata[2]}<br>ID: %{customdata[3]}<extra></extra>"
        )
        
        fig.add_trace(
            px.scatter_mapbox(
                aip_locations_gdf,
                lat=aip_locations_gdf.geometry.y,
                lon=aip_locations_gdf.geometry.x,
                color_discrete_sequence=['#90EE90']
            ).update_traces(
                marker=dict(size=10, opacity=0.8),
                name="Cobertura",
                hovertemplate="<b>Municipio: %{customdata[0]}</b><br>Departamento: %{customdata[1]}<extra></extra>",
                customdata=aip_locations_gdf[["Municipio", "Departamen"]],
                showlegend=True
            ).data[0]
        )
        
        if selected_municipio and current_filtered_data:
            filtered_df = pd.DataFrame(current_filtered_data)
            municipio_data = filtered_df[filtered_df['Municipio'] == selected_municipio]
            if not municipio_data.empty:
                departamento = municipio_data.iloc[0]['Departamento']
                selected_municipio_geom = municipios_gdf[
                    (municipios_gdf['MpNombre'] == selected_municipio) & 
                    (municipios_gdf['Depto'] == departamento)
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

# Función para obtener bbox de municipio
def get_municipio_bbox(municipio_name, departamento_name):
    try:
        municipio = municipios_gdf[
            (municipios_gdf['MpNombre'] == municipio_name) & 
            (municipios_gdf['Depto'] == departamento_name)
        ]
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
        
        zoom = max(8 - max(width, height) * 5, 10)
        
        return {
            'lat': center_lat,
            'lon': center_lon,
            'zoom': zoom
        }
    except Exception as e:
        print(f"Error calculando bbox para {municipio_name}: {e}")
        return None

# Resto de callbacks permanecen igual
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
    Output('municipios-cards-container', 'children'),
    [Input('filtered-data', 'data')],
    [State('selected-municipio', 'data')]
)
def update_municipios_list(filtered_data, selected_municipio):
    if not filtered_data:
        return html.Div("No hay municipios con los filtros actuales", style={
            'textAlign': 'center', 
            'color': 'white', 
            'fontSize': '18px',
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
        'fontSize': '18px',
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
            if 'customdata' in point and len(point['customdata']) >= 4:
                municipio = point['customdata'][0]
            else:
                municipio = None
        else:
            municipio = None
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
                encoded_image = encode_image(foto_path, mobile=True)
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

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
