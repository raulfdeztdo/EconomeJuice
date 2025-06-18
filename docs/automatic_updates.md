# Actualizaciones Automáticas

## Descripción

El sistema de análisis del NASDAQ incluye actualizaciones automáticas cada 15 minutos durante el horario de mercado, así como la capacidad de realizar actualizaciones manuales desde el frontend a través de un servidor Node.js integrado.

## Configuración Automática

### Horario de Ejecución
- **Frecuencia**: Cada 15 minutos
- **Días**: Lunes a Viernes
- **Horario**: 7:00 AM a 10:00 PM
- **Zona horaria**: Local del sistema

### macOS (LaunchAgent)
En macOS, el sistema utiliza LaunchAgent en lugar de cron para mayor confiabilidad:

1. **Archivo de configuración**: `scripts/com.econome.nasdaq.analysis.plist`
2. **Ubicación**: `~/Library/LaunchAgents/`
3. **Comando de carga**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.econome.nasdaq.analysis.plist
   ```
4. **Verificación**:
   ```bash
   launchctl list | grep com.econome.nasdaq.analysis
   ```

### Linux (Cron Job)
Para sistemas Linux, el sistema utiliza cron con la siguiente expresión:
```
*/15 7-22 * * 1-5 /ruta/al/script/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1
```

**Configuración**:
1. Ejecutar el script de configuración:
   ```bash
   ./scripts/setup_cron.sh
   ```

2. Verificar la configuración:
   ```bash
   crontab -l
   ```

3. Ver logs de ejecución:
   ```bash
   tail -f /tmp/nasdaq_analysis.log
   ```

## Servidor Node.js Integrado

### Características
- **Puerto**: 3000 (configurable con variable de entorno PORT)
- **API REST**: Endpoint `/run-analysis` para actualizaciones manuales
- **Archivos estáticos**: Sirve el frontend desde `/public`
- **Datos**: Sirve archivos JSON desde `/data`

### Iniciar el Servidor
```bash
npm start
```

### Endpoints Disponibles
- `GET /`: Dashboard principal
- `POST /run-analysis`: Ejecuta análisis manual
- `GET /data/:filename`: Acceso a archivos de datos

## Funcionalidades del Frontend

### Información de Última Actualización
- **Ubicación**: Debajo de los botones de control
- **Información mostrada**:
  - Icono de estado (✅ éxito, ❌ error, ⏱️ pendiente)
  - Tiempo relativo ("Hace X minutos")
  - Fecha y hora exacta
  - Mensaje de error si aplica

### Botones de Control
1. **Actualizar**: Recarga los datos del archivo existente
2. **Actualizar** (manual): Ejecuta una actualización manual a través del servidor
3. **Hoy**: Selecciona la fecha actual

### Actualización Automática del Timestamp
- El frontend verifica la última actualización cada minuto
- Se actualiza automáticamente sin recargar la página
- Funciona tanto con servidor estático como con Node.js

## Archivos Importantes

### Scripts
- `scripts/run_daily_analysis.sh`: Script principal de análisis
- `scripts/setup_cron.sh`: Configuración del cron job (Linux)
- `scripts/com.econome.nasdaq.analysis.plist`: LaunchAgent para macOS

### Servidor
- `server.js`: Servidor Node.js con API REST
- `package.json`: Dependencias y scripts de Node.js

### Datos
- `data/YYYYMMDD.json`: Archivos de análisis diarios
- `data/last_update.json`: Timestamp de última actualización

### Frontend
- `public/app.js`: Lógica de actualización y timestamp
- `public/index.html`: Interfaz de usuario

## Estructura del Archivo de Timestamp

```json
{
  "last_update": "2024-12-20T15:30:00.000Z",
  "status": "success",
  "message": "Análisis completado exitosamente"
}
```

### Estados Posibles
- `success`: Análisis completado correctamente
- `error`: Error en la ejecución

## Logs y Monitoreo

### Ubicación de Logs
- **Cron logs**: `/tmp/nasdaq_analysis.log`
- **Logs del script**: Salida estándar y error

### Comandos Útiles
```bash
# Ver logs en tiempo real
tail -f /tmp/nasdaq_analysis.log

# Ver últimas 50 líneas
tail -50 /tmp/nasdaq_analysis.log

# Buscar errores
grep -i error /tmp/nasdaq_analysis.log
```

## Solución de Problemas

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
1. Verificar que el cron service esté activo:
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
3. Probar la actualización desde terminal:
   ```bash
   curl -X POST http://localhost:3000/run-analysis
   ```

### El frontend no muestra la última actualización
1. Verificar que existe el archivo `data/last_update.json`
2. Verificar que el formato JSON es válido
3. Revisar la consola del navegador para errores
4. Si usas el servidor Node.js, verificar que esté ejecutándose

### Datos no se actualizan
1. Verificar logs de las actualizaciones automáticas
2. Verificar que el entorno virtual está disponible
3. Probar ejecución manual del script de análisis
3. Verificar dependencias de Python

## Desinstalación

Para eliminar el cron job:
```bash
crontab -e
# Eliminar la línea correspondiente al análisis
```

O eliminar todo el crontab:
```bash
crontab -r
```