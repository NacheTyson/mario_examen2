from flask import Flask, render_template, request, jsonify
import pandas as pd
import math
import requests
from datetime import datetime
import os

app = Flask(__name__)


# Cargar datos de aeropuertos
def load_airport_data():
    """Cargar datos de aeropuertos desde nuestro dataset"""
    try:
        airports_df = pd.read_csv('data/raw/optimized_europe_airports.csv')
        return airports_df
    except Exception as e:
        print(f"Error cargando aeropuertos: {e}")
        return None


def haversine_distance(coord1, coord2):
    """Calcular distancia real entre aeropuertos"""
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371.0  # Radio Tierra en km

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


def get_current_weather(airport):
    """Obtener clima ACTUAL de un aeropuerto"""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': airport['latitude_deg'],
            'longitude': airport['longitude_deg'],
            'current': 'temperature_2m,wind_speed_10m,wind_direction_10m',
            'timezone': 'auto'
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if 'current' in data:
            return {
                'temperature': data['current']['temperature_2m'],
                'wind_speed': data['current']['wind_speed_10m'],
                'wind_direction': data['current']['wind_direction_10m']
            }
    except Exception as e:
        print(f"Error clima {airport['iata_code']}: {e}")

    return {'temperature': 15, 'wind_speed': 10, 'wind_direction': 180}


def calculate_wind_effect(origin_weather, dest_weather):
    """Calcula efecto del viento"""
    origin_wind_speed = origin_weather.get('wind_speed', 10)
    dest_wind_speed = dest_weather.get('wind_speed', 10)
    origin_wind_dir = origin_weather.get('wind_direction', 180)
    dest_wind_dir = dest_weather.get('wind_direction', 180)

    avg_wind_speed = (origin_wind_speed + dest_wind_speed) / 2

    if avg_wind_speed <= 10:
        wind_factor = 1.0
    elif avg_wind_speed <= 25:
        wind_factor = 1 + (avg_wind_speed * 0.002)
    elif avg_wind_speed <= 40:
        wind_factor = 1 + (avg_wind_speed * 0.003)
    else:
        wind_factor = 1 + (avg_wind_speed * 0.004)

    wind_dir_difference = abs(origin_wind_dir - dest_wind_dir)
    if wind_dir_difference > 90:
        wind_factor *= 1.05

    return wind_factor


def calculate_temperature_effect(origin_weather, dest_weather):
    """Calcula efecto de la temperatura"""
    origin_temp = origin_weather.get('temperature', 15)
    dest_temp = dest_weather.get('temperature', 15)
    avg_temp = (origin_temp + dest_temp) / 2

    if 10 <= avg_temp <= 20:
        return 1.0
    elif 5 <= avg_temp < 10 or 20 < avg_temp <= 25:
        return 1.02
    elif 0 <= avg_temp < 5 or 25 < avg_temp <= 30:
        return 1.04
    elif -10 <= avg_temp < 0 or 30 < avg_temp <= 35:
        return 1.07
    else:
        return 1.10


def calculate_improved_duration(distance_km, origin_weather, dest_weather):
    """Calcula duración de vuelo mejorada"""
    base_flight_duration = (distance_km / 800) * 60
    wind_effect = calculate_wind_effect(origin_weather, dest_weather)
    temp_effect = calculate_temperature_effect(origin_weather, dest_weather)
    ground_operations = 45

    flight_duration = base_flight_duration * wind_effect * temp_effect
    total_duration = flight_duration + ground_operations

    return round(total_duration, 2)


@app.route('/')
def index():
    """Página principal con el mapa"""
    airports_df = load_airport_data()
    if airports_df is not None:
        airports_list = airports_df[['iata_code', 'name', 'latitude_deg', 'longitude_deg', 'iso_country']].to_dict(
            'records')
    else:
        airports_list = []

    return render_template('index.html', airports=airports_list)


@app.route('/api/airports')
def get_airports():
    """API para obtener lista de aeropuertos"""
    airports_df = load_airport_data()
    if airports_df is not None:
        airports = airports_df[['iata_code', 'name', 'latitude_deg', 'longitude_deg', 'iso_country']].to_dict('records')
        return jsonify(airports)
    return jsonify([])


@app.route('/api/calculate', methods=['POST'])
def calculate_flight():
    """API para calcular duración de vuelo"""
    data = request.json
    origin_iata = data.get('origin')
    dest_iata = data.get('destination')

    airports_df = load_airport_data()
    if airports_df is None:
        return jsonify({'error': 'No se pudieron cargar los datos de aeropuertos'})

    # Buscar aeropuertos
    origin_airport = airports_df[airports_df['iata_code'] == origin_iata]
    dest_airport = airports_df[airports_df['iata_code'] == dest_iata]

    if origin_airport.empty or dest_airport.empty:
        return jsonify({'error': 'Aeropuertos no encontrados'})

    origin_airport = origin_airport.iloc[0]
    dest_airport = dest_airport.iloc[0]

    # Calcular distancia
    coord1 = (origin_airport['latitude_deg'], origin_airport['longitude_deg'])
    coord2 = (dest_airport['latitude_deg'], dest_airport['longitude_deg'])
    distance = haversine_distance(coord1, coord2)

    # Obtener clima actual
    origin_weather = get_current_weather(origin_airport)
    dest_weather = get_current_weather(dest_airport)

    # Calcular duración
    duration = calculate_improved_duration(distance, origin_weather, dest_weather)

    # Preparar respuesta
    response = {
        'origin': {
            'iata': origin_airport['iata_code'],
            'name': origin_airport['name'],
            'country': origin_airport['iso_country'],
            'weather': origin_weather
        },
        'destination': {
            'iata': dest_airport['iata_code'],
            'name': dest_airport['name'],
            'country': dest_airport['iso_country'],
            'weather': dest_weather
        },
        'distance_km': round(distance, 2),
        'duration_min': duration,
        'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return jsonify(response)


@app.route('/api/weather/<iata_code>')
def get_airport_weather(iata_code):
    """API para obtener clima de un aeropuerto específico"""
    airports_df = load_airport_data()
    if airports_df is None:
        return jsonify({'error': 'No se pudieron cargar los datos'})

    airport = airports_df[airports_df['iata_code'] == iata_code]
    if airport.empty:
        return jsonify({'error': 'Aeropuerto no encontrado'})

    airport = airport.iloc[0]
    weather = get_current_weather(airport)

    return jsonify({
        'iata': iata_code,
        'name': airport['name'],
        'weather': weather
    })


if __name__ == '__main__':
    # Crear carpetas necesarias
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    print("🚀 Iniciando European Flight Duration Predictor...")
    print("📊 Cargando datos de aeropuertos...")
    print("🌐 Servidor disponible en: http://localhost:5000")

    app.run(debug=True, host='0.0.0.0', port=5000)