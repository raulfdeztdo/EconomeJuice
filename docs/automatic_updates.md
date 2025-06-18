# Sistema de Actualización Automática

## Descripción

El sistema de análisis del NASDAQ ahora incluye actualizaciones automáticas cada 15 minutos durante el horario de mercado, así como la capacidad de realizar actualizaciones manuales desde el frontend.

## Configuración Automática

### Horario de Ejecución
- **Frecuencia**: Cada 15 minutos
- **Días**: Lunes a Viernes
- **Horario**: 7:00 AM a 10:00 PM
- **Zona horaria**: Local del sistema

### Cron Job
El sistema utiliza un cron job configurado con la siguiente expresión:
```
*/15 7-22 * * 1-5 /ruta/al/script/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1
```

### Configuración
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
2. **Forzar**: Ejecuta una actualización manual (simula nueva ejecución)
3. **Hoy**: Selecciona la fecha actual

### Actualización Automática del Timestamp
- El frontend verifica la última actualización cada minuto
- Se actualiza automáticamente sin recargar la página

## Archivos Importantes

### Scripts
- `scripts/run_daily_analysis.sh`: Script principal de análisis
- `scripts/setup_cron.sh`: Configuración del cron job

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

### El cron job no se ejecuta
1. Verificar que el cron service esté activo:
   ```bash
   sudo launchctl list | grep cron
   ```

2. Verificar permisos del script:
   ```bash
   ls -la scripts/run_daily_analysis.sh
   ```

3. Probar ejecución manual:
   ```bash
   ./scripts/run_daily_analysis.sh
   ```

### El frontend no muestra la última actualización
1. Verificar que existe el archivo `data/last_update.json`
2. Verificar que el formato JSON es válido
3. Revisar la consola del navegador para errores

### Datos no se actualizan
1. Verificar logs del cron job
2. Verificar que el entorno virtual está disponible
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