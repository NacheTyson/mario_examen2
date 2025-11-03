from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import math
import requests
from datetime import datetime
import os

app = Flask(__name__)

# HTML TEMPLATE COMPLETO CORREGIDO
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>European Flight Duration Predictor</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        #map { 
            height: 500px; 
            border-radius: 0.5rem;
            z-index: 1;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .airport-marker {
            cursor: pointer;
        }
        .flight-path {
            stroke: #3b82f6;
            stroke-width: 3;
            stroke-dasharray: 10, 5;
            opacity: 0.7;
        }
        .origin-marker {
            filter: drop-shadow(0 0 8px #3b82f6);
        }
        .dest-marker {
            filter: drop-shadow(0 0 8px #10b981);
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-2">✈️ European Flight Duration Predictor</h1>
            <p class="text-lg text-gray-600">Predice la duración real de vuelos basada en condiciones climáticas actuales</p>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Panel de Control -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold mb-4">🛫 Selecciona tu Vuelo</h2>

                <div class="space-y-4">
                    <!-- Origen -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Aeropuerto de Origen</label>
                        <select id="originSelect" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200">
                            <option value="">Selecciona origen...</option>
                        </select>
                        <div id="originWeather" class="mt-2 bg-blue-50 border border-blue-200 text-blue-800 p-3 rounded-lg hidden">
                            <div class="flex justify-between items-center">
                                <div>
                                    <div class="font-semibold" id="originName">-</div>
                                    <div class="text-sm mt-1" id="originWeatherInfo">-</div>
                                </div>
                                <div class="text-2xl" id="originWeatherIcon">⛅</div>
                            </div>
                        </div>
                    </div>

                    <!-- Destino -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Aeropuerto de Destino</label>
                        <select id="destSelect" class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200">
                            <option value="">Selecciona destino...</option>
                        </select>
                        <div id="destWeather" class="mt-2 bg-green-50 border border-green-200 text-green-800 p-3 rounded-lg hidden">
                            <div class="flex justify-between items-center">
                                <div>
                                    <div class="font-semibold" id="destName">-</div>
                                    <div class="text-sm mt-1" id="destWeatherInfo">-</div>
                                </div>
                                <div class="text-2xl" id="destWeatherIcon">⛅</div>
                            </div>
                        </div>
                    </div>

                    <!-- Botón Calcular -->
                    <button id="calculateBtn" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 transform hover:scale-105 flex items-center justify-center">
                        <span id="calculateText">🧮 Calcular Duración del Vuelo</span>
                        <div id="calculateSpinner" class="loading ml-2 hidden"></div>
                    </button>
                </div>

                <!-- Resultados -->
                <div id="results" class="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg hidden">
                    <h3 class="text-lg font-semibold text-green-800 mb-3">📊 Resultado de la Predicción</h3>
                    <div id="resultContent" class="space-y-3 text-gray-700">
                        <!-- Resultados dinámicos -->
                    </div>
                    <div class="mt-3 text-xs text-gray-500" id="calculationTime"></div>
                </div>
            </div>

            <!-- Mapa -->
            <div class="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold mb-4">🗺️ Mapa de Aeropuertos Europeos</h2>
                <div id="map"></div>
                <div class="mt-4 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                    <p>💡 <strong>Instrucciones:</strong> Selecciona aeropuertos en el panel o haz clic directamente en los marcadores del mapa</p>
                </div>
            </div>
        </div>

        <!-- Información del Proyecto -->
        <div class="mt-8 bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-xl font-semibold mb-4">ℹ️ Sobre este Proyecto</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-gray-700">
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2 text-blue-600">🌤️ Datos en Tiempo Real</h3>
                    <p>Usamos Open-Meteo API para obtener condiciones climáticas actuales que afectan la duración del vuelo.</p>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2 text-green-600">📐 Cálculos Precisos</h3>
                    <p>Fórmula Haversine para distancias + factores de viento y temperatura para predicciones realistas.</p>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold mb-2 text-purple-600">🇪🇺 Cobertura Europea</h3>
                    <p>50 aeropuertos principales de Europa con datos climáticos confiables.</p>
                </div>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        // Variables globales
        let map;
        let airports = [];
        let originMarker = null;
        let destMarker = null;
        let flightLine = null;

        // Inicialización
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 Inicializando aplicación...');
            initializeMap();
            loadAirports();
            setupEventListeners();
        });

        // Inicializar mapa Leaflet
        function initializeMap() {
            console.log('🗺️ Inicializando mapa...');
            map = L.map('map').setView([48.8566, 2.3522], 5);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            console.log('✅ Mapa inicializado');
        }

        // Cargar aeropuertos desde la API
        async function loadAirports() {
            try {
                console.log('📡 Cargando aeropuertos...');
                showLoading('Cargando aeropuertos...');

                const response = await fetch('/api/airports');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                airports = await response.json();
                console.log(`✅ Cargados ${airports.length} aeropuertos`);

                populateSelects();
                addAirportsToMap();
                hideLoading();

            } catch (error) {
                console.error('❌ Error loading airports:', error);
                hideLoading();
                alert('Error cargando los aeropuertos. Por favor recarga la página.');
            }
        }

        // Poblar selects de aeropuertos
        function populateSelects() {
            console.log('📝 Poblando selects...');
            const originSelect = document.getElementById('originSelect');
            const destSelect = document.getElementById('destSelect');

            if (!originSelect || !destSelect) {
                console.error('❌ No se encontraron los elementos select');
                return;
            }

            // Ordenar aeropuertos alfabéticamente por código IATA
            airports.sort((a, b) => a.iata_code.localeCompare(b.iata_code));

            airports.forEach(airport => {
                const option = document.createElement('option');
                option.value = airport.iata_code;
                option.textContent = `${airport.iata_code} - ${airport.name} (${airport.iso_country})`;

                originSelect.appendChild(option.cloneNode(true));
                destSelect.appendChild(option);
            });

            console.log('✅ Selects poblados');
        }

        // Añadir aeropuertos al mapa
        function addAirportsToMap() {
            console.log('📍 Añadiendo aeropuertos al mapa...');
            airports.forEach(airport => {
                const marker = L.marker([airport.latitude_deg, airport.longitude_deg], {
                    icon: L.divIcon({
                        className: 'airport-marker',
                        html: '✈️',
                        iconSize: [25, 25],
                        iconAnchor: [12, 12]
                    })
                })
                .bindPopup(`
                    <div class="text-center min-w-48">
                        <div class="font-bold text-lg text-blue-600">${airport.iata_code}</div>
                        <div class="text-sm text-gray-700">${airport.name}</div>
                        <div class="text-xs text-gray-500">${airport.iso_country}</div>
                        <div class="mt-2 space-y-1">
                            <button onclick="window.selectAsOrigin('${airport.iata_code}')" 
                                    class="w-full px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm transition duration-200">
                                🛫 Origen
                            </button>
                            <button onclick="window.selectAsDestination('${airport.iata_code}')" 
                                    class="w-full px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm transition duration-200">
                                🛬 Destino
                            </button>
                        </div>
                    </div>
                `)
                .addTo(map);
            });
            console.log('✅ Aeropuertos añadidos al mapa');
        }

        // Configurar event listeners
        function setupEventListeners() {
            console.log('🎯 Configurando event listeners...');
            const calculateBtn = document.getElementById('calculateBtn');
            const originSelect = document.getElementById('originSelect');
            const destSelect = document.getElementById('destSelect');

            if (calculateBtn) {
                calculateBtn.addEventListener('click', calculateFlight);
            }

            if (originSelect) {
                originSelect.addEventListener('change', function() {
                    if (this.value) {
                        updateWeatherInfo('origin', this.value);
                    } else {
                        hideWeatherInfo('origin');
                        clearMapMarkers();
                    }
                });
            }

            if (destSelect) {
                destSelect.addEventListener('change', function() {
                    if (this.value) {
                        updateWeatherInfo('destination', this.value);
                    } else {
                        hideWeatherInfo('destination');
                        clearMapMarkers();
                    }
                });
            }
            console.log('✅ Event listeners configurados');
        }

        // Mostrar loading
        function showLoading(message) {
            const calculateText = document.getElementById('calculateText');
            const calculateSpinner = document.getElementById('calculateSpinner');
            const calculateBtn = document.getElementById('calculateBtn');

            if (calculateText) calculateText.textContent = message;
            if (calculateSpinner) calculateSpinner.classList.remove('hidden');
            if (calculateBtn) calculateBtn.disabled = true;
        }

        // Ocultar loading
        function hideLoading() {
            const calculateText = document.getElementById('calculateText');
            const calculateSpinner = document.getElementById('calculateSpinner');
            const calculateBtn = document.getElementById('calculateBtn');

            if (calculateText) calculateText.textContent = '🧮 Calcular Duración del Vuelo';
            if (calculateSpinner) calculateSpinner.classList.add('hidden');
            if (calculateBtn) calculateBtn.disabled = false;
        }

        // Seleccionar aeropuerto como origen desde el mapa
        window.selectAsOrigin = function(iataCode) {
            const originSelect = document.getElementById('originSelect');
            if (originSelect) {
                originSelect.value = iataCode;
                updateWeatherInfo('origin', iataCode);
                if (map) map.closePopup();
            }
        }

        // Seleccionar aeropuerto como destino desde el mapa
        window.selectAsDestination = function(iataCode) {
            const destSelect = document.getElementById('destSelect');
            if (destSelect) {
                destSelect.value = iataCode;
                updateWeatherInfo('destination', iataCode);
                if (map) map.closePopup();
            }
        }

        // Ocultar información del clima
        function hideWeatherInfo(type) {
            const weatherDiv = document.getElementById(`${type}Weather`);
            if (weatherDiv) {
                weatherDiv.classList.add('hidden');
            }
        }

        // Actualizar información del clima
        async function updateWeatherInfo(type, iataCode) {
            if (!iataCode) return;

            try {
                console.log(`🌤️ Obteniendo clima para ${iataCode}...`);
                showLoading(`Obteniendo clima para ${iataCode}...`);

                const response = await fetch(`/api/weather/${iataCode}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                if (data.weather) {
                    const nameElement = document.getElementById(`${type}Name`);
                    const weatherInfoElement = document.getElementById(`${type}WeatherInfo`);
                    const weatherIconElement = document.getElementById(`${type}WeatherIcon`);
                    const weatherDiv = document.getElementById(`${type}Weather`);

                    const airport = airports.find(a => a.iata_code === iataCode);

                    if (nameElement && airport) nameElement.textContent = `${airport.name} (${iataCode})`;
                    if (weatherInfoElement) weatherInfoElement.textContent = `🌡️ ${data.weather.temperature}°C | 🌬️ ${data.weather.wind_speed} km/h`;
                    if (weatherIconElement) weatherIconElement.textContent = getWeatherIcon(data.weather.temperature, data.weather.wind_speed);
                    if (weatherDiv) weatherDiv.classList.remove('hidden');
                }

                updateMapMarkers();
                hideLoading();

            } catch (error) {
                console.error(`❌ Error updating weather for ${iataCode}:`, error);
                hideLoading();
                alert(`Error obteniendo el clima para ${iataCode}: ${error.message}`);
            }
        }

        // Obtener icono del clima
        function getWeatherIcon(temp, wind) {
            if (wind > 30) return '💨';
            if (wind > 20) return '🌬️';
            if (temp < 0) return '❄️';
            if (temp < 5) return '☁️';
            if (temp > 25) return '☀️';
            if (temp > 20) return '⛅';
            return '🌤️';
        }

        // Limpiar marcadores del mapa
        function clearMapMarkers() {
            if (originMarker && map) {
                map.removeLayer(originMarker);
                originMarker = null;
            }
            if (destMarker && map) {
                map.removeLayer(destMarker);
                destMarker = null;
            }
            if (flightLine && map) {
                map.removeLayer(flightLine);
                flightLine = null;
            }
        }

        // Actualizar marcadores en el mapa
        function updateMapMarkers() {
            const originSelect = document.getElementById('originSelect');
            const destSelect = document.getElementById('destSelect');

            if (!originSelect || !destSelect) return;

            const originIata = originSelect.value;
            const destIata = destSelect.value;

            // Limpiar marcadores anteriores
            clearMapMarkers();

            // Añadir nuevo origen
            if (originIata) {
                const originAirport = airports.find(a => a.iata_code === originIata);
                if (originAirport && map) {
                    originMarker = L.marker([originAirport.latitude_deg, originAirport.longitude_deg], {
                        icon: L.divIcon({
                            className: 'airport-marker origin-marker',
                            html: '🛫',
                            iconSize: [30, 30],
                            iconAnchor: [15, 15]
                        })
                    }).addTo(map);
                }
            }

            // Añadir nuevo destino
            if (destIata) {
                const destAirport = airports.find(a => a.iata_code === destIata);
                if (destAirport && map) {
                    destMarker = L.marker([destAirport.latitude_deg, destAirport.longitude_deg], {
                        icon: L.divIcon({
                            className: 'airport-marker dest-marker',
                            html: '🛬',
                            iconSize: [30, 30],
                            iconAnchor: [15, 15]
                        })
                    }).addTo(map);
                }
            }

            // Añadir línea de vuelo si hay ambos
            if (originIata && destIata && map) {
                const originAirport = airports.find(a => a.iata_code === originIata);
                const destAirport = airports.find(a => a.iata_code === destIata);

                if (originAirport && destAirport) {
                    const latlngs = [
                        [originAirport.latitude_deg, originAirport.longitude_deg],
                        [destAirport.latitude_deg, destAirport.longitude_deg]
                    ];

                    flightLine = L.polyline(latlngs, {
                        color: '#3b82f6',
                        weight: 4,
                        dashArray: '10, 5',
                        opacity: 0.8,
                        className: 'flight-path'
                    }).addTo(map);

                    // Ajustar vista del mapa para mostrar ambos aeropuertos
                    const group = new L.featureGroup([originMarker, destMarker]);
                    map.fitBounds(group.getBounds().pad(0.2));
                }
            }
        }

        // Calcular duración del vuelo
        async function calculateFlight() {
            const originSelect = document.getElementById('originSelect');
            const destSelect = document.getElementById('destSelect');

            if (!originSelect || !destSelect) {
                alert('Error: No se encontraron los elementos de selección');
                return;
            }

            const originIata = originSelect.value;
            const destIata = destSelect.value;

            if (!originIata || !destIata) {
                alert('Por favor selecciona aeropuertos de origen y destino');
                return;
            }

            if (originIata === destIata) {
                alert('Los aeropuertos de origen y destino deben ser diferentes');
                return;
            }

            try {
                console.log(`✈️ Calculando vuelo: ${originIata} → ${destIata}`);
                showLoading('Calculando duración...');

                const response = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        origin: originIata,
                        destination: destIata
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();

                if (result.error) {
                    throw new Error(result.error);
                }

                displayResults(result);
                hideLoading();

            } catch (error) {
                console.error('❌ Error calculando vuelo:', error);
                hideLoading();
                alert('Error calculando el vuelo: ' + error.message);
            }
        }

        // Mostrar resultados
        function displayResults(result) {
            const resultsDiv = document.getElementById('results');
            const resultContent = document.getElementById('resultContent');
            const calculationTime = document.getElementById('calculationTime');

            if (!resultsDiv || !resultContent || !calculationTime) {
                console.error('❌ No se encontraron elementos de resultados');
                return;
            }

            const hours = Math.floor(result.duration_min / 60);
            const minutes = Math.round(result.duration_min % 60);
            const durationText = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;

            resultContent.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-white p-3 rounded-lg border border-blue-200">
                        <div class="font-semibold text-blue-700 mb-2">🛫 Origen</div>
                        <div class="text-sm">
                            <div class="font-medium">${result.origin.name}</div>
                            <div class="text-gray-600">${result.origin.iata} - ${result.origin.country}</div>
                            <div class="mt-1 text-xs">
                                🌡️ ${result.origin.weather.temperature}°C<br>
                                🌬️ ${result.origin.weather.wind_speed} km/h
                            </div>
                        </div>
                    </div>
                    <div class="bg-white p-3 rounded-lg border border-green-200">
                        <div class="font-semibold text-green-700 mb-2">🛬 Destino</div>
                        <div class="text-sm">
                            <div class="font-medium">${result.destination.name}</div>
                            <div class="text-gray-600">${result.destination.iata} - ${result.destination.country}</div>
                            <div class="mt-1 text-xs">
                                🌡️ ${result.destination.weather.temperature}°C<br>
                                🌬️ ${result.destination.weather.wind_speed} km/h
                            </div>
                        </div>
                    </div>
                </div>
                <div class="bg-gradient-to-r from-blue-100 to-purple-100 p-4 rounded-lg border border-purple-200">
                    <div class="flex justify-between items-center">
                        <div>
                            <div class="font-semibold text-purple-700">📏 Distancia</div>
                            <div class="text-2xl font-bold text-purple-600">${result.distance_km} km</div>
                        </div>
                        <div class="text-center">
                            <div class="font-semibold text-purple-700">⏱️ Duración Estimada</div>
                            <div class="text-2xl font-bold text-purple-600">${durationText}</div>
                        </div>
                    </div>
                </div>
            `;

            calculationTime.textContent = `Calculado el: ${result.calculation_time}`;
            resultsDiv.classList.remove('hidden');

            // Scroll suave a los resultados
            resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    </script>
</body>
</html>
'''


def download_airport_data():
    """Descargar datos de aeropuertos europeos desde la web"""
    try:
        print("🌍 Descargando datos de aeropuertos europeos...")

        # Dataset público de aeropuertos (OurAirports)
        url = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv"

        # Descargar todos los aeropuertos
        all_airports = pd.read_csv(url)

        # Filtrar aeropuertos europeos principales
        europe_countries = ['ES', 'FR', 'DE', 'GB', 'IT', 'NL', 'CH', 'BE', 'PT', 'SE',
                            'NO', 'DK', 'FI', 'IE', 'AT', 'PL', 'CZ', 'HU', 'GR', 'TR']

        europe_airports = all_airports[
            (all_airports['iso_country'].isin(europe_countries)) &
            (all_airports['type'].isin(['medium_airport', 'large_airport'])) &
            (all_airports['iata_code'].notna()) &
            (all_airports['scheduled_service'] == 'yes')
            ].copy()

        # Ordenar por importancia y tomar los 50 principales
        europe_airports['priority'] = europe_airports['type'].map({
            'large_airport': 1,
            'medium_airport': 2
        })

        top_airports = europe_airports.sort_values(['priority', 'iata_code']).head(50)

        # Seleccionar y renombrar columnas necesarias
        top_airports = top_airports[['iata_code', 'name', 'latitude_deg', 'longitude_deg', 'iso_country']]
        top_airports = top_airports.rename(columns={'iata_code': 'iata_code'})

        print(f"✅ Descargados {len(top_airports)} aeropuertos europeos")
        return top_airports

    except Exception as e:
        print(f"❌ Error descargando aeropuertos: {e}")
        # Datos de respaldo en caso de error
        return create_fallback_data()


def create_fallback_data():
    """Crear datos de respaldo con aeropuertos principales"""
    fallback_data = {
        'iata_code': ['MAD', 'BCN', 'CDG', 'ORY', 'FRA', 'MUC', 'LHR', 'LGW', 'AMS', 'FCO',
                      'LIN', 'ZRH', 'BRU', 'VIE', 'PRG', 'BUD', 'WAW', 'ARN', 'CPH', 'OSL',
                      'HEL', 'DUB', 'LIS', 'OPO', 'AGP', 'PMI', 'VLC', 'SVQ', 'NCE', 'MRS',
                      'TLS', 'BOD', 'LIL', 'HAM', 'STR', 'CGN', 'DUS', 'BER', 'MAN', 'EDI',
                      'BHX', 'GLA', 'BLQ', 'VCE', 'NAP', 'GVA', 'BSL', 'OTP', 'SOF', 'KRK'],
        'name': [
            'Adolfo Suárez Madrid–Barajas Airport', 'Barcelona-El Prat Airport',
            'Charles de Gaulle Airport', 'Paris-Orly Airport', 'Frankfurt Airport',
            'Munich Airport', 'Heathrow Airport', 'Gatwick Airport', 'Amsterdam Airport Schiphol',
            'Leonardo da Vinci–Fiumicino Airport', 'Milan Linate Airport', 'Zurich Airport',
            'Brussels Airport', 'Vienna International Airport', 'Václav Havel Airport Prague',
            'Budapest Ferenc Liszt International Airport', 'Warsaw Chopin Airport',
            'Stockholm Arlanda Airport', 'Copenhagen Airport', 'Oslo Airport',
            'Helsinki Airport', 'Dublin Airport', 'Lisbon Airport', 'Porto Airport',
            'Málaga Airport', 'Palma de Mallorca Airport', 'Valencia Airport',
            'Seville Airport', 'Nice Côte d\'Azur Airport', 'Marseille Provence Airport',
            'Toulouse–Blagnac Airport', 'Bordeaux–Mérignac Airport', 'Lille Airport',
            'Hamburg Airport', 'Stuttgart Airport', 'Cologne Bonn Airport',
            'Düsseldorf Airport', 'Berlin Brandenburg Airport', 'Manchester Airport',
            'Edinburgh Airport', 'Birmingham Airport', 'Glasgow Airport',
            'Bologna Guglielmo Marconi Airport', 'Venice Marco Polo Airport',
            'Naples International Airport', 'Geneva Airport', 'EuroAirport Basel-Mulhouse-Freiburg',
            'Henri Coandă International Airport', 'Sofia Airport', 'Kraków John Paul II International Airport'
        ],
        'latitude_deg': [
            40.471926, 41.297445, 49.012779, 48.725278, 50.033333, 48.353783, 51.4775, 51.148056,
            52.308613, 41.800278, 45.445103, 47.458056, 50.901389, 48.110278, 50.100833, 47.429722,
            52.165833, 59.651944, 55.617917, 60.193889, 60.317222, 53.421389, 38.781311, 41.248055,
            36.6749, 39.55361, 39.489314, 37.418, 43.658411, 43.435555, 43.629075, 44.828335,
            50.563333, 53.630389, 48.689878, 50.865917, 51.289453, 52.362247, 53.353744, 55.95,
            52.453856, 55.871944, 44.535444, 45.505278, 40.886111, 46.238064, 47.59, 44.572161,
            42.695194, 50.077731
        ],
        'longitude_deg': [
            -3.56264, 2.083294, 2.55, 2.359444, 8.570556, 11.786086, -0.461389, -0.190278,
            4.763889, 12.238889, 9.276739, 8.548056, 4.484444, 16.569722, 14.26, 19.261111,
            20.967222, 17.918611, 12.655972, 11.100361, 24.963333, -6.27, -9.135919, -8.681389,
            -4.499106, 2.727778, -0.481625, -5.893106, 7.215872, 5.213611, 1.363819, -0.715556,
            3.086944, 9.988228, 9.221964, 7.142744, 6.766775, 13.500672, -2.27495, -3.3725,
            -1.748028, -4.433056, 11.288667, 12.351944, 14.290833, 6.10895, 7.529167, 26.102178,
            23.406167, 19.784836
        ],
        'iso_country': [
            'ES', 'ES', 'FR', 'FR', 'DE', 'DE', 'GB', 'GB', 'NL', 'IT', 'IT', 'CH', 'BE', 'AT',
            'CZ', 'HU', 'PL', 'SE', 'DK', 'NO', 'FI', 'IE', 'PT', 'PT', 'ES', 'ES', 'ES', 'ES',
            'FR', 'FR', 'FR', 'FR', 'FR', 'DE', 'DE', 'DE', 'DE', 'DE', 'GB', 'GB', 'GB', 'GB',
            'IT', 'IT', 'IT', 'CH', 'CH', 'RO', 'BG', 'PL'
        ]
    }

    return pd.DataFrame(fallback_data)


# Cargar datos de aeropuertos (se descargan una vez al iniciar la app)
airports_df = download_airport_data()


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
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/airports')
def get_airports():
    """API para obtener lista de aeropuertos"""
    airports = airports_df.to_dict('records')
    return jsonify(airports)


@app.route('/api/calculate', methods=['POST'])
def calculate_flight():
    """API para calcular duración de vuelo"""
    data = request.json
    origin_iata = data.get('origin')
    dest_iata = data.get('destination')

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
    print("🚀 European Flight Duration Predictor")
    print("=====================================")
    print(f"📊 Aeropuertos cargados: {len(airports_df)}")
    print(f"🌍 Países: {airports_df['iso_country'].nunique()}")
    print(f"🌐 Servidor: http://localhost:5000")
    print("=====================================")

    app.run(debug=True, host='0.0.0.0', port=5000)

# Guardar como: create_readme.py
import os

# --- Información del Proyecto ---
PROJECT_TITLE = "✈️ European Flight Duration Predictor"
CREATOR_NAME = "Mario Lloreda Rodero"
TEACHER_NAME = "Juan Marcelo Gutierrez Miranda"
# ---------------------------------

# Contenido del archivo README.md en formato Markdown
# Se usa una f-string para insertar las variables de arriba
readme_content = f"""
# {PROJECT_TITLE}

Un proyecto de aplicación web para predecir la duración de vuelos europeos basándose en datos meteorológicos en tiempo real.

* **Creador:** {CREATOR_NAME}
* **Profesor:** {TEACHER_NAME}

---

## 📄 Descripción del Proyecto

Este proyecto es una aplicación web interactiva creada con **Flask** (Python) para el backend y **Leaflet.js** con **Tailwind CSS** para el frontend.

Permite a los usuarios seleccionar un aeropuerto de origen y uno de destino entre los 50 principales de Europa. La aplicación calcula la distancia geodésica (usando la fórmula Haversine) y, lo más importante, ajusta la duración estimada del vuelo basándose en las **condiciones meteorológicas actuales** (viento y temperatura) obtenidas de APIs en tiempo real.

El objetivo es proporcionar una estimación de vuelo más precisa que una simple búsqueda estática, demostrando el impacto del clima en la aviación.

---

## 🚀 Instrucciones de Uso

Para ejecutar este proyecto localmente, sigue estos pasos:

1.  **Clona el repositorio** (o descarga los archivos del proyecto).

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\\Scripts\\activate
    ```

3.  **Instala las dependencias necesarias:**
    El código utiliza `flask`, `pandas` y `requests`.
    ```bash
    pip install flask pandas requests
    ```
    *(Opcionalmente, crea un `requirements.txt` con esos nombres y ejecuta `pip install -r requirements.txt`)*

4.  **Ejecuta la aplicación Flask:**
    Asegúrate de que tu archivo principal se llame `app.py`.
    ```bash
    python app.py
    ```

5.  **Abre tu navegador:**
    Visita [http://127.0.0.1:5000](http://127.0.0.1:5000) para ver y usar la aplicación.

### Cómo usar la interfaz:
* Selecciona un **aeropuerto de origen** usando el menú desplegable o haciendo clic en un icono ✈️ en el mapa.
* Selecciona un **aeropuerto de destino** de la misma manera.
* Haz clic en el botón **"🧮 Calcular Duración del Vuelo"**.
* Los resultados (distancia, clima y duración) aparecerán en la tarjeta de "Resultados".

---

## 🏗️ Arquitectura de la Aplicación

La aplicación sigue una arquitectura cliente-servidor simple, donde Flask actúa como servidor web y API.

### Frontend (Cliente)
* **Tecnologías:** HTML, Tailwind CSS y JavaScript (ES6).
* **Mapa:** Se utiliza **Leaflet.js** para mostrar un mapa interactivo de Europa con los marcadores de los aeropuertos.
* **Renderizado:** El frontend es una Sola Página (SPA) renderizada desde una única plantilla HTML (`HTML_TEMPLATE`) en el script de Flask.
* **Comunicación:** El cliente (JavaScript) realiza llamadas `fetch` asíncronas a los endpoints de la API del backend para obtener datos sin recargar la página.

### Backend (Servidor - Flask)
El backend de Flask (`app.py`) expone varios puntos finales (endpoints) API:

* `@app.route('/')`: Sirve la página principal que contiene toda la lógica del frontend (el `HTML_TEMPLATE`).
* `@app.route('/api/airports')`: Devuelve un objeto JSON con la lista de los 50 aeropuertos europeos, obtenidos por la función `download_airport_data()` usando `pandas`.
* `@app.route('/api/weather/<iata_code>')`: (Endpoint inferido por el JS) Obtiene y devuelve el clima actual (temperatura, viento) para el aeropuerto con el código IATA especificado.
* `@app.route('/api/calculate')`: (Endpoint inferido por el JS) Recibe el origen y el destino. Llama internamente a la API del clima, calcula la distancia Haversine y aplica una fórmula (que incluye el viento y la temperatura) para estimar la duración del vuelo.

---

## 🔌 APIs Externas Utilizadas

1.  **OurAirports (Datos de Aeropuertos):**
    * **Endpoint:** `https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv`
    * **Uso:** La función `download_airport_data()` descarga este archivo CSV público, lo filtra con `pandas` para encontrar aeropuertos europeos principales y crea la lista de 50 aeropuertos utilizada por la aplicación.

2.  **Open-Meteo API (Clima):**
    * **Uso:** (Como se menciona en el HTML del proyecto) Esta API se utiliza para obtener los datos meteorológicos en tiempo real (temperatura y velocidad del viento) para las coordenadas geográficas de los aeropuertos seleccionados.

---

## 📊 Resumen de Hallazgos

Este proyecto demuestra con éxito cómo integrar múltiples fuentes de datos (un archivo CSV para aeropuertos y una API JSON para el clima) en una aplicación web funcional.

El hallazgo principal es la **variabilidad de la duración del vuelo** basada en factores meteorológicos. Un mismo vuelo puede tener duraciones notablemente diferentes dependiendo de la dirección y la fuerza del viento (viento de cola vs. viento en contra), algo que los cálculos estáticos no capturan. La aplicación visualiza esta complejidad de una manera simple y accesible.
"""

def create_readme_file():
    """Escribe el contenido de la variable 'readme_content' en un archivo README.md"""
    try:
        with open("README.md", "w", encoding="utf-8") as f:
            # Usamos .strip() para eliminar cualquier espacio en blanco inicial/final
            f.write(readme_content.strip())
        print("\n✅ ¡Éxito! El archivo README.md ha sido creado.")
        print("   Puedes añadirlo y enviarlo a tu repositorio git.")
    except IOError as e:
        print(f"\n❌ Error escribiendo el archivo README.md: {e}")

if __name__ == "__main__":
    print("Generando archivo README.md...")
    create_readme_file()