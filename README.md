# ✈️ European Flight Duration Predictor

Un proyecto de aplicación web para predecir la duración de vuelos europeos basándose en datos meteorológicos en tiempo real.

* **Creador:** Mario Lloreda Rodero
* **Profesor:** Juan Marcelo Gutierrez Miranda

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
    source venv/bin/activate  # En Windows: venv\Scripts\activate
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