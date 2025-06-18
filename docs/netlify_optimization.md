# Optimización de Netlify para 300 Minutos de Build Mensuales

## 📊 Límites de Netlify Actualizados

**Límite Real**: 300 minutos de build por mes (no 100 despliegues)
- **Tiempo por build**: ~2-3 minutos promedio
- **Builds máximos estimados**: ~100-150 por mes
- **Estrategia**: Optimizar frecuencia y duración de builds

## ⏰ Nueva Programación de Análisis

### Horario de Ejecución
- **Frecuencia**: Cada 15 minutos
- **Horario España**: 7:00 - 22:00 (lunes a viernes)
- **Horario UTC**: 6:00 - 21:00 (lunes a viernes)
- **Total ejecuciones diarias**: 64 ejecuciones
- **Total ejecuciones semanales**: 320 ejecuciones
- **Total ejecuciones mensuales**: ~1,280 ejecuciones

### Optimización Inteligente

#### 1. Análisis Diferenciado por Horario
```yaml
# Horario de mercado (14:30-21:00 UTC / 9:30-16:00 EST)
- Análisis completo con generación de datos
- Duración estimada: 2-3 minutos
- Frecuencia de cambios: Alta

# Fuera de horario de mercado (6:00-14:30 y 21:00-22:00 UTC)
- Análisis ligero sin generación de datos
- Duración estimada: 30-60 segundos
- Frecuencia de cambios: Muy baja
```

#### 2. Detección Inteligente de Cambios
- **Pre-verificación**: Comprobar si el mercado está abierto
- **Análisis condicional**: Solo generar datos nuevos cuando sea necesario
- **Commit inteligente**: Solo hacer push si hay cambios reales
- **Build trigger**: Netlify solo se activa con cambios en el repositorio

## 📈 Estimación de Uso Mensual

### Escenario Optimizado
```
Horario de mercado (6.5 horas/día × 5 días = 32.5 horas/semana):
- Ejecuciones: 26 × 5 = 130 por semana
- Builds con cambios estimados: 30-40% = 39-52 builds/semana
- Tiempo de build: 39-52 × 2.5 min = 97-130 min/semana

Fuera de horario (8.5 horas/día × 5 días = 42.5 horas/semana):
- Ejecuciones: 34 × 5 = 170 por semana
- Builds con cambios estimados: 5-10% = 8-17 builds/semana
- Tiempo de build: 8-17 × 1 min = 8-17 min/semana

Total semanal: 105-147 minutos
Total mensual: 420-588 minutos
```

### ⚠️ Riesgo de Exceder Límite
La estimación actual (420-588 min/mes) **EXCEDE** el límite de 300 minutos.

## 🔧 Estrategias de Mitigación

### Opción 1: Reducir Frecuencia
```yaml
# Cambiar de cada 15 min a cada 30 min
cron: '0,30 6-21 * * 1-5'
# Resultado: ~210-294 minutos/mes ✅
```

### Opción 2: Horario Más Restrictivo
```yaml
# Solo horario de mercado + 1 hora antes/después
cron: '0,15,30,45 13-22 * * 1-5'
# Resultado: ~180-250 minutos/mes ✅
```

### Opción 3: Análisis Solo en Horario de Mercado
```yaml
# Solo cuando el mercado está abierto
cron: '0,15,30,45 14-21 * * 1-5'
# Resultado: ~120-180 minutos/mes ✅
```

## 🚀 Configuración Recomendada

### Implementación Actual
```yaml
name: Daily NASDAQ Analysis
on:
  schedule:
    - cron: '0,15,30,45 6-21 * * 1-5'  # Cada 15 min, 7-22h España
```

### Optimizaciones Implementadas
1. **Verificación de horario de mercado**
2. **Análisis ligero fuera de horario**
3. **Detección inteligente de cambios**
4. **Commits condicionales**
5. **Builds solo cuando hay cambios**

## 📊 Monitoreo y Alertas

### Métricas a Vigilar
- Minutos de build utilizados (Netlify Dashboard)
- Frecuencia de cambios por horario
- Duración promedio de builds
- Tasa de éxito de análisis

### Alertas Configuradas
- **80% del límite**: Reducir frecuencia a cada 30 minutos
- **90% del límite**: Solo análisis en horario de mercado
- **95% del límite**: Pausar análisis automático

## 🔄 Plan de Contingencia

### Si se Excede el Límite
1. **Inmediato**: Deshabilitar workflow automático
2. **Temporal**: Usar solo ejecución manual
3. **Largo plazo**: Migrar a servidor propio o upgrade de plan

### Configuración de Emergencia
```yaml
# Análisis mínimo - Solo 2 veces al día
cron: '0 9,16 * * 1-5'  # 9:00 y 16:00 UTC
# Resultado: ~20-40 minutos/mes
```

## 📝 Próximos Pasos

1. **Monitorear** uso real durante 1 semana
2. **Ajustar** frecuencia según datos reales
3. **Optimizar** duración de builds
4. **Evaluar** upgrade de plan si es necesario

---

**Última actualización**: $(date +'%Y-%m-%d %H:%M UTC')
**Estado**: Configuración optimizada para 300 min/mes
**Riesgo actual**: ALTO - Requiere monitoreo constante