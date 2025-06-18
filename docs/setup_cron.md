# Configuración de Ejecución Automática

## Configurar Cron Job para Análisis Diario

Para que el análisis se ejecute automáticamente todos los días a las 7:00 AM hora española, sigue estos pasos:

### 1. Editar Crontab

```bash
crontab -e
```

### 2. Agregar la línea de cron

Agrega esta línea al final del archivo (ajusta la ruta completa):

```bash
# Ejecutar análisis NASDAQ 100 a las 7:00 AM hora española
# En invierno (UTC+1): 6:00 UTC
# En verano (UTC+2): 5:00 UTC
0 6 * * * /Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh
```

**Nota:** Ajusta la hora según el horario de verano/invierno:
- **Invierno (UTC+1):** `0 6 * * *` (6:00 AM UTC = 7:00 AM España)
- **Verano (UTC+2):** `0 5 * * *` (5:00 AM UTC = 7:00 AM España)

### 3. Verificar que cron esté funcionando

```bash
# Ver trabajos de cron actuales
crontab -l

# Ver logs de cron (macOS)
tail -f /var/log/system.log | grep cron
```

### 4. Configuración alternativa con horarios específicos

Si quieres ser más específico con los horarios:

```bash
# Ejecutar solo en días laborables
0 6 * * 1-5 /Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh

# Ejecutar todos los días excepto fines de semana
0 6 * * 0,6 /Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh
```

### 5. Permisos necesarios

Asegúrate de que el script tenga permisos de ejecución:

```bash
chmod +x /Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh
```

### 6. Configuración para macOS (Launchd)

En macOS, también puedes usar Launchd como alternativa a cron:

1. Crear archivo `~/Library/LaunchAgents/com.economejuice.nasdaq.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.economejuice.nasdaq</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/raulfdez/Desktop/EconomeJuice/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/raulfdez/Desktop/EconomeJuice/logs/launchd_error.log</string>
</dict>
</plist>
```

2. Cargar el servicio:

```bash
launchctl load ~/Library/LaunchAgents/com.economejuice.nasdaq.plist
```

3. Verificar que esté cargado:

```bash
launchctl list | grep economejuice
```

### 7. Logs y Monitoreo

Los logs se guardarán en:
- `logs/analysis_YYYYMMDD.log` - Logs diarios del análisis
- Los logs de cron en `/var/log/system.log` (macOS)

### 8. Solución de Problemas

**Si el cron no funciona:**

1. Verificar permisos:
```bash
ls -la /Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh
```

2. Probar el script manualmente:
```bash
/Users/raulfdez/Desktop/EconomeJuice/run_daily_analysis.sh
```

3. Verificar que cron tenga permisos (macOS):
   - Ir a "Preferencias del Sistema" > "Seguridad y Privacidad" > "Privacidad"
   - Agregar `/usr/sbin/cron` a "Acceso completo al disco"

4. Verificar variables de entorno en cron:
```bash
# Agregar al inicio del script si es necesario
export PATH=/usr/local/bin:/usr/bin:/bin
```

### 9. Comando de Prueba

Para probar que todo funciona, ejecuta:

```bash
# Ejecutar análisis manualmente
./run_daily_analysis.sh

# Verificar que se creó el archivo JSON
ls -la data/$(date +%Y%m%d).json
```

¡Listo! El sistema ejecutará automáticamente el análisis todos los días a las 7:00 AM.