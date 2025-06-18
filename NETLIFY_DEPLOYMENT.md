# Despliegue en Netlify - EconomeJuice

## Configuración del Proyecto

Este proyecto está configurado para desplegarse automáticamente en Netlify con las siguientes características:

### Estructura de Archivos

```
EconomeJuice/
├── public/                 # Archivos estáticos (HTML, CSS, JS)
│   ├── data/              # Datos JSON generados (copiados durante build)
│   ├── _redirects         # Configuración de rutas Netlify
│   ├── index.html         # Dashboard principal
│   └── app.js             # Lógica del frontend
├── netlify/
│   └── functions/         # Funciones serverless
│       └── run-analysis.js # Endpoint para ejecutar análisis manual
├── src/                   # Scripts de análisis Python
├── scripts/               # Scripts de automatización
├── data/                  # Datos originales (no desplegados)
└── netlify.toml           # Configuración de Netlify
```

### Funciones Serverless

#### `/run-analysis` (POST)
- **Propósito**: Ejecutar análisis manual del NASDAQ
- **Método**: POST
- **Respuesta**: JSON con resultado del análisis
- **Timeout**: 5 minutos
- **CORS**: Habilitado para todas las origins

### Proceso de Build

1. **Instalación de dependencias**:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. **Ejecución del análisis inicial**:
   ```bash
   python src/nasdaq_analyzer.py
   ```

3. **Copia de datos**:
   ```bash
   mkdir -p public/data
   cp -r data/* public/data/
   ```

### Variables de Entorno

Configura estas variables en el panel de Netlify:

- `NASDAQ_API_KEY`: Clave de API para datos del NASDAQ (opcional)
- `TIMEZONE`: Zona horaria (default: Europe/Madrid)
- `PYTHON_VERSION`: Versión de Python (configurada: 3.9)
- `NODE_VERSION`: Versión de Node.js (configurada: 18)

### Rutas y Redirecciones

- `/` → Dashboard principal
- `/run-analysis` → Función serverless para análisis manual
- `/data/*` → Archivos JSON de datos

### Actualizaciones Automáticas

#### En Desarrollo Local
Puedes configurar un cron job para actualizaciones automáticas:
```bash
bash scripts/setup_cron.sh
```

#### En Producción (Netlify)
Las actualizaciones manuales se realizan a través del endpoint `/run-analysis`.

### Solución de Problemas

#### Error 404 en `/run-analysis`
- Verifica que el archivo `netlify/functions/run-analysis.js` existe
- Revisa que `_redirects` está en el directorio `public/`
- Confirma que las dependencias de Node.js están instaladas

#### Datos no actualizados
- Los datos se generan durante el build y se copian a `public/data/`
- Para actualizaciones en tiempo real, usa el endpoint `/run-analysis`
- Verifica que los scripts Python se ejecutan correctamente

#### Timeouts en funciones
- Las funciones Netlify tienen un límite de 10 segundos en el plan gratuito
- El análisis puede tardar más, considera optimizar los scripts
- Usa el plan Pro para timeouts de hasta 26 segundos

### Monitoreo

- **Logs de build**: Disponibles en el panel de Netlify
- **Logs de funciones**: Visibles en la sección Functions del panel
- **Estado de datos**: Archivo `last_update.json` contiene timestamp y estado

### Comandos Útiles

```bash
# Desarrollo local
npm run dev

# Ejecutar análisis manualmente
npm run analysis

# Configurar cron (solo local)
npm run setup-cron
```

### Limitaciones en Netlify

1. **Funciones gratuitas**: 125,000 invocaciones/mes, 10s timeout
2. **Build time**: 300 minutos/mes en plan gratuito
3. **Almacenamiento**: Los datos se regeneran en cada build
4. **Cron jobs**: No disponibles, usar servicios externos o webhooks

### Recomendaciones

1. **Para actualizaciones frecuentes**: Considera usar Netlify Functions con webhooks
2. **Para datos históricos**: Implementa almacenamiento externo (base de datos)
3. **Para monitoreo**: Configura alertas basadas en `last_update.json`
4. **Para escalabilidad**: Migra a Netlify Pro o considera otros servicios