import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Carga de datos (asumiendo que ya tienes el archivo Excel procesado)
# En un caso real, tendrías que adaptar esto para cargar tus datos
def cargar_datos():
    try:
        # Intenta cargar desde archivo procesado
        df = pd.read_excel("inflacion_procesada.xlsx")
    except:
        '''
        # Si no existe, creamos datos de ejemplo basados en la descripción
        # Esto es solo para demostración
        import numpy as np

        # Crear fechas mensuales
        fechas = pd.date_range(start='1979-01-01', end='2025-01-31', freq='M')
        ciudades = ['Barranquilla', 'Bogotá', 'Bucaramanga', 'Cali', 'Manizales', 'Medellín', 'Pasto']
        
        # Crear DataFrame largo
        data = []
        for ciudad in ciudades:
            # Simulamos tendencias similares a las descritas
            base = 1.0
            for fecha in fechas:
                # Simular crecimiento con aceleración en los 90s y 2021
                if fecha.year < 1990:
                    base *= 1.01  # Crecimiento lento
                elif fecha.year < 2000:
                    base *= 1.015  # Crecimiento acelerado en los 90s
                elif fecha.year < 2020:
                    base *= 1.005  # Crecimiento moderado
                else:
                    base *= 1.01  # Nuevo crecimiento desde 2021
                
                # Añadir variación por ciudad
                factor_ciudad = 1.0 + (ciudades.index(ciudad) - 3) * 0.002
                
                data.append({
                    'Fecha': fecha,
                    'Ciudad': ciudad,
                    'IPC': base * factor_ciudad
                })
        
        df = pd.DataFrame(data)
        
        # Calcular inflación anual
        df = df.sort_values(['Ciudad', 'Fecha'])
        df['Inflacion_Anual'] = df.groupby('Ciudad')['IPC'].pct_change(12) * 100'''
        print("Problemas")
    
    return df

# Inicializar la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server

# Cargar datos
df = cargar_datos()

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Análisis de IPC e Inflación en Colombia"),
    
    html.Div([
        html.Div([
            html.Label("Seleccione una métrica:"),
            dcc.Dropdown(
                id='metrica-dropdown',
                options=[
                    {'label': 'IPC', 'value': 'IPC'},
                    {'label': 'Inflación Anual', 'value': 'Inflacion_Anual'}
                ],
                value='IPC'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'margin-right': '20px'}),
        
        html.Div([
            html.Label("Seleccione ciudades:"),
            dcc.Dropdown(
                id='ciudad-dropdown',
                options=[{'label': ciudad, 'value': ciudad} for ciudad in sorted(df['Ciudad'].unique())],
                value=sorted(df['Ciudad'].unique()),
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'margin-right': '20px'}),
        
        html.Div([
            html.Label("Rango de fechas:"),
            dcc.RangeSlider(
                id='fecha-slider',
                min=df['Fecha'].dt.year.min(),
                max=df['Fecha'].dt.year.max(),
                step=1,
                marks={year: str(year) for year in range(df['Fecha'].dt.year.min(), df['Fecha'].dt.year.max()+1, 5)},
                value=[df['Fecha'].dt.year.max()-10, df['Fecha'].dt.year.max()]
            )
        ], style={'width': '60%', 'padding': '20px 0px'})
    ]),
    
    dcc.Graph(id='main-graph'),
    
    html.Div([
        html.H3("Estadísticas descriptivas"),
        html.Div(id='stats-table')
    ])
])

# Callbacks
@app.callback(
    [Output('main-graph', 'figure'),
     Output('stats-table', 'children')],
    [Input('metrica-dropdown', 'value'),
     Input('ciudad-dropdown', 'value'),
     Input('fecha-slider', 'value')]
)
def update_graph(metrica, ciudades, rango_anos):
    # Filtrar datos
    filtro_fecha = (df['Fecha'].dt.year >= rango_anos[0]) & (df['Fecha'].dt.year <= rango_anos[1])
    filtro_ciudad = df['Ciudad'].isin(ciudades)
    df_filtrado = df[filtro_fecha & filtro_ciudad]
    
    # Título para la gráfica según la métrica
    titulo = f"Evolución de {'la Inflación Anual' if metrica == 'Inflacion_Anual' else 'el IPC'} por Ciudad ({rango_anos[0]}-{rango_anos[1]})"
    y_label = "Tasa de Inflación (%)" if metrica == 'Inflacion_Anual' else "IPC"
    
    # Crear gráfica
    fig = px.line(
        df_filtrado, 
        x='Fecha', 
        y=metrica, 
        color='Ciudad',
        title=titulo,
        labels={'Fecha': 'Año', metrica: y_label}
    )
    
    # Crear estadísticas personalizadas con valores máximos y mínimos
    stats_list = []
    for ciudad in ciudades:
        df_ciudad = df_filtrado[df_filtrado['Ciudad'] == ciudad]
        
        if not df_ciudad.empty:
            # Encontrar el valor máximo y su fecha
            max_idx = df_ciudad[metrica].idxmax()
            max_valor = df_ciudad.loc[max_idx, metrica]
            max_fecha = df_ciudad.loc[max_idx, 'Fecha']
            
            # Encontrar el valor mínimo y su fecha
            min_idx = df_ciudad[metrica].idxmin()
            min_valor = df_ciudad.loc[min_idx, metrica]
            min_fecha = df_ciudad.loc[min_idx, 'Fecha']
            
            stats_list.append({
                'Ciudad': ciudad,
                'Mes Máximo': max_fecha.strftime('%b %Y'),
                'Valor Máximo': max_valor,
                'Mes Mínimo': min_fecha.strftime('%b %Y'),
                'Valor Mínimo': min_valor
            })
    
    # Convertir a DataFrame para formato tabular
    stats_df = pd.DataFrame(stats_list)
    
    # Formatear valores numéricos
    formato = '.2f' if metrica == 'Inflacion_Anual' else '.4f'
    stats_df['Valor Máximo'] = stats_df['Valor Máximo'].map(lambda x: f"{x:{formato}}")
    stats_df['Valor Mínimo'] = stats_df['Valor Mínimo'].map(lambda x: f"{x:{formato}}")
    
    # Crear tabla HTML
    stats_table = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in stats_df.columns])),
        html.Tbody([
            html.Tr([
                html.Td(stats_df.iloc[i][col]) for col in stats_df.columns
            ]) for i in range(len(stats_df))
        ])
    ], className='table table-striped', style={'width': '100%', 'border': '1px solid', 'margin-top': '10px'})
    
    return fig, stats_table

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True, dev_tools_ui=False)