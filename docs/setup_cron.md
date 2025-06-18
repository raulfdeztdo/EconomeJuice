# Configurar Actualizaciones Automáticas

## Configuración por Sistema Operativo

### macOS - LaunchAgent (Recomendado)

En macOS, se recomienda usar LaunchAgent en lugar de cron para mayor confiabilidad:

#### 1. Verificar que el archivo LaunchAgent existe
```bash
ls -la scripts/com.econome.nasdaq.analysis.plist
```

#### 2. Copiar a la ubicación correcta
```bash
cp scripts/com.econome.nasdaq.analysis.plist ~/Library/LaunchAgents/
```

#### 3. Cargar el LaunchAgent
```bash
launchctl load ~/Library/LaunchAgents/com.econome.nasdaq.analysis.plist
```

#### 4. Verificar que está cargado
```bash
launchctl list | grep com.econome.nasdaq.analysis
```

### Linux - Cron Job

Para sistemas Linux, sigue estos pasos para configurar el cron job:

#### 1. Editar Crontab

```bash
crontab -e
```

#### 2. Agregar la línea de cron

Agrega esta línea al final del archivo (ajusta la ruta completa):

```bash
# Ejecutar análisis NASDAQ cada 15 minutos de lunes a viernes de 7:00 a 22:00
*/15 7-22 * * 1-5 /ruta/completa/a/EconomeJuice/scripts/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1
```

**Ejemplo con ruta específica:**
```bash
*/15 7-22 * * 1-5 /Users/raulfdez/Desktop/EconomeJuice/scripts/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1
```

#### 3. Verificar que cron esté funcionando

```bash
# Ver trabajos de cron actuales
crontab -l

# Ver logs de cron (Linux)
tail -f /var/log/cron.log

# Ver logs del análisis
tail -f /tmp/nasdaq_analysis.log
```

#### 4. Configuración alternativa con horarios específicos

Si quieres personalizar los horarios:

```bash
# Ejecutar cada 30 minutos en horario extendido
*/30 6-23 * * 1-5 /ruta/al/script/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1

# Ejecutar solo en horarios específicos
0,15,30,45 9-16 * * 1-5 /ruta/al/script/run_daily_analysis.sh >> /tmp/nasdaq_analysis.log 2>&1
```

## Configuración Común

### Permisos necesarios

Asegúrate de que el script tenga permisos de ejecución:

```bash
chmod +x scripts/run_daily_analysis.sh
```

### Logs y Monitoreo

Los logs se guardan en:
- `/tmp/nasdaq_analysis.log` - Logs de ejecución del análisis
- `data/last_update.json` - Timestamp de última actualización

### Comandos útiles para monitoreo

```bash
# Ver logs en tiempo real
tail -f /tmp/nasdaq_analysis.log

# Ver últimas 50 líneas
tail -50 /tmp/nasdaq_analysis.log

# Buscar errores
grep -i error /tmp/nasdaq_analysis.log

# Ver estado de última actualización
cat data/last_update.json
```

## Solución de Problemas

### Problemas comunes

1. **Verificar permisos del script:**
```bash
ls -la scripts/run_daily_analysis.sh
```

2. **Probar el script manualmente:**
```bash
./scripts/run_daily_analysis.sh
```

3. **Verificar dependencias de Python:**
```bash
pip list | grep -E "yfinance|pandas|numpy"
```

4. **Verificar que el entorno virtual está activado (si se usa):**
```bash
which python3
```

### Problemas específicos por sistema

#### Linux
- **Verificar que cron está ejecutándose:**
  ```bash
  systemctl status cron
  ```

- **Ver logs de cron:**
  ```bash
  tail -f /var/log/cron.log
  ```

#### macOS
- **El LaunchAgent es la opción recomendada** (ver sección macOS arriba)
- **Si usas cron en macOS, puede requerir permisos especiales**

### Script de configuración automática

Para Linux, puedes usar el script de configuración automática:

```bash
./scripts/setup_cron.sh
```

Este script:
1. Verifica permisos del script de análisis
2. Configura el cron job automáticamente
3. Verifica que la configuración sea correcta

## Verificación Final

Después de configurar las actualizaciones automáticas:

1. **Esperar 15 minutos** (o el intervalo configurado)
2. **Verificar que se creó el archivo de log:**
   ```bash
   ls -la /tmp/nasdaq_analysis.log
   ```
3. **Verificar que se actualizó el timestamp:**
   ```bash
   cat data/last_update.json
   ```
4. **Verificar en el dashboard web** que aparece la información de última actualización

## Desactivar Actualizaciones Automáticas

### macOS (LaunchAgent)
```bash
# Descargar el LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.econome.nasdaq.analysis.plist

# Eliminar el archivo (opcional)
rm ~/Library/LaunchAgents/com.econome.nasdaq.analysis.plist
```

### Linux (Cron)
```bash
# Editar crontab y eliminar la línea
crontab -e

# O eliminar todo el crontab
crontab -r
```
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