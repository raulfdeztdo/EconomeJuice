#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced NASDAQ 100 Technical Analysis Script
Versión mejorada con múltiples fuentes de datos y análisis avanzado
"""

import json
import os
import requests
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import time
import logging
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedNasdaqAnalyzer:
    def __init__(self):
        self.symbol = "^NDX"  # NASDAQ 100 Index
        self.data_dir = "data"
        self.ensure_data_directory()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def ensure_data_directory(self):
        """Crear directorio data si no existe"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Directorio {self.data_dir} creado")

    def get_market_data(self, days_back: int = 60) -> pd.DataFrame:
        """Obtener datos históricos del NASDAQ 100 con manejo de errores mejorado"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Intentar obtener datos con reintentos
            for attempt in range(3):
                try:
                    data = ticker.history(start=start_date, end=end_date, interval='1d')
                    if not data.empty:
                        logger.info(f"Datos obtenidos para {len(data)} días")
                        return data
                except Exception as e:
                    logger.warning(f"Intento {attempt + 1} fallido: {e}")
                    time.sleep(2)

            logger.error("No se pudieron obtener datos después de 3 intentos")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado: {e}")
            return pd.DataFrame()

    def calculate_advanced_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcular indicadores técnicos avanzados"""
        if data.empty:
            return {}

        try:
            indicators = {}

            # RSI (Relative Strength Index)
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi.iloc[-1]) if not rsi.empty else None

            # Medias móviles múltiples
            for period in [10, 20, 50, 200]:
                if len(data) >= period:
                    sma = data['Close'].rolling(window=period).mean()
                    indicators[f'sma_{period}'] = float(sma.iloc[-1]) if not sma.empty else None

                    ema = data['Close'].ewm(span=period).mean()
                    indicators[f'ema_{period}'] = float(ema.iloc[-1]) if not ema.empty else None

            # MACD
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            macd_histogram = macd - macd_signal

            indicators['macd'] = float(macd.iloc[-1]) if not macd.empty else None
            indicators['macd_signal'] = float(macd_signal.iloc[-1]) if not macd_signal.empty else None
            indicators['macd_histogram'] = float(macd_histogram.iloc[-1]) if not macd_histogram.empty else None

            # Bandas de Bollinger
            bb_period = 20
            bb_middle = data['Close'].rolling(window=bb_period).mean()
            bb_std = data['Close'].rolling(window=bb_period).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)

            indicators['bb_upper'] = float(bb_upper.iloc[-1]) if not bb_upper.empty else None
            indicators['bb_middle'] = float(bb_middle.iloc[-1]) if not bb_middle.empty else None
            indicators['bb_lower'] = float(bb_lower.iloc[-1]) if not bb_lower.empty else None

            # Estocástico
            if len(data) >= 14:
                low_14 = data['Low'].rolling(window=14).min()
                high_14 = data['High'].rolling(window=14).max()
                k_percent = 100 * ((data['Close'] - low_14) / (high_14 - low_14))
                d_percent = k_percent.rolling(window=3).mean()

                indicators['stochastic_k'] = float(k_percent.iloc[-1]) if not k_percent.empty else None
                indicators['stochastic_d'] = float(d_percent.iloc[-1]) if not d_percent.empty else None

            # Williams %R
            if len(data) >= 14:
                high_14 = data['High'].rolling(window=14).max()
                low_14 = data['Low'].rolling(window=14).min()
                williams_r = -100 * ((high_14 - data['Close']) / (high_14 - low_14))
                indicators['williams_r'] = float(williams_r.iloc[-1]) if not williams_r.empty else None

            # ATR (Average True Range)
            if len(data) >= 14:
                high_low = data['High'] - data['Low']
                high_close = np.abs(data['High'] - data['Close'].shift())
                low_close = np.abs(data['Low'] - data['Close'].shift())
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = true_range.rolling(window=14).mean()
                indicators['atr'] = float(atr.iloc[-1]) if not atr.empty else None

            # Volumen promedio
            if 'Volume' in data.columns:
                vol_sma_20 = data['Volume'].rolling(window=20).mean()
                indicators['volume_sma_20'] = float(vol_sma_20.iloc[-1]) if not vol_sma_20.empty else None
                indicators['volume_ratio'] = float(data['Volume'].iloc[-1] / vol_sma_20.iloc[-1]) if not vol_sma_20.empty and vol_sma_20.iloc[-1] > 0 else None

            # Datos del último día
            indicators['last_close'] = float(data['Close'].iloc[-1])
            indicators['last_high'] = float(data['High'].iloc[-1])
            indicators['last_low'] = float(data['Low'].iloc[-1])
            indicators['last_volume'] = int(data['Volume'].iloc[-1]) if 'Volume' in data.columns else 0

            # Cambio porcentual
            if len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                indicators['daily_change'] = float((data['Close'].iloc[-1] - prev_close) / prev_close * 100)

            return indicators

        except Exception as e:
            logger.error(f"Error calculando indicadores técnicos: {e}")
            return {}

    def get_market_sentiment(self) -> Dict[str, Any]:
        """Obtener indicadores de sentimiento del mercado"""
        sentiment = {
            'fear_greed_index': None,
            'vix_level': None,
            'market_sentiment': 'neutral'
        }

        try:
            # Obtener VIX (índice de volatilidad)
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="5d")
            if not vix_data.empty:
                vix_current = float(vix_data['Close'].iloc[-1])
                sentiment['vix_level'] = vix_current

                # Interpretar VIX
                if vix_current < 20:
                    sentiment['market_sentiment'] = 'complacent'
                elif vix_current > 30:
                    sentiment['market_sentiment'] = 'fearful'
                else:
                    sentiment['market_sentiment'] = 'neutral'

            # Simular Fear & Greed Index (en producción usar API real)
            if sentiment['vix_level']:
                # Inversamente correlacionado con VIX
                fear_greed = max(0, min(100, 100 - (sentiment['vix_level'] - 10) * 2))
                sentiment['fear_greed_index'] = round(fear_greed, 1)

        except Exception as e:
            logger.error(f"Error obteniendo sentimiento del mercado: {e}")

        return sentiment

    def get_economic_calendar(self) -> List[Dict[str, str]]:
        """Obtener eventos económicos relevantes (simulado)"""
        # En producción, usar APIs como Economic Calendar API, Alpha Vantage, etc.
        events = [
            {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': '14:30',
                'event': 'Datos de empleo no agrícola (NFP)',
                'importance': 'high',
                'forecast': 'TBD',
                'previous': 'TBD'
            },
            {
                'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '20:00',
                'event': 'Decisión de tipos de interés Fed',
                'importance': 'high',
                'forecast': 'Sin cambios',
                'previous': '5.25-5.50%'
            }
        ]

        return events

    def analyze_trend_advanced(self, indicators: Dict[str, Any], sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis de tendencia avanzado con múltiples factores"""
        if not indicators:
            return {'trend': 'neutral', 'confidence': 0, 'signals': [], 'strength': 'weak'}

        signals = []
        bullish_signals = 0
        bearish_signals = 0
        signal_strength = 0

        # Análisis RSI
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:
                signals.append(f'RSI oversold ({rsi:.1f}) - señal alcista fuerte')
                bullish_signals += 2
                signal_strength += 2
            elif rsi < 40:
                signals.append(f'RSI bajo ({rsi:.1f}) - señal alcista moderada')
                bullish_signals += 1
                signal_strength += 1
            elif rsi > 70:
                signals.append(f'RSI overbought ({rsi:.1f}) - señal bajista fuerte')
                bearish_signals += 2
                signal_strength += 2
            elif rsi > 60:
                signals.append(f'RSI alto ({rsi:.1f}) - señal bajista moderada')
                bearish_signals += 1
                signal_strength += 1
            else:
                signals.append(f'RSI neutral ({rsi:.1f})')

        # Análisis MACD
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd and macd_signal:
            if macd > macd_signal and macd > 0:
                signals.append('MACD alcista fuerte - por encima de señal y línea cero')
                bullish_signals += 2
                signal_strength += 2
            elif macd > macd_signal:
                signals.append('MACD alcista - por encima de señal')
                bullish_signals += 1
                signal_strength += 1
            elif macd < macd_signal and macd < 0:
                signals.append('MACD bajista fuerte - por debajo de señal y línea cero')
                bearish_signals += 2
                signal_strength += 2
            else:
                signals.append('MACD bajista - por debajo de señal')
                bearish_signals += 1
                signal_strength += 1

        # Análisis de medias móviles
        close = indicators.get('last_close')
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')

        if close and sma_20:
            if close > sma_20:
                signals.append('Precio por encima de SMA20 - tendencia corto plazo alcista')
                bullish_signals += 1
            else:
                signals.append('Precio por debajo de SMA20 - tendencia corto plazo bajista')
                bearish_signals += 1

        if close and sma_50:
            if close > sma_50:
                signals.append('Precio por encima de SMA50 - tendencia medio plazo alcista')
                bullish_signals += 1
            else:
                signals.append('Precio por debajo de SMA50 - tendencia medio plazo bajista')
                bearish_signals += 1

        if close and sma_200:
            if close > sma_200:
                signals.append('Precio por encima de SMA200 - tendencia largo plazo alcista')
                bullish_signals += 2
                signal_strength += 1
            else:
                signals.append('Precio por debajo de SMA200 - tendencia largo plazo bajista')
                bearish_signals += 2
                signal_strength += 1

        # Análisis de volumen
        volume_ratio = indicators.get('volume_ratio')
        if volume_ratio:
            if volume_ratio > 1.5:
                signals.append(f'Volumen alto ({volume_ratio:.1f}x promedio) - confirmación de movimiento')
                signal_strength += 1
            elif volume_ratio < 0.7:
                signals.append(f'Volumen bajo ({volume_ratio:.1f}x promedio) - falta de convicción')
                signal_strength -= 1

        # Análisis de sentimiento
        vix = sentiment.get('vix_level')
        if vix:
            if vix > 30:
                signals.append(f'VIX alto ({vix:.1f}) - miedo en el mercado, posible rebote')
                bullish_signals += 1
            elif vix < 15:
                signals.append(f'VIX bajo ({vix:.1f}) - complacencia, posible corrección')
                bearish_signals += 1

        # Determinar tendencia y fuerza
        total_signals = bullish_signals + bearish_signals
        if total_signals == 0:
            trend = 'neutral'
            confidence = 50
        elif bullish_signals > bearish_signals:
            trend = 'bullish'
            confidence = min(95, 50 + (bullish_signals / total_signals) * 45)
        else:
            trend = 'bearish'
            confidence = min(95, 50 + (bearish_signals / total_signals) * 45)

        # Determinar fuerza de la señal
        if signal_strength >= 6:
            strength = 'very_strong'
        elif signal_strength >= 4:
            strength = 'strong'
        elif signal_strength >= 2:
            strength = 'moderate'
        else:
            strength = 'weak'

        return {
            'trend': trend,
            'confidence': round(confidence, 1),
            'strength': strength,
            'signals': signals,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'signal_strength': signal_strength
        }

    def predict_daily_levels_advanced(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, float]:
        """Predicción avanzada de niveles de soporte y resistencia"""
        if data.empty or not indicators:
            return {}

        try:
            levels = {}

            # Datos recientes para cálculos
            recent_data = data.tail(20)

            # Niveles basados en Bandas de Bollinger
            bb_upper = indicators.get('bb_upper')
            bb_lower = indicators.get('bb_lower')
            bb_middle = indicators.get('bb_middle')

            if bb_upper and bb_lower:
                levels['bb_resistance'] = bb_upper
                levels['bb_support'] = bb_lower
                levels['bb_middle'] = bb_middle

            # Niveles basados en máximos y mínimos
            recent_high = recent_data['High'].max()
            recent_low = recent_data['Low'].min()

            # Resistencias múltiples
            levels['resistance_1'] = recent_high
            levels['resistance_2'] = recent_high * 1.02
            levels['resistance_3'] = recent_high * 1.05

            # Soportes múltiples
            levels['support_1'] = recent_low
            levels['support_2'] = recent_low * 0.98
            levels['support_3'] = recent_low * 0.95

            # Niveles de retroceso de Fibonacci
            price_range = recent_high - recent_low
            levels['fib_23_6'] = recent_high - (price_range * 0.236)
            levels['fib_38_2'] = recent_high - (price_range * 0.382)
            levels['fib_50_0'] = recent_high - (price_range * 0.500)
            levels['fib_61_8'] = recent_high - (price_range * 0.618)
            levels['fib_78_6'] = recent_high - (price_range * 0.786)

            # Punto pivote y niveles derivados
            last_high = indicators.get('last_high', recent_high)
            last_low = indicators.get('last_low', recent_low)
            last_close = indicators.get('last_close', recent_data['Close'].iloc[-1])

            pivot = (last_high + last_low + last_close) / 3
            levels['pivot_point'] = pivot

            # Resistencias del punto pivote
            levels['r1'] = 2 * pivot - last_low
            levels['r2'] = pivot + (last_high - last_low)
            levels['r3'] = last_high + 2 * (pivot - last_low)

            # Soportes del punto pivote
            levels['s1'] = 2 * pivot - last_high
            levels['s2'] = pivot - (last_high - last_low)
            levels['s3'] = last_low - 2 * (last_high - pivot)

            # Niveles basados en ATR
            atr = indicators.get('atr')
            if atr and last_close:
                levels['atr_resistance'] = last_close + (atr * 2)
                levels['atr_support'] = last_close - (atr * 2)

            # Convertir todos los valores a float
            return {k: float(v) for k, v in levels.items() if v is not None}

        except Exception as e:
            logger.error(f"Error calculando niveles avanzados: {e}")
            return {}

    def generate_trading_signals(self, indicators: Dict[str, Any], trend_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generar señales de trading específicas"""
        signals = []

        try:
            # Señales basadas en RSI
            rsi = indicators.get('rsi')
            if rsi:
                if rsi < 30:
                    signals.append({
                        'type': 'BUY',
                        'strength': 'STRONG',
                        'reason': f'RSI oversold at {rsi:.1f}',
                        'timeframe': 'Short-term'
                    })
                elif rsi > 70:
                    signals.append({
                        'type': 'SELL',
                        'strength': 'STRONG',
                        'reason': f'RSI overbought at {rsi:.1f}',
                        'timeframe': 'Short-term'
                    })

            # Señales basadas en MACD
            macd = indicators.get('macd')
            macd_signal = indicators.get('macd_signal')
            if macd and macd_signal:
                if macd > macd_signal and macd > 0:
                    signals.append({
                        'type': 'BUY',
                        'strength': 'MODERATE',
                        'reason': 'MACD bullish crossover above zero',
                        'timeframe': 'Medium-term'
                    })
                elif macd < macd_signal and macd < 0:
                    signals.append({
                        'type': 'SELL',
                        'strength': 'MODERATE',
                        'reason': 'MACD bearish crossover below zero',
                        'timeframe': 'Medium-term'
                    })

            # Señales basadas en tendencia general
            trend = trend_analysis.get('trend')
            confidence = trend_analysis.get('confidence', 0)
            strength = trend_analysis.get('strength')

            if trend == 'bullish' and confidence > 70:
                signals.append({
                    'type': 'BUY',
                    'strength': strength.upper() if strength else 'MODERATE',
                    'reason': f'Strong bullish trend with {confidence}% confidence',
                    'timeframe': 'Long-term'
                })
            elif trend == 'bearish' and confidence > 70:
                signals.append({
                    'type': 'SELL',
                    'strength': strength.upper() if strength else 'MODERATE',
                    'reason': f'Strong bearish trend with {confidence}% confidence',
                    'timeframe': 'Long-term'
                })

        except Exception as e:
            logger.error(f"Error generando señales de trading: {e}")

        return signals

    def generate_enhanced_analysis(self) -> Dict[str, Any]:
        """Generar análisis completo mejorado"""
        logger.info("Iniciando análisis mejorado del NASDAQ 100")

        # Obtener datos de mercado
        market_data = self.get_market_data()
        if market_data.empty:
            logger.error("No se pudieron obtener datos de mercado")
            return {}

        # Calcular indicadores técnicos avanzados
        indicators = self.calculate_advanced_indicators(market_data)

        # Obtener sentimiento del mercado
        sentiment = self.get_market_sentiment()

        # Análisis de tendencia avanzado
        trend_analysis = self.analyze_trend_advanced(indicators, sentiment)

        # Predicción de niveles avanzada
        daily_levels = self.predict_daily_levels_advanced(market_data, indicators)

        # Generar señales de trading
        trading_signals = self.generate_trading_signals(indicators, trend_analysis)

        # Obtener calendario económico
        economic_events = self.get_economic_calendar()

        # Datos del día anterior
        yesterday_data = {
            'high': float(market_data['High'].iloc[-1]),
            'low': float(market_data['Low'].iloc[-1]),
            'close': float(market_data['Close'].iloc[-1]),
            'volume': int(market_data['Volume'].iloc[-1]) if 'Volume' in market_data.columns else 0,
            'change': indicators.get('daily_change', 0)
        }

        # Compilar análisis completo
        analysis = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'symbol': self.symbol,
            'yesterday_data': yesterday_data,
            'technical_indicators': indicators,
            'market_sentiment': sentiment,
            'trend_analysis': trend_analysis,
            'daily_levels': daily_levels,
            'trading_signals': trading_signals,
            'economic_events': economic_events,
            'news': self.get_market_news(),
            'summary': self.generate_enhanced_summary(trend_analysis, daily_levels, indicators, sentiment),
            'risk_assessment': self.assess_risk(indicators, sentiment, trend_analysis)
        }

        return analysis

    def get_market_news(self) -> List[Dict[str, str]]:
        """Obtener noticias del mercado (versión mejorada)"""
        news = []
        try:
            # En producción, integrar con APIs reales como NewsAPI, Alpha Vantage, etc.
            news.extend([
                {
                    'title': 'Análisis técnico automatizado - NASDAQ 100',
                    'summary': 'Análisis completo basado en múltiples indicadores técnicos y sentimiento del mercado.',
                    'source': 'EconomeJuice Analytics',
                    'timestamp': datetime.now().isoformat(),
                    'category': 'technical_analysis'
                },
                {
                    'title': 'Monitoreo de volatilidad del mercado',
                    'summary': 'Seguimiento continuo de los niveles de volatilidad y su impacto en las decisiones de inversión.',
                    'source': 'Sistema de monitoreo',
                    'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
                    'category': 'market_data'
                }
            ])

        except Exception as e:
            logger.error(f"Error obteniendo noticias: {e}")

        return news

    def generate_enhanced_summary(self, trend_analysis: Dict, daily_levels: Dict, indicators: Dict, sentiment: Dict) -> str:
        """Generar resumen mejorado del análisis"""
        trend = trend_analysis.get('trend', 'neutral')
        confidence = trend_analysis.get('confidence', 0)
        strength = trend_analysis.get('strength', 'moderate')

        summary = f"📊 NASDAQ 100 - Tendencia {trend} ({strength}) con {confidence}% de confianza. "

        # Información de niveles clave
        if daily_levels:
            resistance = daily_levels.get('resistance_1', 0)
            support = daily_levels.get('support_1', 0)
            summary += f"🎯 Resistencia clave: {resistance:.2f}, Soporte: {support:.2f}. "

        # Información de RSI
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:
                summary += f"⚡ RSI oversold ({rsi:.1f}) - oportunidad de compra. "
            elif rsi > 70:
                summary += f"⚠️ RSI overbought ({rsi:.1f}) - precaución. "
            else:
                summary += f"📈 RSI neutral ({rsi:.1f}). "

        # Información de volatilidad
        vix = sentiment.get('vix_level')
        if vix:
            if vix > 25:
                summary += f"😰 Alta volatilidad (VIX: {vix:.1f}) - mercado nervioso. "
            elif vix < 15:
                summary += f"😌 Baja volatilidad (VIX: {vix:.1f}) - mercado tranquilo. "

        # Cambio diario
        daily_change = indicators.get('daily_change')
        if daily_change:
            direction = "📈" if daily_change > 0 else "📉"
            summary += f"{direction} Cambio diario: {daily_change:+.2f}%."

        return summary

    def assess_risk(self, indicators: Dict, sentiment: Dict, trend_analysis: Dict) -> Dict[str, Any]:
        """Evaluar el riesgo del mercado"""
        risk_factors = []
        risk_score = 50  # Neutral

        # Factor de volatilidad
        vix = sentiment.get('vix_level')
        if vix:
            if vix > 30:
                risk_factors.append('Alta volatilidad del mercado')
                risk_score += 20
            elif vix < 15:
                risk_factors.append('Baja volatilidad - posible complacencia')
                risk_score += 10

        # Factor de tendencia
        trend_strength = trend_analysis.get('strength')
        if trend_strength == 'weak':
            risk_factors.append('Tendencia débil - dirección incierta')
            risk_score += 15

        # Factor de RSI extremo
        rsi = indicators.get('rsi')
        if rsi:
            if rsi > 80 or rsi < 20:
                risk_factors.append('RSI en niveles extremos')
                risk_score += 10

        # Determinar nivel de riesgo
        if risk_score >= 80:
            risk_level = 'very_high'
        elif risk_score >= 65:
            risk_level = 'high'
        elif risk_score >= 45:
            risk_level = 'moderate'
        elif risk_score >= 30:
            risk_level = 'low'
        else:
            risk_level = 'very_low'

        return {
            'risk_level': risk_level,
            'risk_score': min(100, max(0, risk_score)),
            'risk_factors': risk_factors,
            'recommendation': self.get_risk_recommendation(risk_level)
        }

    def get_risk_recommendation(self, risk_level: str) -> str:
        """Obtener recomendación basada en el nivel de riesgo"""
        recommendations = {
            'very_low': 'Condiciones favorables para inversión. Considerar aumentar exposición.',
            'low': 'Riesgo controlado. Mantener posiciones actuales.',
            'moderate': 'Riesgo moderado. Diversificar y usar stop-loss.',
            'high': 'Alto riesgo. Reducir exposición y aumentar efectivo.',
            'very_high': 'Riesgo muy alto. Considerar posiciones defensivas.'
        }
        return recommendations.get(risk_level, 'Evaluar cuidadosamente antes de invertir.')

    def save_analysis(self, analysis: Dict[str, Any]) -> str:
        """Guardar análisis en archivo JSON"""
        if not analysis:
            logger.error("No hay análisis para guardar")
            return ""

        filename = f"{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.data_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            logger.info(f"Análisis guardado en {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error guardando análisis: {e}")
            return ""

    def run_enhanced_analysis(self):
        """Ejecutar análisis mejorado completo"""
        try:
            analysis = self.generate_enhanced_analysis()
            if analysis:
                filepath = self.save_analysis(analysis)
                if filepath:
                    logger.info("✅ Análisis mejorado completado exitosamente")

                    # Mostrar resumen en consola
                    print("\n" + "="*60)
                    print("📊 RESUMEN DEL ANÁLISIS NASDAQ 100")
                    print("="*60)
                    print(f"📅 Fecha: {analysis['date']}")
                    print(f"📈 Tendencia: {analysis['trend_analysis']['trend'].upper()}")
                    print(f"🎯 Confianza: {analysis['trend_analysis']['confidence']}%")
                    print(f"💪 Fuerza: {analysis['trend_analysis']['strength'].upper()}")
                    print(f"⚠️  Riesgo: {analysis['risk_assessment']['risk_level'].upper()}")
                    print(f"📝 Resumen: {analysis['summary']}")
                    print("="*60)

                    return True

            logger.error("Falló el análisis mejorado")
            return False
        except Exception as e:
            logger.error(f"Error en análisis mejorado: {e}")
            return False

def main():
    """Función principal"""
    analyzer = EnhancedNasdaqAnalyzer()
    success = analyzer.run_enhanced_analysis()

    if success:
        print("\n✅ Análisis mejorado completado exitosamente")
    else:
        print("\n❌ Error en el análisis mejorado")
        exit(1)

if __name__ == "__main__":
    main()