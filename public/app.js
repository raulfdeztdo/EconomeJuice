const { createApp } = Vue;

createApp({
    data() {
        return {
            analysis: null,
            loading: false,
            error: null,
            selectedDate: this.getTodayString(),
            availableDates: [],
            currentDate: new Date().toLocaleDateString('es-ES', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }),
            isDarkMode: false,
            currentTimeframe: '1m',
            selectedTimeframe: '1m',
            chart: null,
            lastUpdate: null,
            updateStatus: null,
            isUpdating: false
        }
    },

    mounted() {
        this.initializeDarkMode();
        this.loadAvailableDates();
        this.loadAnalysis();
        this.loadLastUpdate();
        this.setupTimeframeButtons();
        
        // Actualizar el timestamp cada minuto
        setInterval(() => {
            this.loadLastUpdate();
        }, 60000);
    },

    methods: {
        getTodayString() {
            const today = new Date();
            return today.toISOString().split('T')[0];
        },

        async loadAvailableDates() {
            try {
                // Simular carga de fechas disponibles
                // En producción, esto vendría de un endpoint que liste los archivos JSON
                const dates = [];
                const today = new Date();

                // Generar fechas de los últimos 30 días como ejemplo
                for (let i = 0; i < 30; i++) {
                    const date = new Date(today);
                    date.setDate(date.getDate() - i);
                    const dateString = date.toISOString().split('T')[0].replace(/-/g, '');
                    dates.push(dateString);
                }

                this.availableDates = dates;
            } catch (error) {
                console.error('Error cargando fechas disponibles:', error);
            }
        },

        async loadAnalysis() {
            this.loading = true;
            this.error = null;

            try {
                const dateString = this.selectedDate.replace(/-/g, '');
                const response = await fetch(`../data/${dateString}.json`);

                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error(`No hay datos disponibles para la fecha ${this.selectedDate}`);
                    }
                    throw new Error(`Error ${response.status}: ${response.statusText}`);
                }

                this.analysis = await response.json();

                // Initialize chart with 1m timeframe after loading
                this.$nextTick(() => {
                    this.updateChart('1m');
                });
                
                // Cargar timestamp después de cargar análisis
                this.loadLastUpdate();
            } catch (error) {
                console.error('Error cargando análisis:', error);
                this.error = error.message;

                // Si no se encuentra el archivo, cargar datos de ejemplo
                if (error.message.includes('404') || error.message.includes('No hay datos')) {
                    this.loadSampleData();
                }
            } finally {
                this.loading = false;
            }
        },

        async loadLastUpdate() {
            try {
                const response = await fetch('../data/last_update.json');
                if (response.ok) {
                    const data = await response.json();
                    this.lastUpdate = new Date(data.last_update);
                    this.updateStatus = data.status;
                } else {
                    this.lastUpdate = null;
                    this.updateStatus = null;
                }
            } catch (error) {
                console.error('Error cargando última actualización:', error);
                this.lastUpdate = null;
                this.updateStatus = null;
            }
        },

        async manualUpdate() {
            if (this.isUpdating) return;
            
            this.isUpdating = true;
            try {
                // Simular llamada al endpoint de actualización
                // En producción, esto haría una llamada a un endpoint que ejecute el análisis
                const response = await fetch('/api/update-analysis', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (response.ok) {
                    // Esperar un poco para que se complete el análisis
                    setTimeout(() => {
                        this.loadAnalysis();
                        this.loadLastUpdate();
                    }, 2000);
                } else {
                    throw new Error('Error en la actualización manual');
                }
            } catch (error) {
                console.error('Error en actualización manual:', error);
                // Para demo, simplemente recargar los datos existentes
                this.loadAnalysis();
                this.loadLastUpdate();
            } finally {
                setTimeout(() => {
                    this.isUpdating = false;
                }, 2000);
            }
        },

        formatLastUpdate() {
            if (!this.lastUpdate) return 'No disponible';
            
            const now = new Date();
            const diff = now - this.lastUpdate;
            const minutes = Math.floor(diff / 60000);
            const hours = Math.floor(minutes / 60);
            
            if (minutes < 1) {
                return 'Hace menos de 1 minuto';
            } else if (minutes < 60) {
                return `Hace ${minutes} minuto${minutes > 1 ? 's' : ''}`;
            } else if (hours < 24) {
                return `Hace ${hours} hora${hours > 1 ? 's' : ''}`;
            } else {
                return this.lastUpdate.toLocaleDateString('es-ES', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        },

        getUpdateStatusIcon() {
            if (this.updateStatus === 'success') {
                return '✅';
            } else if (this.updateStatus === 'error') {
                return '❌';
            }
            return '⏱️';
        },

        loadSampleData() {
            // Datos de ejemplo para demostración
            this.analysis = {
                date: this.selectedDate,
                timestamp: new Date().toISOString(),
                symbol: '^NDX',
                yesterday_data: {
                    high: 21850.25,
                    low: 21720.80,
                    close: 21785.50,
                    volume: 2450000000
                },
                technical_indicators: {
                    rsi: 58.7,
                    sma_20: 21750.30,
                    sma_50: 21680.15,
                    macd: 45.8,
                    macd_signal: 42.1,
                    macd_histogram: 3.7,
                    bb_upper: 21920.50,
                    bb_middle: 21750.30,
                    bb_lower: 21580.10,
                    last_close: 21785.50,
                    last_high: 21850.25,
                    last_low: 21720.80,
                    last_volume: 2450000000
                },
                trend_analysis: {
                    trend: 'bullish',
                    confidence: 72.5,
                    signals: [
                        'RSI neutral (58.7) - sin señales extremas',
                        'MACD por encima de señal - alcista',
                        'Precio por encima de SMA20 - alcista',
                        'Volumen por encima del promedio'
                    ],
                    bullish_signals: 3,
                    bearish_signals: 0
                },
                daily_levels: {
                    resistance_1: 21920.50,
                    resistance_2: 22100.00,
                    support_1: 21580.10,
                    support_2: 21450.00,
                    fibonacci_38: 21770.25,
                    fibonacci_62: 21690.80,
                    pivot_point: 21785.18
                },
                news: [
                    {
                        title: 'Datos de ejemplo - Análisis técnico generado',
                        summary: 'Este es un análisis de ejemplo. En producción, aquí aparecerían noticias reales del mercado.',
                        source: 'Sistema de demostración',
                        timestamp: new Date().toISOString()
                    }
                ],
                intraday_analysis: {
                    '1m': {
                        timeframe: '1m',
                        total_bars: 390,
                        rsi: 45.5,
                        trend_short: 'neutral',
                        scalp_buy_signal: false,
                        scalp_sell_signal: false,
                        range_trading: true,
                        atr_stop_long: 21800.0,
                        atr_stop_short: 21750.0
                    },
                    '5m': {
                        timeframe: '5m',
                        total_bars: 78,
                        rsi: 52.3,
                        trend_short: 'bullish',
                        ema_bullish_cross: false,
                        ema_bearish_cross: false,
                        momentum_5: 0.25
                    },
                    '15m': {
                        timeframe: '15m',
                        total_bars: 26,
                        rsi: 58.7,
                        trend_short: 'bullish',
                        macd_bullish: true,
                        support_level: 16580.0,
                        resistance_level: 16920.0
                    },
                    '4h': {
                        timeframe: '4h',
                        total_bars: 6,
                        rsi: 62.1,
                        trend_short: 'bullish',
                        macd_bullish: true,
                        ema_50: 16750.0,
                        volume_above_average: true
                    },
                    '1d': {
                        timeframe: '1d',
                        total_bars: 1,
                        rsi: 58.7,
                        trend_short: 'bullish',
                        sma_20: 16750.0,
                        sma_50: 16680.0,
                        golden_cross: false,
                        death_cross: false
                    }
                },
                chart_data: {
                    '1m': [],
                    '5m': [],
                    '15m': [],
                    '4h': [],
                    '1d': []
                },
                summary: 'Análisis NASDAQ 100 - Tendencia bullish con 72.5% de confianza. Resistencia clave en 16920.50, soporte en 16580.10. RSI en zona neutral sin señales extremas.'
            };

            this.error = 'Mostrando datos de ejemplo. Para ver datos reales, ejecute el script de análisis.';
        },

        loadToday() {
            this.selectedDate = this.getTodayString();
            this.loadAnalysis();
        },

        selectDate(dateString) {
            // Convertir YYYYMMDD a YYYY-MM-DD
            const year = dateString.substring(0, 4);
            const month = dateString.substring(4, 6);
            const day = dateString.substring(6, 8);
            this.selectedDate = `${year}-${month}-${day}`;
            this.loadAnalysis();
        },

        formatDate(dateString) {
            // Convertir YYYYMMDD a formato legible
            const year = dateString.substring(0, 4);
            const month = dateString.substring(4, 6);
            const day = dateString.substring(6, 8);
            const date = new Date(year, month - 1, day);
            return date.toLocaleDateString('es-ES', {
                day: 'numeric',
                month: 'short'
            });
        },

        formatNumber(value) {
            if (value === null || value === undefined) return 'N/A';
            return new Intl.NumberFormat('es-ES', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(value);
        },

        formatVolume(value) {
            if (value === null || value === undefined) return 'N/A';

            if (value >= 1000000000) {
                return (value / 1000000000).toFixed(1) + 'B';
            } else if (value >= 1000000) {
                return (value / 1000000).toFixed(1) + 'M';
            } else if (value >= 1000) {
                return (value / 1000).toFixed(1) + 'K';
            }
            return value.toString();
        },

        formatDateTime(timestamp) {
            if (!timestamp) return 'N/A';
            const date = new Date(timestamp);
            return date.toLocaleString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        formatToPips(value) {
            if (value === null || value === undefined) return 'N/A';
            // Para NAS100, mostrar el precio real con 2 decimales
            // NAS100 no se mide en pips como forex, sino en puntos de índice
            return `${value.toFixed(2)}`;
        },

        initializeDarkMode() {
            // Verificar si hay una preferencia guardada en cookies
            const savedTheme = this.getCookie('darkMode');
            if (savedTheme === 'true') {
                this.isDarkMode = true;
                document.documentElement.classList.add('dark');
            } else if (savedTheme === 'false') {
                this.isDarkMode = false;
                document.documentElement.classList.remove('dark');
            } else {
                // Si no hay preferencia guardada, usar preferencia del sistema
                this.isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (this.isDarkMode) {
                    document.documentElement.classList.add('dark');
                }
            }
        },

        toggleDarkMode() {
            this.isDarkMode = !this.isDarkMode;
            if (this.isDarkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
            // Guardar preferencia en cookie
            this.setCookie('darkMode', this.isDarkMode.toString(), 365);
        },

        setCookie(name, value, days) {
            const expires = new Date();
            expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
            document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
        },

        getCookie(name) {
            const nameEQ = name + '=';
            const ca = document.cookie.split(';');
            for (let i = 0; i < ca.length; i++) {
                let c = ca[i];
                while (c.charAt(0) === ' ') c = c.substring(1, c.length);
                if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
            }
            return null;
        },

        getTrendClass(trend) {
            switch (trend) {
                case 'bullish':
                    return 'trend-bullish';
                case 'bearish':
                    return 'trend-bearish';
                default:
                    return 'trend-neutral';
            }
        },

        getTrendIcon(trend) {
            switch (trend) {
                case 'bullish':
                    return 'fas fa-arrow-up';
                case 'bearish':
                    return 'fas fa-arrow-down';
                default:
                    return 'fas fa-minus';
            }
        },

        getTrendText(trend) {
            switch (trend) {
                case 'bullish':
                    return 'Alcista';
                case 'bearish':
                    return 'Bajista';
                default:
                    return 'Neutral';
            }
        },

        getRSIStatus(rsi) {
            if (rsi === null || rsi === undefined) return 'N/A';

            if (rsi < 30) {
                return 'Sobreventa';
            } else if (rsi > 70) {
                return 'Sobrecompra';
            } else {
                return 'Neutral';
            }
        },

        getRSIColor(rsi) {
            if (!rsi) return 'text-gray-500';
            if (rsi < 30) return 'text-green-600 font-semibold';
            if (rsi > 70) return 'text-red-600 font-semibold';
            return 'text-blue-600';
        },

        setupTimeframeButtons() {
            // Initialize with 15m timeframe
            this.currentTimeframe = '15m';
            this.selectedTimeframe = '15m';
        },

        selectTimeframe() {
            this.updateChart();
        },
        
        changeTimeframe() {
            this.selectTimeframe();
        },

        updateChart() {
            // Destroy existing chart if it exists
            if (this.chart) {
                this.chart.destroy();
            }

            const canvas = document.getElementById('priceChart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            // Generate sample data for demonstration
            const chartData = this.generateSampleChartData();

            // Create chart with actual and forecast data
            const datasets = [];
            
            // Actual data dataset
            if (chartData.actualPrices.some(price => price !== null)) {
                datasets.push({
                    label: 'NASDAQ 100 - Datos Reales (15M)',
                    data: chartData.actualPrices,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    spanGaps: false
                });
            }
            
            // Forecast data dataset
            if (chartData.forecastPrices.some(price => price !== null)) {
                datasets.push({
                    label: 'NASDAQ 100 - Previsión (15M)',
                    data: chartData.forecastPrices,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.1,
                    spanGaps: false
                });
            }
            
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'NASDAQ 100 - 15 Minutos (7:00-22:00)',
                            color: this.isDarkMode ? '#ffffff' : '#374151'
                        },
                        legend: {
                            labels: {
                                color: this.isDarkMode ? '#ffffff' : '#374151'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                color: this.isDarkMode ? '#9ca3af' : '#6b7280'
                            },
                            grid: {
                                color: this.isDarkMode ? '#374151' : '#e5e7eb'
                            }
                        },
                        y: {
                            ticks: {
                                color: this.isDarkMode ? '#9ca3af' : '#6b7280',
                                callback: (value) => {
                                    return this.formatToPips(value);
                                }
                            },
                            grid: {
                                color: this.isDarkMode ? '#374151' : '#e5e7eb'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            });

            // Update chart info
            this.updateChartInfo(chartData);
        },

        generateSampleChartData() {
            const labels = [];
            const actualPrices = [];
            const forecastPrices = [];
            const basePrice = 21750; // Precio base del NAS100 (rango realista)
            
            const now = new Date();
            const currentHour = now.getHours();
            const currentMinute = now.getMinutes();
            
            // Generate 15-minute intervals from 7:00 to 22:00 (15 hours = 60 intervals)
            const startHour = 7;
            const endHour = 22;
            const totalIntervals = (endHour - startHour) * 4; // 4 intervals per hour
            
            // Calculate current position in the trading day
            let currentInterval = 0;
            if (currentHour >= startHour && currentHour < endHour) {
                currentInterval = (currentHour - startHour) * 4 + Math.floor(currentMinute / 15);
            } else if (currentHour >= endHour) {
                currentInterval = totalIntervals;
            }
            
            let currentPrice = basePrice;
            
            // Generate data for all intervals
            for (let i = 0; i < totalIntervals; i++) {
                const hour = startHour + Math.floor(i / 4);
                const minute = (i % 4) * 15;
                const timeLabel = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                labels.push(timeLabel);
                
                if (i <= currentInterval) {
                    // Actual data (past and current)
                    const volatility = 15; // Volatility in pips for 15-minute intervals
                    const change = (Math.random() - 0.5) * volatility;
                    currentPrice += change;
                    actualPrices.push(currentPrice);
                    forecastPrices.push(null);
                } else {
                     // Forecast data (future)
                     const volatility = 12; // Slightly lower volatility for predictions
                     const change = (Math.random() - 0.5) * volatility;
                     currentPrice += change;
                     actualPrices.push(null);
                     forecastPrices.push(currentPrice);
                 }
             }
             
             return {
                 labels: labels,
                 actualPrices: actualPrices,
                 forecastPrices: forecastPrices
             };
        },



        updateChartInfo(data) {
            const chartInfo = document.getElementById('chartInfo');
            if (!chartInfo) return;

            // Combine actual and forecast prices, filtering out nulls
            const actualPrices = data.actualPrices.filter(price => price !== null);
            const forecastPrices = data.forecastPrices.filter(price => price !== null);
            const allPrices = [...actualPrices, ...forecastPrices];
            
            if (allPrices.length === 0) return;

            const lastActualPrice = actualPrices[actualPrices.length - 1] || allPrices[0];
            const firstPrice = actualPrices[0] || allPrices[0];
            const change = lastActualPrice - firstPrice;
            const changePercent = (change / firstPrice) * 100;
            const maxPrice = Math.max(...allPrices);
            const minPrice = Math.min(...allPrices);
            const lastForecastPrice = forecastPrices.length > 0 ? forecastPrices[forecastPrices.length - 1] : null;

            chartInfo.innerHTML = `
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <span class="text-gray-600 dark:text-gray-400">Actual:</span>
                        <span class="font-semibold ml-2">${this.formatToPips(lastActualPrice)}</span>
                    </div>
                    <div>
                        <span class="text-gray-600 dark:text-gray-400">Cambio:</span>
                        <span class="ml-2 ${change >= 0 ? 'text-green-600' : 'text-red-600'} font-semibold">
                            ${change >= 0 ? '+' : ''}${this.formatToPips(change)} (${changePercent.toFixed(2)}%)
                        </span>
                    </div>
                    <div>
                        <span class="text-gray-600 dark:text-gray-400">Máximo:</span>
                        <span class="font-semibold ml-2">${this.formatToPips(maxPrice)}</span>
                    </div>
                    <div>
                        <span class="text-gray-600 dark:text-gray-400">Mínimo:</span>
                        <span class="font-semibold ml-2">${this.formatToPips(minPrice)}</span>
                    </div>
                </div>
                ${lastForecastPrice ? `
                <div class="mt-2 text-sm">
                    <span class="text-gray-600 dark:text-gray-400">Previsión fin de día:</span>
                    <span class="font-semibold ml-2 text-amber-600">${this.formatToPips(lastForecastPrice)}</span>
                </div>
                ` : ''}
                <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Temporalidad: 15M (7:00-22:00) | Datos reales: ${actualPrices.length} | Previsión: ${forecastPrices.length} | Última actualización: ${new Date().toLocaleTimeString()}
                </div>
            `;
        }
    }
}).mount('#app');