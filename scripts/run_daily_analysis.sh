#!/bin/bash

# Script para ejecutar el análisis del NASDAQ cada 15 minutos
# Se ejecuta de lunes a viernes de 7:00 a 22:00 cada 15 minutos

echo "$(date): Iniciando análisis del NASDAQ..."

# Cambiar al directorio del proyecto (directorio padre del script)
cd "$(dirname "$0")/.."

# Activar el entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Entorno virtual activado"
fi

# Ejecutar el análisis desde la carpeta src
python src/nasdaq_analyzer.py

# Verificar el resultado
if [ $? -eq 0 ]; then
    echo "✅ Análisis completado exitosamente"

    # Verificar que se creó el archivo JSON del día
    TODAY_FILE="data/$(date +%Y%m%d).json"
    if [ -f "$TODAY_FILE" ]; then
        echo "✅ Archivo de datos creado: $TODAY_FILE"

        # Mostrar tamaño del archivo
        FILE_SIZE=$(ls -lh "$TODAY_FILE" | awk '{print $5}')
        echo "📊 Tamaño del archivo: $FILE_SIZE"
        
        # Crear archivo de timestamp para el frontend
        TIMESTAMP_FILE="data/last_update.json"
        echo "{\"last_update\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\", \"status\": \"success\"}" > "$TIMESTAMP_FILE"
        echo "📅 Timestamp actualizado: $TIMESTAMP_FILE"
        
        # Copiar archivos al directorio public/data para despliegue
        mkdir -p public/data
        cp data/*.json public/data/ 2>/dev/null || true
        echo "📁 Archivos copiados a public/data para despliegue"
    else
        echo "⚠️  ADVERTENCIA: No se encontró el archivo de datos del día"
        # Crear archivo de timestamp con error
        TIMESTAMP_FILE="data/last_update.json"
        echo "{\"last_update\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\", \"status\": \"error\", \"message\": \"No se encontró archivo de datos\"}" > "$TIMESTAMP_FILE"
        
        # Copiar timestamp de error a public/data
        mkdir -p public/data
        cp "$TIMESTAMP_FILE" public/data/ 2>/dev/null || true
    fi
else
    echo "❌ Error en el análisis"
    # Crear archivo de timestamp con error
    TIMESTAMP_FILE="data/last_update.json"
    echo "{\"last_update\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\", \"status\": \"error\", \"message\": \"Error ejecutando análisis\"}" > "$TIMESTAMP_FILE"
    
    # Copiar timestamp de error a public/data
    mkdir -p public/data
    cp "$TIMESTAMP_FILE" public/data/ 2>/dev/null || true
    exit 1
fi

echo "=== Análisis completado ==="

# Desactivar entorno virtual si se activó
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit 0