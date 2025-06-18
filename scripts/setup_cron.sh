#!/bin/bash

# Script para configurar el cron job que ejecuta el análisis cada 15 minutos
# De lunes a viernes de 7:00 a 22:00

echo "Configurando cron job para análisis automático del NASDAQ..."

# Obtener la ruta absoluta del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_SCRIPT="$SCRIPT_DIR/run_daily_analysis.sh"

# Verificar que el script existe
if [ ! -f "$ANALYSIS_SCRIPT" ]; then
    echo "❌ Error: No se encontró el script $ANALYSIS_SCRIPT"
    exit 1
fi

# Hacer el script ejecutable
chmod +x "$ANALYSIS_SCRIPT"

# Crear el cron job
# Ejecutar cada 15 minutos (*/15) de lunes a viernes (1-5) de 7:00 a 22:00
CRON_JOB="*/15 7-22 * * 1-5 $ANALYSIS_SCRIPT >> /tmp/nasdaq_analysis.log 2>&1"

echo "Agregando cron job: $CRON_JOB"

# Agregar el cron job al crontab del usuario
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job configurado exitosamente"
    echo "📅 El análisis se ejecutará cada 15 minutos de lunes a viernes de 7:00 a 22:00"
    echo "📝 Los logs se guardarán en /tmp/nasdaq_analysis.log"
    echo ""
    echo "Para ver el crontab actual:"
    echo "  crontab -l"
    echo ""
    echo "Para eliminar el cron job:"
    echo "  crontab -e"
    echo "  (y eliminar la línea correspondiente)"
else
    echo "❌ Error configurando el cron job"
    exit 1
fi

echo ""
echo "=== Configuración completada ==="