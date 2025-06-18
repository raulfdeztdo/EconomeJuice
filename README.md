# 📊 EconomeJuice - Análisis Técnico NASDAQ 100

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/EconomeJuice/graphs/commit-activity)

Sistema automatizado de análisis técnico profesional para el índice NASDAQ 100 con visualización web interactiva y dashboard en tiempo real.

## 🚀 Características Principales

### 📈 Análisis Técnico Avanzado
- **Indicadores Técnicos**: RSI, MACD, ADX, Bandas de Bollinger
- **Análisis Multi-timeframe**: 1m, 5m, 15m, 1h, 1d
- **Detección de Patrones**: Identificación automática de señales de trading
- **Niveles Clave**: Soporte y resistencia dinámicos

### 🎯 Sentimiento de Mercado
- **VIX Analysis**: Índice de volatilidad y miedo del mercado
- **TICK Index**: Breadth del mercado en tiempo real
- **Order Flow**: Análisis de presión compradora/vendedora
- **Big Prints**: Detección de operaciones institucionales

### 🔮 Predicción Probabilística
- **Machine Learning**: Algoritmos de predicción basados en datos históricos
- **Confidence Scoring**: Niveles de confianza para cada predicción
- **Risk Assessment**: Evaluación automática de riesgo

### 🌐 Dashboard Web Interactivo
- **Responsive Design**: Compatible con desktop y móvil
- **Dark/Light Mode**: Interfaz adaptable
- **Auto-Updates**: Actualizaciones automáticas cada 15 minutos
- **Manual Updates**: Botón de actualización forzada
- **Last Update Info**: Información de última actualización en tiempo real
- **Historical Analysis**: Navegación por análisis históricos

## 📋 Requisitos

- Python 3.8+
- Conexión a internet (para obtener datos de mercado)
- Navegador web moderno

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <tu-repositorio>
cd EconomeJuice
```

### 2. Crear entorno virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 4. Instalar dependencias de Node.js

```bash
npm install
```

### 5. Ejecutar análisis inicial

```bash
python3 src/nasdaq_analyzer.py
```

Esto creará un archivo JSON en el directorio `data/` con el análisis del día actual.

### 6. Iniciar el servidor

```bash
npm start
```

Esto iniciará el servidor Node.js en `http://localhost:3000` con todas las funcionalidades habilitadas.

### Alternativa: Servidor estático simple

Si solo quieres ver la interfaz sin funcionalidades de servidor:

```bash
# Con Python
python3 -m http.server 8000
# Luego visita: http://localhost:8000/public/
```

## ⚙️ Sistema de Actualización Automática

### 🔄 Configuración Automática (Recomendado)

El sistema incluye configuración automática que ejecuta el análisis **cada 15 minutos** de lunes a viernes de 7:00 AM a 10:00 PM:

#### En macOS (LaunchAgent)
El sistema utiliza LaunchAgent para programar las actualizaciones automáticas:
- ✅ Ejecución cada 15 minutos durante horario de mercado
- ✅ Solo días laborables (lunes a viernes)
- ✅ Horario: 7:00 AM - 10:00 PM
- ✅ Logs automáticos en `/tmp/nasdaq_analysis.log`
- ✅ Archivo de timestamp para el frontend

#### En Linux (Cron)
Para sistemas Linux, usa el script de configuración:
```bash
# Configurar automáticamente el cron job
./scripts/setup_cron.sh
```

### 📊 Funcionalidades del Frontend

- **Información de última actualización**: Muestra cuándo fue la última ejecución
- **Estado visual**: Iconos de éxito (✅), error (❌) o pendiente (⏱️)
- **Tiempo relativo**: "Hace X minutos" con fecha/hora exacta
- **Actualización manual**: Botón "Actualizar" para ejecutar análisis bajo demanda
- **Auto-refresh**: El timestamp se actualiza cada minuto automáticamente
- **Servidor integrado**: Manejo de actualizaciones a través de API REST

### 🔧 Configuración Manual (Avanzado)

#### Usando Cron (Linux/macOS)

1. Hacer el script ejecutable:
```bash
chmod +x scripts/run_daily_analysis.sh
```

2. Editar crontab:
```bash
crontab -e
```

3. Agregar la línea para ejecución cada 15 minutos:
```bash
# Ejecutar cada 15 minutos de lunes a viernes de 7:00 a 22:00
*/15 7-22 * * 1-5 /ruta/completa/a/EconomeJuice/scripts/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1
```

#### Verificar configuración:
```bash
# Ver cron jobs activos
crontab -l

# Ver logs en tiempo real
tail -f /tmp/nasdaq_analysis.log
```

### Usando Task Scheduler (Windows)

1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Configurar para ejecutar diariamente a las 7:00 AM
4. Acción: Ejecutar `run_daily_analysis.sh` (necesitarás WSL o Git Bash)

## 🌐 Despliegue en Netlify

### Opción 1: Drag & Drop

1. Ve a [netlify.com](https://netlify.com)
2. Arrastra la carpeta del proyecto a la zona de despliegue
3. ¡Listo! Tu sitio estará disponible en una URL de Netlify

### Opción 2: Desde Git

1. Sube tu proyecto a GitHub/GitLab
2. Conecta tu repositorio en Netlify
3. Configurar:
   - **Build command**: (dejar vacío)
   - **Publish directory**: `.` (directorio raíz)
4. Desplegar

### Configuración para Netlify

El proyecto incluye un archivo `netlify.toml` preconfigurado:

```toml
[build]
  publish = "public"
  command = "python src/nasdaq_analyzer.py"

[[redirects]]
  from = "/data/*"
  to = "../data/:splat"
  status = 200

[[headers]]
  for = "*.json"
  [headers.values]
    Cache-Control = "public, max-age=300"

[[headers]]
  for = "*.js"
  [headers.values]
    Cache-Control = "public, max-age=31536000"
```

## 📁 Estructura del Proyecto

```
EconomeJuice/
├── src/                   # Código fuente Python
│   ├── nasdaq_analyzer.py # Script principal de análisis
│   └── enhanced_analyzer.py # Analizador avanzado
├── public/                # Frontend web
│   ├── index.html        # Página principal
│   ├── app.js            # Lógica de Vue.js
│   └── wiki.html         # Wiki de indicadores técnicos
├── scripts/               # Scripts de automatización
│   ├── run_daily_analysis.sh  # Script de ejecución
│   ├── setup_cron.sh     # Configuración automática de cron
│   └── com.econome.nasdaq.analysis.plist # LaunchAgent para macOS
├── data/                  # Datos y análisis
│   ├── last_update.json  # Timestamp de última actualización
│   ├── 20241220.json     # Análisis por fecha
│   └── .gitkeep
├── docs/                  # Documentación
│   ├── automatic_updates.md # Guía de actualizaciones automáticas
│   └── setup_cron.md     # Configuración de cron
├── server.js              # Servidor Node.js con API REST
├── package.json           # Dependencias y scripts de Node.js
├── package-lock.json      # Lockfile de dependencias
├── requirements.txt       # Dependencias de Python
├── netlify.toml          # Configuración de despliegue
├── .gitignore            # Archivos ignorados por Git
├── LICENSE               # Licencia MIT
└── README.md             # Este archivo
```

## 🔧 Personalización

### Modificar indicadores técnicos

Edita la función `calculate_technical_indicators()` en `nasdaq_analyzer.py`:

```python
# Agregar nuevos indicadores
stochastic = calculate_stochastic(data)
williams_r = calculate_williams_r(data)
```

### Cambiar símbolo de análisis

Modifica la variable `symbol` en la clase `NasdaqAnalyzer`:

```python
self.symbol = "^GSPC"  # Para S&P 500
self.symbol = "^DJI"   # Para Dow Jones
```

### Personalizar la interfaz

Modifica `index.html` y `app.js` para:
- Cambiar colores y estilos
- Agregar nuevas secciones
- Modificar el layout

## 📊 Formato de Datos JSON

Cada archivo de análisis contiene:

```json
{
  "date": "2024-12-20",
  "timestamp": "2024-12-20T07:00:00.000Z",
  "symbol": "^NDX",
  "yesterday_data": {
    "high": 21456.78,
    "low": 21298.45,
    "close": 21389.12,
    "volume": 3250000000
  },
  "technical_indicators": {
    "rsi": 62.3,
    "sma_20": 21345.67,
    "macd": 78.5,
    // ... más indicadores
  },
  "trend_analysis": {
    "trend": "bullish",
    "confidence": 75.8,
    "signals": ["..."]
  },
  "daily_levels": {
    "resistance_1": 21520.89,
    "support_1": 21170.45,
    // ... más niveles
  },
  "news": [...],
  "summary": "..."
}
```

## 🐛 Solución de Problemas

### Error: "No module named 'yfinance'"
```bash
pip install yfinance
```

### Error: "Permission denied" en el script
```bash
chmod +x scripts/run_daily_analysis.sh
```

### Error: "npm: command not found"
Instala Node.js desde [nodejs.org](https://nodejs.org) o usando un gestor de paquetes:
```bash
# macOS con Homebrew
brew install node

# Ubuntu/Debian
sudo apt install nodejs npm
```

### El servidor Node.js no inicia
1. Verificar que las dependencias están instaladas:
   ```bash
   npm install
   ```
2. Verificar que el puerto 3000 no esté en uso:
   ```bash
   lsof -i :3000
   ```
3. Probar con otro puerto:
   ```bash
   PORT=3001 npm start
   ```

### La actualización manual no funciona
1. Verificar que el servidor Node.js está ejecutándose
2. Revisar la consola del navegador para errores
3. Verificar que el script tiene permisos de ejecución
4. Probar la actualización manual desde terminal:
   ```bash
   curl -X POST http://localhost:3000/run-analysis
   ```

### La página no carga datos
1. Verifica que existe el archivo JSON del día en `data/`
2. Ejecuta el análisis manualmente: `python3 src/nasdaq_analyzer.py`
3. Revisa la consola del navegador para errores
4. Verifica que el archivo `data/last_update.json` existe

### Las actualizaciones automáticas no funcionan (macOS)
1. Verificar que el LaunchAgent está cargado:
   ```bash
   launchctl list | grep com.econome.nasdaq.analysis
   ```
2. Verificar permisos del script:
   ```bash
   ls -la scripts/run_daily_analysis.sh
   ```
3. Probar ejecución manual:
   ```bash
   ./scripts/run_daily_analysis.sh
   ```
4. Ver logs:
   ```bash
   tail -f /tmp/nasdaq_analysis.log
   ```

### Las actualizaciones automáticas no funcionan (Linux)
1. Verificar que el servicio cron está activo:
   ```bash
   systemctl status cron
   ```
2. Verificar la configuración del crontab:
   ```bash
   crontab -l
   ```
3. Ver logs del cron:
   ```bash
   tail -f /var/log/cron.log
   ```

### No se muestra la última actualización
1. Verificar que existe `data/last_update.json`
2. Verificar formato JSON válido
3. Revisar consola del navegador para errores de fetch
4. Si usas el servidor Node.js, verificar que esté ejecutándose

### Problemas con CORS en desarrollo local
Usa el servidor Node.js incluido en lugar de un servidor estático:
```bash
npm start
# Luego visita: http://localhost:3000
```

## 📈 Próximas Mejoras

- [x] ~~Actualizaciones automáticas cada 15 minutos~~
- [x] ~~Sistema de timestamps en tiempo real~~
- [x] ~~Botón de actualización manual~~
- [x] ~~Modo oscuro~~
- [x] ~~Wiki de indicadores técnicos en español~~
- [x] ~~Estructura de proyecto organizada~~
- [x] ~~API REST para datos y actualizaciones~~
- [x] ~~Servidor Node.js integrado~~
- [x] ~~Soporte para macOS con LaunchAgent~~
- [ ] Integración con APIs de noticias reales
- [ ] Gráficos interactivos con Chart.js
- [ ] Alertas por email/SMS
- [ ] Análisis de múltiples índices
- [ ] Machine Learning para predicciones
- [ ] PWA (Progressive Web App)
- [ ] Notificaciones push
- [ ] Análisis de sentimiento de redes sociales
- [ ] Dashboard de administración
- [ ] Configuración de intervalos personalizables

## ⚠️ Disclaimer

Este software es solo para fines educativos e informativos. No constituye asesoramiento financiero. Las decisiones de inversión deben basarse en su propia investigación y análisis.

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

---

**¡Disfruta analizando el mercado! 📈**