# Servidor Node.js y API REST

## Descripción

El proyecto incluye un servidor Node.js integrado que proporciona una API REST para manejar actualizaciones manuales y servir archivos estáticos. Esto mejora la experiencia del usuario al permitir actualizaciones en tiempo real sin necesidad de recargar la página.

## Características

### Servidor Express
- **Framework**: Express.js
- **Puerto por defecto**: 3000
- **Puerto configurable**: Variable de entorno `PORT`
- **CORS**: Habilitado para desarrollo

### Endpoints Disponibles

#### `GET /`
- **Descripción**: Sirve el dashboard principal
- **Archivo**: `public/index.html`
- **Respuesta**: Página HTML del dashboard

#### `POST /run-analysis`
- **Descripción**: Ejecuta el análisis de NASDAQ manualmente
- **Proceso**: 
  1. Ejecuta `scripts/run_daily_analysis.sh`
  2. Actualiza `data/last_update.json` con el resultado
  3. Retorna el estado de la operación
- **Respuesta exitosa**:
  ```json
  {
    "success": true,
    "message": "Análisis ejecutado exitosamente",
    "timestamp": "2024-12-20T15:30:00.000Z"
  }
  ```
- **Respuesta de error**:
  ```json
  {
    "success": false,
    "message": "Error al ejecutar el análisis: [detalle del error]",
    "timestamp": "2024-12-20T15:30:00.000Z"
  }
  ```

#### `GET /data/:filename`
- **Descripción**: Sirve archivos de datos JSON
- **Parámetros**: `filename` - nombre del archivo (ej: `20241220.json`, `last_update.json`)
- **Respuesta**: Contenido del archivo JSON
- **Error 404**: Si el archivo no existe

### Archivos Estáticos
- **Directorio**: `/public`
- **Archivos servidos**:
  - `index.html` - Dashboard principal
  - `app.js` - Lógica del frontend
  - `wiki.html` - Wiki de indicadores técnicos
  - Otros archivos CSS, imágenes, etc.

## Instalación y Configuración

### Dependencias
```json
{
  "express": "^4.18.2",
  "cors": "^2.8.5"
}
```

### Instalación
```bash
npm install
```

### Scripts Disponibles
```bash
# Iniciar el servidor
npm start

# Ejecutar análisis manualmente
npm run analyze

# Configurar cron (Linux)
npm run setup-cron
```

## Uso

### Iniciar el Servidor
```bash
# Puerto por defecto (3000)
npm start

# Puerto personalizado
PORT=8080 npm start
```

### Acceder al Dashboard
Abre tu navegador y visita:
- `http://localhost:3000` (puerto por defecto)
- `http://localhost:8080` (puerto personalizado)

### Actualización Manual desde el Frontend
1. Haz clic en el botón "Actualizar" en el dashboard
2. El sistema ejecutará el análisis automáticamente
3. Los datos se actualizarán sin recargar la página
4. El timestamp se actualizará con la nueva información

### Actualización Manual desde Terminal
```bash
# Usando curl
curl -X POST http://localhost:3000/run-analysis

# Usando wget
wget --post-data='' http://localhost:3000/run-analysis
```

## Integración con el Frontend

### Función `manualUpdate()` en app.js
```javascript
async function manualUpdate() {
    try {
        console.log('Iniciando actualización manual...');
        
        const response = await fetch('/run-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Actualización completada:', result.message);
            // Recargar datos después de un breve delay
            setTimeout(() => {
                loadAnalysis();
                loadLastUpdate();
            }, 2000);
        } else {
            console.error('Error en actualización:', result.message);
        }
    } catch (error) {
        console.error('Error al ejecutar actualización manual:', error);
    }
}
```

## Logs y Monitoreo

### Logs del Servidor
El servidor muestra logs en la consola:
```
Servidor iniciado en http://localhost:3000
Rutas configuradas:
- GET / -> Dashboard principal
- POST /run-analysis -> Ejecutar análisis manual
- GET /data/:filename -> Servir archivos de datos
```

### Logs de Análisis
Los logs del análisis se guardan en:
- **Archivo**: `/tmp/nasdaq_analysis.log`
- **Formato**: Timestamp + mensaje + resultado

### Monitoreo en Tiempo Real
```bash
# Ver logs del análisis
tail -f /tmp/nasdaq_analysis.log

# Ver logs del servidor (si se redirigen)
tail -f /tmp/server.log
```

## Solución de Problemas

### El servidor no inicia
1. **Verificar dependencias**:
   ```bash
   npm install
   ```

2. **Puerto en uso**:
   ```bash
   # Verificar qué proceso usa el puerto 3000
   lsof -i :3000
   
   # Usar otro puerto
   PORT=3001 npm start
   ```

3. **Permisos del script**:
   ```bash
   chmod +x scripts/run_daily_analysis.sh
   ```

### La actualización manual no funciona
1. **Verificar que el servidor esté ejecutándose**
2. **Revisar la consola del navegador** para errores de JavaScript
3. **Probar el endpoint directamente**:
   ```bash
   curl -X POST http://localhost:3000/run-analysis
   ```
4. **Verificar permisos del script de análisis**

### Errores de CORS
Si tienes problemas de CORS en desarrollo:
1. El servidor ya incluye configuración de CORS
2. Asegúrate de acceder a través del servidor Node.js (`http://localhost:3000`)
3. No abras el archivo HTML directamente en el navegador

### Archivos de datos no se sirven
1. **Verificar que existen** en el directorio `data/`
2. **Verificar permisos** de lectura
3. **Probar acceso directo**:
   ```bash
   curl http://localhost:3000/data/last_update.json
   ```

## Desarrollo y Extensión

### Agregar Nuevos Endpoints
Edita `server.js` y agrega nuevas rutas:
```javascript
// Nuevo endpoint de ejemplo
app.get('/api/status', (req, res) => {
    res.json({
        status: 'running',
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
    });
});
```

### Middleware Personalizado
```javascript
// Logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});
```

### Variables de Entorno
Crea un archivo `.env` para configuración:
```env
PORT=3000
ANALYSIS_SCRIPT_PATH=./scripts/run_daily_analysis.sh
DATA_DIR=./data
LOG_FILE=/tmp/nasdaq_analysis.log
```

## Seguridad

### Consideraciones
1. **Ejecución de scripts**: El servidor ejecuta scripts del sistema, asegúrate de que solo usuarios autorizados tengan acceso
2. **Validación de entrada**: Los endpoints actuales no requieren autenticación, considera agregar autenticación para producción
3. **Rate limiting**: Considera agregar limitación de velocidad para el endpoint de análisis manual

### Mejoras Recomendadas para Producción
1. **Autenticación**: JWT o session-based auth
2. **Rate limiting**: Express-rate-limit
3. **Validación**: Express-validator
4. **Logging**: Winston o similar
5. **Process management**: PM2 o similar
6. **HTTPS**: Certificados SSL/TLS

## Próximas Mejoras

- [ ] Autenticación y autorización
- [ ] Rate limiting para actualizaciones manuales
- [ ] WebSockets para actualizaciones en tiempo real
- [ ] API para configurar intervalos de actualización
- [ ] Dashboard de administración
- [ ] Métricas y monitoreo avanzado
- [ ] Notificaciones push
- [ ] Múltiples símbolos de análisis