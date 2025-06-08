# -*- coding: utf-8 -*-
"""
Dashboard de Proyectos Fundación AIP - Versión Móvil con Manejo de Errores
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

# Carga de datos con manejo robusto de errores
def cargar_datos():
    try:
        # Cargar datos de proyectos
        df = pd.read_excel("data/proyectos.xlsx")
        
        # Verificar columnas esenciales
        columnas_requeridas = {
            'Fecha inicio': 'convertir a datetime',
            'Fecha fin': 'convertir a datetime',
            'Beneficiarios directos': 'sumar con indirectos',
            'Beneficiarios indirectos': 'sumar con directos',
            'Municipio': 'normalizar texto',
            'Departamento': 'normalizar texto',
            'Tipo de proyecto': 'filtrado',
            'Comunidad beneficiaria': 'filtrado',
            'Costo total ($COP)': 'filtrado',
            'Duración del proyecto (meses)': 'visualización',
            'Entidad financiadora': 'visualización',
            'Área intervenida (ha)': 'visualización'
        }
        
        # Verificar que existan las columnas requeridas
        for col in columnas_requeridas:
            if col not in df.columns:
                raise ValueError(f"Columna requerida faltante: {col}")
        
        # Procesamiento de datos
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
        # Retornar DataFrames vacíos con estructura mínima requerida
        df_fallback = pd.DataFrame(columns=list(columnas_requeridas.keys()) + ['Beneficiarios totales'])
        gdf_fallback = gpd.GeoDataFrame(columns=['MpNombre', 'Depto', 'geometry', 'lon', 'lat'])
        return df_fallback, gdf_fallback, gpd.GeoDataFrame()

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

# 3. Estilos optimizados para móvil (igual que en la versión anterior)
styles = {
    # ... (mantener todos los estilos igual que en la versión anterior)
}

# 4. Layout móvil optimizado (igual que en la versión anterior)
app.layout = html.Div(style={
    'backgroundColor': colors['background'],
    'padding': '5px',
    'margin': '0'
}, children=[
    # ... (mantener todo el layout igual que en la versión anterior)
])

# 5. Callbacks con manejo robusto de errores

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
    
    try:
        # Aplicar filtros con manejo de valores nulos
        filtered = df.copy()
        
        # Filtro de años
        filtered = filtered[
            (filtered['Fecha inicio'].dt.year >= anos[0]) & 
            (filtered['Fecha inicio'].dt.year <= anos[1])
        ]
        
        # Filtro de costos (con verificación de columna)
        if 'Costo total ($COP)' in filtered.columns:
            filtered = filtered[
                (filtered['Costo total ($COP)'] >= costos[0]*1000000) &
                (filtered['Costo total ($COP)'] <= costos[1]*1000000)
            ]
        
        # Filtros adicionales
        if tipos:
            filtered = filtered[filtered['Tipo de proyecto'].isin(tipos)]
        if departamentos:
            filtered = filtered[filtered['Departamento'].isin(departamentos)]
        if comunidades:
            filtered = filtered[filtered['Comunidad beneficiaria'].isin(comunidades)]
        
        # Unir con datos geográficos (con manejo de columnas faltantes)
        geo_columns = ['MpNombre', 'Depto', 'geometry', 'lon', 'lat']
        available_geo_columns = [col for col in geo_columns if col in municipios_gdf.columns]
        
        filtered_with_geom = pd.merge(
            filtered,
            municipios_gdf[available_geo_columns],
            left_on=['Municipio', 'Departamento'],
            right_on=['MpNombre', 'Depto'],
            how='left'
        )
        
        filtered_gdf = gpd.GeoDataFrame(filtered_with_geom)
        filtered_with_geometry = filtered_gdf[~filtered_gdf.geometry.isna()]
        
        # Crear figura del mapa con manejo de datos vacíos
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
            
            # Agregar puntos de ubicaciones AIP si existen
            if not aip_locations_gdf.empty and 'geometry' in aip_locations_gdf.columns:
                fig.add_trace(
                    px.scatter_mapbox(
                        aip_locations_gdf,
                        lat=aip_locations_gdf.geometry.y,
                        lon=aip_locations_gdf.geometry.x,
                        color_discrete_sequence=[colors['aip-locations']]
                    ).update_traces(
                        marker=dict(size=10, opacity=0.8),
                        name="Cobertura AIP",
                        customdata=aip_locations_gdf[["Municipio", "Departamen"]] if "Municipio" in aip_locations_gdf.columns else None,
                        hovertemplate="<b>Municipio: %{customdata[0]}</b><br>Departamento: %{customdata[1]}<extra></extra>" if "Municipio" in aip_locations_gdf.columns else "Ubicación AIP<extra></extra>",
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
        
        # Calcular métricas con valores por defecto para columnas faltantes
        total_proyectos = len(filtered)
        
        if 'Costo total ($COP)' in filtered.columns:
            total_inversion = f"${filtered['Costo total ($COP)'].sum()/1000000:,.0f}M"
        else:
            total_inversion = "$N/A"
            
        if 'Beneficiarios totales' in filtered.columns:
            total_beneficiarios = f"{filtered['Beneficiarios totales'].sum():,}"
        else:
            total_beneficiarios = "N/A"
            
        if 'Área intervenida (ha)' in filtered.columns:
            total_area = f"{filtered['Área intervenida (ha)'].sum():,.1f} ha"
        else:
            total_area = "N/A ha"
        
        # Opciones para selector de proyectos
        proyecto_options = []
        if not filtered.empty and 'ID' in filtered.columns and 'Municipio' in filtered.columns:
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
    
    except Exception as e:
        print(f"Error en update_data: {str(e)}")
        raise PreventUpdate

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
    
    try:
        filtered_df = pd.DataFrame(filtered_data)
        
        # Verificar si la columna Municipio existe
        if 'Municipio' not in filtered_df.columns:
            return html.Div("Datos no tienen información de municipios", style={
                'textAlign': 'center', 
                'color': 'white'
            })
        
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
    
    except Exception as e:
        print(f"Error en update_municipios_list: {str(e)}")
        return html.Div("Error mostrando municipios", style={
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
    
    try:
        trigger_id = ctx.triggered[0]['prop_id']
        
        if trigger_id == 'mapa.clickData':
            if map_click and map_click['points']:
                point = map_click['points'][0]
                if 'customdata' in point and len(point['customdata']) >= 2:  # Tiene datos de municipio
                    municipio = point['customdata'][0]
                else:  # Es un punto de ubicación AIP
                    municipio = point['customdata'][0] if 'customdata' in point and point['customdata'] else None
            else:
                return [None, "Seleccione", "N/A", "0", "0", "0", "N/A"]
        else:
            municipio = json.loads(trigger_id.split('.')[0].replace("'", '"'))['index']
        
        filtered_df = pd.DataFrame(filtered_data)
        
        # Verificar si el municipio existe en los datos filtrados
        if municipio not in filtered_df['Municipio'].values:
            return [None, "Seleccione", "N/A", "0", "0", "0", "N/A"]
        
        municipio_data = filtered_df[filtered_df['Municipio'] == municipio]
        
        if not municipio_data.empty:
            proyecto_data = municipio_data.iloc[0]
            
            # Obtener valores con manejo de columnas faltantes
            financiador = proyecto_data.get('Entidad financiadora', 'N/A')
            duracion = proyecto_data.get('Duración del proyecto (meses)', '0')
            beneficiarios = f"{proyecto_data.get('Beneficiarios totales', 0):,}"
            area = f"{proyecto_data.get('Área intervenida (ha)', 0):,}"
            producto = proyecto_data.get('Producto', 'N/A')
            
            return [
                municipio,
                municipio,
                financiador,
                str(duracion),
                beneficiarios,
                area,
                producto
            ]
        
        return [None, "Seleccione", "N/A", "0", "0", "0", "N/A"]
    
    except Exception as e:
        print(f"Error en update_municipio_info: {str(e)}")
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
    
    try:
        filtered_df = pd.DataFrame(filtered_data)
        proyecto = filtered_df[filtered_df['ID'] == proyecto_id]
        
        if proyecto.empty:
            return []
        
        # Manejo seguro de columnas de fotos
        if 'Fotografías' not in proyecto.columns:
            return [html.Div("No hay fotografías disponibles", style={'textAlign': 'center'})]
        
        fotos = proyecto['Fotografías'].iloc[0]
        if pd.isna(fotos) or not fotos:
            return [html.Div("No hay fotografías disponibles", style={'textAlign': 'center'})]
        
        # Suponiendo que las fotos están en una cadena separada por comas
        fotos_list = [foto.strip() for foto in fotos.split(',') if foto.strip()]
        
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
    
    except Exception as e:
        print(f"Error en update_photo_buttons: {str(e)}")
        return [html.Div("Error cargando fotografías", style={'textAlign': 'center'})]

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
    
    try:
        photo_id = json.loads(ctx.triggered[0]['prop_id'].split('.')[0].replace("'", '"'))['index']
        
        # Aquí deberías implementar la lógica para obtener la imagen real
        # Por ahora simulamos con una imagen codificada
        return {'display': 'block'}, huella_encoded  # Reemplazar con la foto real
    
    except Exception as e:
        print(f"Error en show_photo: {str(e)}")
        raise PreventUpdate

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
