import speedtest as speedtest
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import threading
import time
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os
import plotly.io as pio

# Variables globales
data = {'time': [], 'download': [], 'upload': [], 'status': []}

# Función para verificar conectividad
def check_connectivity():
    response = os.system("ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1")
    return response == 0

# Función para medir velocidad
def test_speed():
    global data
    while True:
        timestamp = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        if check_connectivity():
            try:
                st = speedtest.Speedtest()
                st.get_best_server()
                download_speed = st.download() / 1_000_000  # Convertir a Mbps
                upload_speed = st.upload() / 1_000_000  # Convertir a Mbps
                status = 'Online'
            except Exception:
                download_speed = 0
                upload_speed = 0
                status = 'Intermitencia'
        else:
            download_speed = 0
            upload_speed = 0
            status = 'Offline'
        
        data['time'].append(timestamp)
        data['download'].append(download_speed)
        data['upload'].append(upload_speed)
        data['status'].append(status)
        
        # Mantener solo los últimos 50 registros
        if len(data['time']) > 50:
            for key in data:
                data[key].pop(0)
        
        time.sleep(10)  # Ejecutar cada 10 segundos

# Iniciar la medición en un hilo
threading.Thread(target=test_speed, daemon=True).start()

# Crear la app Dash
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Monitoreo de Conectividad a Internet"),
    dcc.Graph(id='live-graph'),

    # Campos de fecha para seleccionar el rango
    html.Div([
        dcc.DatePickerRange(
            id='date-picker-range',
            start_date=datetime.datetime.today().strftime('%Y-%m-%d'),
            end_date=datetime.datetime.today().strftime('%Y-%m-%d'),
            display_format='DD/MM/YYYY'
        ),
    ]),

    # Botón para generar el reporte PDF
    html.Button('Generar Reporte PDF', id='generate-pdf-button', n_clicks=0),

    # Zona de mensaje
    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0),
    html.Div(id='status-text', style={'font-size': '20px'})
])

@app.callback(
    [Output('live-graph', 'figure'), Output('status-text', 'children')],
    [Input('interval-component', 'n_intervals')]
)

def update_graph(n):
    if not data['time']:
        return {
            'data': [],
            'layout': go.Layout(title='Velocidad de Internet', xaxis={'title': 'Tiempo'}, yaxis={'title': 'Mbps'})
        }, html.Span("Estado: Desconocido - Última medición: Desconocido", style={'color': 'orange'})

    status = data['status'][-1]
    color = 'green' if status == 'Online' else 'red' if status == 'Offline' else 'orange'
    
    return {
        'data': [
            go.Scatter(x=data['time'], y=data['download'], mode='lines+markers', name='Download (Mbps)', line=dict(color='blue')),
            go.Scatter(x=data['time'], y=data['upload'], mode='lines+markers', name='Upload (Mbps)', line=dict(color='orange'))
        ],
        'layout': go.Layout(
            title='Velocidad de Internet',
            xaxis={'title': 'Tiempo'},
            yaxis={'title': 'Mbps'},
            shapes=[
                dict(
                    type='rect',
                    xref='paper',
                    yref='paper',
                    x0=0, x1=1, y0=0, y1=1,
                    fillcolor='red' if status == 'Offline' else 'orange' if status == 'Intermitencia' else 'green',
                    opacity=0.1,
                    layer='below'
                )
            ]
        )
    }, html.Span(f"Estado: {status} - Última medición: {data['time'][-1]}", style={'color': color})

@app.callback(
   
    [Input('generate-pdf-button', 'n_clicks')],
    [Input('date-picker-range', 'start_date'), Input('date-picker-range', 'end_date')]
)
def generate_pdf(n_clicks, start_date, end_date):
    if n_clicks > 0:
        # Filtrar los datos por las fechas seleccionadas
        filtered_data = filter_data_by_date(start_date, end_date)
        
        # Verificar si los datos están disponibles
        if filtered_data is None:
            return 'No hay datos disponibles para el rango de fechas seleccionado.'
        
        # Generar el gráfico como imagen
        graph_image = generate_graph_image()

        # Generar el PDF con la imagen
        generate_pdf_report(graph_image)
        
        return f'Reporte generado para el rango: {start_date} a {end_date}'
    return ""

def filter_data_by_date(start_date, end_date):
    filtered_data = {'time': [], 'download': [], 'upload': [], 'status': []}
    
    # Convertir las fechas a objetos datetime para comparación
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    
    for i, timestamp in enumerate(data['time']):
        timestamp_obj = datetime.datetime.strptime(timestamp, '%d/%m/%Y %H:%M:%S')
        if start_date <= timestamp_obj <= end_date:
            filtered_data['time'].append(data['time'][i])
            filtered_data['download'].append(data['download'][i])
            filtered_data['upload'].append(data['upload'][i])
            filtered_data['status'].append(data['status'][i])
    
    return filtered_data

def generate_graph_image():
    # Exportar el gráfico como imagen PNG
    fig = go.Figure(
        data=[
            go.Scatter(x=data['time'], y=data['download'], mode='lines+markers', name='Download (Mbps)', line=dict(color='blue')),
            go.Scatter(x=data['time'], y=data['upload'], mode='lines+markers', name='Upload (Mbps)', line=dict(color='orange'))
        ],
        layout=go.Layout(
            title='Velocidad de Internet',
            xaxis={'title': 'Tiempo'},
            yaxis={'title': 'Mbps'}
        )
    )
    
    # Guardar el gráfico como imagen en un archivo temporal
    image_file = "graph_image.png"
    pio.write_image(fig, image_file)
    
    return image_file

def generate_pdf_report(graph_image):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    c.drawString(100, 750, f'Reporte de velocidad de Internet')
    c.drawString(100, 730, f'Fecha de generación: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
    
    # Insertar la imagen del gráfico en el PDF
    c.drawImage(graph_image, 100, 500, width=400, height=300)
    
    c.save()
    
    # Guardar el PDF
    with open("reporte_velocidad_internet.pdf", "wb") as f:
        f.write(buffer.getvalue())

if __name__ == '__main__':
    app.run_server(debug=True)
