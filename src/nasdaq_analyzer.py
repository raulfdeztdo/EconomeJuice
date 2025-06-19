#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NASDAQ 100 Technical Analysis Script
Ejecuta análisis técnico diario del NASDAQ 100 y guarda los resultados en JSON
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
from typing import Dict, List, Any
import re
from urllib.parse import urljoin, urlparse
import math

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NasdaqAnalyzer:
    def __init__(self):
        self.symbol = "^NDX"  # NASDAQ 100 Index
        self.data_dir = "data"
        self.ensure_data_directory()
        
    def ensure_data_directory(self):
        """Crear directorio data si no existe"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Directorio {self.data_dir} creado")
    
    def get_market_data(self, days_back: int = 30) -> pd.DataFrame:
        """Obtener datos históricos del NASDAQ 100"""
        try:
            ticker = yf.Ticker(self.symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            data = ticker.history(start=start_date, end=end_date)
            logger.info(f"Datos obtenidos para {len(data)} días")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado: {e}")
            return pd.DataFrame()
    
    def get_intraday_data(self, interval: str = '1m', period: str = '1d') -> pd.DataFrame:
        """Obtener datos intradía para análisis de temporalidades bajas
        
        Args:
            interval: '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '4h', '1d'
            period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        """
        try:
            # Usar NQ=F (NASDAQ 100 Futures) para datos intradía que son más similares a TradingView US 100 Cash CFD
            # NQ=F proporciona valores en el rango de 21,000+ similar a TradingView
            symbol = "NQ=F" if self.symbol == "^NDX" else self.symbol
            
            # Ajustar período según el intervalo para obtener suficientes datos
            if interval in ["1m", "2m", "5m"]:
                period = "1d"
            elif interval in ["15m", "30m", "60m", "90m"]:
                period = "5d"
            elif interval in ["1h", "4h"]:
                period = "60d"
            elif interval == "1d":
                period = "1y"
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No se pudieron obtener datos intradía para {interval}")
                return pd.DataFrame()
            
            logger.info(f"Datos intradía obtenidos: {len(data)} barras de {symbol} para {interval}")
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos intradía {interval}: {e}")
            return pd.DataFrame()
    
    def get_chart_data_for_web(self, interval: str = '1m', period: str = '1d') -> Dict[str, Any]:
        """Obtener datos formateados para gráficos web"""
        try:
            data = self.get_intraday_data(interval, period)
            if data.empty:
                return {}
            
            # Formatear datos para Chart.js
            chart_data = {
                'labels': [dt.strftime('%H:%M') for dt in data.index],
                'datasets': [
                    {
                        'label': f'NASDAQ 100 ({interval})',
                        'data': [{
                            'x': dt.strftime('%H:%M'),
                            'o': float(row['Open']),
                            'h': float(row['High']),
                            'l': float(row['Low']),
                            'c': float(row['Close'])
                        } for dt, row in data.iterrows()],
                        'borderColor': 'rgb(75, 192, 192)',
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)'
                    }
                ],
                'volume_data': [{
                    'x': dt.strftime('%H:%M'),
                    'y': int(row['Volume'])
                } for dt, row in data.iterrows()]
            }
            
            return chart_data
        except Exception as e:
            logger.error(f"Error preparando datos para gráfico: {e}")
            return {}
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcular indicadores técnicos avanzados"""
        if data.empty:
            return {}
        
        try:
            # RSI (Relative Strength Index)
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Medias móviles múltiples - CORREGIDO: Asegurar que se calculen correctamente
            sma_10 = data['Close'].rolling(window=10).mean()
            sma_20 = data['Close'].rolling(window=20).mean()
            sma_50 = data['Close'].rolling(window=50).mean() if len(data) >= 50 else pd.Series([None] * len(data), index=data.index)
            sma_200 = data['Close'].rolling(window=200).mean() if len(data) >= 200 else pd.Series([None] * len(data), index=data.index)
            ema_12 = data['Close'].ewm(span=12).mean()
            ema_26 = data['Close'].ewm(span=26).mean()
            ema_50 = data['Close'].ewm(span=50).mean() if len(data) >= 50 else pd.Series([None] * len(data), index=data.index)
            ema_100 = data['Close'].ewm(span=100).mean() if len(data) >= 100 else pd.Series([None] * len(data), index=data.index)
            
            # MACD
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            macd_histogram = macd - macd_signal
            
            # Bandas de Bollinger
            bb_middle = sma_20
            bb_std = data['Close'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_width = ((bb_upper - bb_lower) / bb_middle) * 100
            
            # Stochastic Oscillator
            low_14 = data['Low'].rolling(window=14).min()
            high_14 = data['High'].rolling(window=14).max()
            k_percent = 100 * ((data['Close'] - low_14) / (high_14 - low_14))
            d_percent = k_percent.rolling(window=3).mean()
            
            # Williams %R
            williams_r = -100 * ((high_14 - data['Close']) / (high_14 - low_14))
            
            # Average True Range (ATR)
            high_low = data['High'] - data['Low']
            high_close = np.abs(data['High'] - data['Close'].shift())
            low_close = np.abs(data['Low'] - data['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()
            
            # ADX (Average Directional Index) - NUEVO
            def calculate_adx(high, low, close, period=14):
                plus_dm = high.diff()
                minus_dm = low.diff()
                plus_dm[plus_dm < 0] = 0
                minus_dm[minus_dm > 0] = 0
                minus_dm = minus_dm.abs()
                
                tr_smooth = true_range.rolling(window=period).mean()
                plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr_smooth)
                minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr_smooth)
                
                dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
                adx = dx.rolling(window=period).mean()
                
                return adx, plus_di, minus_di
            
            adx, plus_di, minus_di = calculate_adx(data['High'], data['Low'], data['Close'])
            
            # Volume indicators - CORREGIDO: RVOL y lógica mejorada
            volume_sma = data['Volume'].rolling(window=20).mean()
            volume_std = data['Volume'].rolling(window=20).std()
            average_volume = volume_sma.iloc[-1] if not volume_sma.empty else 0
            volume_std_dev = volume_std.iloc[-1] if not volume_std.empty else 0
            current_volume = data['Volume'].iloc[-1]
            
            # RVOL (Relative Volume) - CORREGIDO
            rvol = current_volume / average_volume if average_volume > 0 else 1
            volume_above_average = rvol > 1.5  # CORREGIDO: usar RVOL > 1.5
            volume_spike = rvol > 2.0  # Spike cuando RVOL > 2.0
            
            # Big Print Detection (órdenes grandes)
            volume_percentile_95 = data['Volume'].rolling(window=50).quantile(0.95).iloc[-1] if len(data) >= 50 else current_volume
            big_print_detected = current_volume > volume_percentile_95
            
            # On-Balance Volume (OBV)
            obv = (np.sign(data['Close'].diff()) * data['Volume']).fillna(0).cumsum()
            
            # Commodity Channel Index (CCI)
            typical_price = (data['High'] + data['Low'] + data['Close']) / 3
            sma_tp = typical_price.rolling(window=20).mean()
            mad = typical_price.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
            cci = (typical_price - sma_tp) / (0.015 * mad)
            
            # Money Flow Index (MFI)
            typical_price_mfi = (data['High'] + data['Low'] + data['Close']) / 3
            money_flow = typical_price_mfi * data['Volume']
            positive_flow = money_flow.where(typical_price_mfi > typical_price_mfi.shift(), 0).rolling(window=14).sum()
            negative_flow = money_flow.where(typical_price_mfi < typical_price_mfi.shift(), 0).rolling(window=14).sum()
            mfi = 100 - (100 / (1 + (positive_flow / negative_flow)))
            
            # Análisis de Gaps - NUEVO
            def detect_gaps(data):
                gaps = []
                if len(data) > 1:
                    prev_close = data['Close'].iloc[-2]
                    current_open = data['Open'].iloc[-1] if 'Open' in data.columns else data['Close'].iloc[-1]
                    
                    gap_size = abs(current_open - prev_close)
                    gap_percentage = (gap_size / prev_close) * 100
                    
                    if gap_percentage > 0.5:  # Gap significativo > 0.5%
                        gap_type = 'up' if current_open > prev_close else 'down'
                        gaps.append({
                            'type': gap_type,
                            'size': gap_size,
                            'percentage': gap_percentage,
                            'support_resistance_level': (prev_close + current_open) / 2
                        })
                return gaps
            
            gaps = detect_gaps(data)
            
            # Volatilidad mejorada - NUEVO
            price_changes = data['Close'].pct_change().dropna()
            volatility_std = price_changes.rolling(window=20).std().iloc[-1] * 100 if len(price_changes) > 20 else 0
            daily_range_pct = ((data['High'].iloc[-1] - data['Low'].iloc[-1]) / data['Close'].iloc[-1]) * 100
            
            # Último día de datos
            last_close = data['Close'].iloc[-1]
            last_high = data['High'].iloc[-1]
            last_low = data['Low'].iloc[-1]
            last_volume = data['Volume'].iloc[-1]
            
            return {
                # Indicadores básicos
                'rsi': float(rsi.iloc[-1]) if not rsi.empty else None,
                'rsi_oversold': int(float(rsi.iloc[-1]) < 30) if not rsi.empty else 0,
                'rsi_overbought': int(float(rsi.iloc[-1]) > 70) if not rsi.empty else 0,
                
                # Medias móviles - CORREGIDO
                'sma_10': float(sma_10.iloc[-1]) if not sma_10.empty else None,
                'sma_20': float(sma_20.iloc[-1]) if not sma_20.empty else None,
                'sma_50': float(sma_50.iloc[-1]) if not sma_50.empty and not pd.isna(sma_50.iloc[-1]) else None,
                'sma_200': float(sma_200.iloc[-1]) if not sma_200.empty and not pd.isna(sma_200.iloc[-1]) else None,
                'ema_12': float(ema_12.iloc[-1]) if not ema_12.empty else None,
                'ema_26': float(ema_26.iloc[-1]) if not ema_26.empty else None,
                'ema_50': float(ema_50.iloc[-1]) if not ema_50.empty and not pd.isna(ema_50.iloc[-1]) else None,
                'ema_100': float(ema_100.iloc[-1]) if not ema_100.empty and not pd.isna(ema_100.iloc[-1]) else None,
                
                # MACD
                'macd': float(macd.iloc[-1]) if not macd.empty else None,
                'macd_signal': float(macd_signal.iloc[-1]) if not macd_signal.empty else None,
                'macd_histogram': float(macd_histogram.iloc[-1]) if not macd_histogram.empty else None,
                'macd_bullish': int(float(macd.iloc[-1]) > float(macd_signal.iloc[-1])) if not macd.empty and not macd_signal.empty else 0,
                
                # Bandas de Bollinger
                'bb_upper': float(bb_upper.iloc[-1]) if not bb_upper.empty else None,
                'bb_middle': float(bb_middle.iloc[-1]) if not bb_middle.empty else None,
                'bb_lower': float(bb_lower.iloc[-1]) if not bb_lower.empty else None,
                'bb_width': float(bb_width.iloc[-1]) if not bb_width.empty else None,
                'bb_squeeze': int(float(bb_width.iloc[-1]) < 10) if not bb_width.empty else 0,
                
                # Osciladores
                'stoch_k': float(k_percent.iloc[-1]) if not k_percent.empty else None,
                'stoch_d': float(d_percent.iloc[-1]) if not d_percent.empty else None,
                'williams_r': float(williams_r.iloc[-1]) if not williams_r.empty else None,
                'cci': float(cci.iloc[-1]) if not cci.empty else None,
                'mfi': float(mfi.iloc[-1]) if not mfi.empty else None,
                
                # ADX - CORREGIDO: lógica de tendencia fuerte
                'adx': float(adx.iloc[-1]) if not adx.empty and not pd.isna(adx.iloc[-1]) else None,
                'plus_di': float(plus_di.iloc[-1]) if not plus_di.empty and not pd.isna(plus_di.iloc[-1]) else None,
                'minus_di': float(minus_di.iloc[-1]) if not minus_di.empty and not pd.isna(minus_di.iloc[-1]) else None,
                'adx_trend_strength': 'strong' if not adx.empty and not pd.isna(adx.iloc[-1]) and adx.iloc[-1] > 25 else 'weak' if not adx.empty and not pd.isna(adx.iloc[-1]) else 'unknown',
                'trend_is_strong': int(not adx.empty and not pd.isna(adx.iloc[-1]) and adx.iloc[-1] > 20),  # CORREGIDO: tendencia fuerte si ADX > 20
                
                # Volatilidad - MEJORADO
                'atr': float(atr.iloc[-1]) if not atr.empty else None,
                'volatility_high': int(float(atr.iloc[-1]) > float(atr.rolling(window=20).mean().iloc[-1])) if not atr.empty else 0,
                'volatility_std': float(volatility_std) if volatility_std else 0,
                'daily_range_pct': float(daily_range_pct) if daily_range_pct else 0,
                
                # Análisis de Gaps - NUEVO
                'gaps_detected': len(gaps),
                'gap_info': gaps[0] if gaps else None,
                
                # Volumen - CORREGIDO: RVOL y nuevos indicadores
                'rvol': float(rvol) if rvol else 1,  # NUEVO: Relative Volume
                'volume_above_average': int(volume_above_average),  # CORREGIDO: basado en RVOL > 1.5
                'volume_spike': int(volume_spike),  # CORREGIDO: basado en RVOL > 2.0
                'big_print_detected': int(big_print_detected),  # NUEVO: detección de órdenes grandes
                'average_volume': float(average_volume) if average_volume else 0,
                'volume_std_dev': float(volume_std_dev) if volume_std_dev else 0,
                'volume_percentile_95': float(volume_percentile_95) if 'volume_percentile_95' in locals() else 0,
                'obv': float(obv.iloc[-1]) if not obv.empty else None,
                'obv_trend': 'bullish' if len(obv) > 5 and obv.iloc[-1] > obv.iloc[-5] else 'bearish' if len(obv) > 5 else 'neutral',
                
                # Datos del último día
                'last_close': float(last_close),
                'last_high': float(last_high),
                'last_low': float(last_low),
                'last_volume': int(last_volume),
                'daily_range': float(last_high - last_low),
                'daily_change': float(data['Close'].iloc[-1] - data['Close'].iloc[-2]) if len(data) > 1 else 0,
                'daily_change_pct': float(((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100) if len(data) > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error calculando indicadores técnicos: {e}")
            return {}
    
    def calculate_probabilistic_analysis(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis probabilístico básico usando regresión lineal - NUEVO"""
        if data.empty or not indicators:
            return {}
        
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.preprocessing import StandardScaler
            import warnings
            warnings.filterwarnings('ignore')
            
            # Preparar features para el modelo
            features = []
            feature_names = []
            
            # RSI
            if indicators.get('rsi') is not None:
                features.append(indicators['rsi'])
                feature_names.append('rsi')
            
            # MACD
            if indicators.get('macd') is not None:
                features.append(indicators['macd'])
                feature_names.append('macd')
            
            # OBV trend (convertir a numérico)
            obv_trend = indicators.get('obv_trend', 'neutral')
            obv_numeric = 1 if obv_trend == 'bullish' else -1 if obv_trend == 'bearish' else 0
            features.append(obv_numeric)
            feature_names.append('obv_trend')
            
            # Precio relativo a medias móviles
            current_price = indicators.get('last_close', 0)
            sma_20 = indicators.get('sma_20')
            if sma_20 and current_price:
                price_vs_sma20 = (current_price - sma_20) / sma_20 * 100
                features.append(price_vs_sma20)
                feature_names.append('price_vs_sma20')
            
            # ADX para fuerza de tendencia
            if indicators.get('adx') is not None:
                features.append(indicators['adx'])
                feature_names.append('adx')
            
            # Volumen relativo
            volume_ratio = indicators.get('volume_ratio', 1)
            features.append(volume_ratio)
            feature_names.append('volume_ratio')
            
            # Volatilidad
            volatility_std = indicators.get('volatility_std', 0)
            features.append(volatility_std)
            feature_names.append('volatility_std')
            
            if len(features) < 3:
                return {'error': 'Insuficientes features para análisis probabilístico'}
            
            # Crear datos históricos para entrenamiento (simulado)
            # En producción, esto usaría datos históricos reales
            np.random.seed(42)  # Para reproducibilidad
            n_samples = 100
            
            # Generar datos sintéticos basados en los features actuales
            X_train = []
            y_train = []
            
            for i in range(n_samples):
                # Generar variaciones de los features actuales
                sample_features = []
                for j, feature in enumerate(features):
                    if feature_names[j] == 'rsi':
                        sample_features.append(np.random.normal(feature, 10))
                    elif feature_names[j] == 'macd':
                        sample_features.append(np.random.normal(feature, feature * 0.2))
                    elif feature_names[j] == 'obv_trend':
                        sample_features.append(np.random.choice([-1, 0, 1]))
                    elif feature_names[j] == 'price_vs_sma20':
                        sample_features.append(np.random.normal(feature, 2))
                    elif feature_names[j] == 'adx':
                        sample_features.append(np.random.normal(feature, 5))
                    elif feature_names[j] == 'volume_ratio':
                        sample_features.append(np.random.normal(feature, 0.3))
                    else:
                        sample_features.append(np.random.normal(feature, feature * 0.1))
                
                X_train.append(sample_features)
                
                # Generar target basado en lógica de trading
                rsi_val = sample_features[0] if 'rsi' in feature_names else 50
                macd_val = sample_features[1] if 'macd' in feature_names else 0
                obv_val = sample_features[2] if 'obv_trend' in feature_names else 0
                
                # Lógica simplificada para determinar ruptura
                bullish_score = 0
                if rsi_val < 30: bullish_score += 2
                elif rsi_val < 50: bullish_score += 1
                if macd_val > 0: bullish_score += 1
                if obv_val > 0: bullish_score += 1
                
                # 1 = ruptura alcista, 0 = neutral, -1 = ruptura bajista
                if bullish_score >= 3:
                    y_train.append(1)
                elif bullish_score <= 1:
                    y_train.append(-1)
                else:
                    y_train.append(0)
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # Entrenar modelo
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # Predecir con features actuales
            current_features = np.array(features).reshape(1, -1)
            current_features_scaled = scaler.transform(current_features)
            prediction = model.predict(current_features_scaled)[0]
            
            # Convertir predicción a probabilidades
            if prediction > 0.5:
                bullish_prob = min(95, 50 + prediction * 30)
                bearish_prob = 100 - bullish_prob
                trend_prediction = 'bullish'
            elif prediction < -0.5:
                bearish_prob = min(95, 50 + abs(prediction) * 30)
                bullish_prob = 100 - bearish_prob
                trend_prediction = 'bearish'
            else:
                bullish_prob = 50
                bearish_prob = 50
                trend_prediction = 'neutral'
            
            return {
                'trend_prediction': trend_prediction,
                'bullish_probability': round(bullish_prob, 1),
                'bearish_probability': round(bearish_prob, 1),
                'prediction_confidence': round(abs(prediction) * 100, 1),
                'features_used': feature_names,
                'model_score': round(model.score(X_train_scaled, y_train), 3)
            }
            
        except ImportError:
            return {'error': 'sklearn no disponible para análisis probabilístico'}
        except Exception as e:
            logger.error(f"Error en análisis probabilístico: {e}")
            return {'error': str(e)}
    
    def calculate_intraday_indicators(self, data: pd.DataFrame, timeframe: str = '1m') -> Dict[str, Any]:
        """Calcular indicadores técnicos específicos para temporalidades bajas"""
        if data.empty:
            return {}
        
        try:
            # Ajustar períodos según la temporalidad
            if timeframe == '1m':
                rsi_period = 14
                sma_fast = 9
                sma_slow = 21
                ema_fast = 8
                ema_slow = 13
                macd_fast = 12
                macd_slow = 26
                macd_signal = 9
                bb_period = 20
                atr_period = 14
            elif timeframe == '5m':
                rsi_period = 14
                sma_fast = 20
                sma_slow = 50
                ema_fast = 12
                ema_slow = 26
                macd_fast = 12
                macd_slow = 26
                macd_signal = 9
                bb_period = 20
                atr_period = 14
            elif timeframe == '15m':
                rsi_period = 14
                sma_fast = 20
                sma_slow = 50
                ema_fast = 12
                ema_slow = 26
                macd_fast = 12
                macd_slow = 26
                macd_signal = 9
                bb_period = 20
                atr_period = 14
            elif timeframe == '4h':
                rsi_period = 14
                sma_fast = 20
                sma_slow = 50
                ema_fast = 12
                ema_slow = 26
                macd_fast = 12
                macd_slow = 26
                macd_signal = 9
                bb_period = 20
                atr_period = 14
            elif timeframe == '1d':
                rsi_period = 14
                sma_fast = 20
                sma_slow = 50
                ema_fast = 12
                ema_slow = 26
                macd_fast = 12
                macd_slow = 26
                macd_signal = 9
                bb_period = 20
                atr_period = 14
            else:
                # Valores por defecto
                rsi_period = 14
                sma_fast = 20
                sma_slow = 50
                ema_fast = 12
                ema_slow = 26
                macd_fast = 12
                macd_slow = 26
                macd_signal = 9
                bb_period = 20
                atr_period = 14
            
            # RSI adaptado
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Medias móviles para scalping
            sma_fast_line = data['Close'].rolling(window=sma_fast).mean()
            sma_slow_line = data['Close'].rolling(window=sma_slow).mean()
            ema_fast_line = data['Close'].ewm(span=ema_fast).mean()
            ema_slow_line = data['Close'].ewm(span=ema_slow).mean()
            
            # MACD para momentum intradía
            ema_12 = data['Close'].ewm(span=macd_fast).mean()
            ema_26 = data['Close'].ewm(span=macd_slow).mean()
            macd_line = ema_12 - ema_26
            macd_signal_line = macd_line.ewm(span=macd_signal).mean()
            macd_histogram = macd_line - macd_signal_line
            
            # Bandas de Bollinger para volatilidad
            bb_middle = data['Close'].rolling(window=bb_period).mean()
            bb_std = data['Close'].rolling(window=bb_period).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            # ATR para stop loss dinámico
            high_low = data['High'] - data['Low']
            high_close = np.abs(data['High'] - data['Close'].shift())
            low_close = np.abs(data['Low'] - data['Close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=atr_period).mean()
            
            # Stochastic rápido para entradas
            low_14 = data['Low'].rolling(window=14).min()
            high_14 = data['High'].rolling(window=14).max()
            k_percent = 100 * ((data['Close'] - low_14) / (high_14 - low_14))
            d_percent = k_percent.rolling(window=3).mean()
            
            # Análisis de momentum intradía
            price_change = data['Close'].pct_change()
            momentum_5 = data['Close'].pct_change(5) * 100
            momentum_10 = data['Close'].pct_change(10) * 100
            
            # Niveles de soporte y resistencia intradía
            recent_high = data['High'].rolling(window=20).max()
            recent_low = data['Low'].rolling(window=20).min()
            
            # Análisis de volumen para confirmación
            volume_sma = data['Volume'].rolling(window=20).mean()
            volume_ratio = data['Volume'] / volume_sma
            
            # Señales de trading específicas para scalping
            current_price = data['Close'].iloc[-1]
            
            # Señal de cruce de EMAs
            ema_bullish_cross = (ema_fast_line.iloc[-1] > ema_slow_line.iloc[-1] and 
                               ema_fast_line.iloc[-2] <= ema_slow_line.iloc[-2])
            ema_bearish_cross = (ema_fast_line.iloc[-1] < ema_slow_line.iloc[-1] and 
                               ema_fast_line.iloc[-2] >= ema_slow_line.iloc[-2])
            
            # Señales de RSI para scalping
            rsi_current = rsi.iloc[-1]
            rsi_oversold_scalp = rsi_current < 25  # Más estricto para scalping
            rsi_overbought_scalp = rsi_current > 75
            
            # Señales de Bollinger Bands
            bb_squeeze = (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1] < 0.02
            price_near_upper_bb = current_price > bb_upper.iloc[-1] * 0.98
            price_near_lower_bb = current_price < bb_lower.iloc[-1] * 1.02
            
            # Señales de scalping mejoradas
            rsi_current = rsi.iloc[-1] if not rsi.empty else 50
            
            # Condiciones para señal de compra
            macd_histogram_positive = macd_histogram.iloc[-1] > 0 if not macd_histogram.empty else False
            
            scalp_buy_conditions = [
                rsi_current < 35,  # RSI oversold pero no extremo
                macd_histogram_positive,  # MACD histogram cruzando positivo
                price_near_lower_bb or (current_price < bb_middle.iloc[-1] * 0.999) if not bb_middle.empty else False,  # Precio cerca del soporte
                not bb_squeeze  # No en squeeze
            ]
            
            # Condiciones para señal de venta
            macd_histogram_negative = macd_histogram.iloc[-1] < 0 if not macd_histogram.empty else False
            
            scalp_sell_conditions = [
                rsi_current > 65,  # RSI overbought pero no extremo
                macd_histogram_negative,  # MACD histogram cruzando negativo
                price_near_upper_bb or (current_price > bb_middle.iloc[-1] * 1.001) if not bb_middle.empty else False,  # Precio cerca de resistencia
                not bb_squeeze  # No en squeeze
            ]
            
            # Activar señal si se cumplen al menos 2 de 4 condiciones
            scalp_buy_signal = sum(scalp_buy_conditions) >= 2
            scalp_sell_signal = sum(scalp_sell_conditions) >= 2
            
            # Construir el resultado completo
            result = {
                'timeframe': timeframe,
                'total_bars': len(data),
                
                # Indicadores básicos
                'rsi': float(rsi.iloc[-1]) if not rsi.empty else None,
                'rsi_oversold_scalp': int(rsi_oversold_scalp),
                'rsi_overbought_scalp': int(rsi_overbought_scalp),
                
                # Medias móviles
                'sma_fast': float(sma_fast_line.iloc[-1]) if not sma_fast_line.empty and not pd.isna(sma_fast_line.iloc[-1]) else None,
                'sma_slow': float(sma_slow_line.iloc[-1]) if not sma_slow_line.empty and not pd.isna(sma_slow_line.iloc[-1]) else None,
                'ema_fast': float(ema_fast_line.iloc[-1]) if not ema_fast_line.empty and not pd.isna(ema_fast_line.iloc[-1]) else None,
                'ema_slow': float(ema_slow_line.iloc[-1]) if not ema_slow_line.empty and not pd.isna(ema_slow_line.iloc[-1]) else None,
                
                # Señales de cruce
                'ema_bullish_cross': int(ema_bullish_cross),
                'ema_bearish_cross': int(ema_bearish_cross),
                
                # MACD
                'macd': float(macd_line.iloc[-1]) if not macd_line.empty else None,
                'macd_signal': float(macd_signal_line.iloc[-1]) if not macd_signal_line.empty else None,
                'macd_histogram': float(macd_histogram.iloc[-1]) if not macd_histogram.empty else None,
                'macd_bullish': int(macd_line.iloc[-1] > macd_signal_line.iloc[-1]) if not macd_line.empty else 0,
                
                # Bandas de Bollinger
                'bb_upper': float(bb_upper.iloc[-1]) if not bb_upper.empty else None,
                'bb_middle': float(bb_middle.iloc[-1]) if not bb_middle.empty else None,
                'bb_lower': float(bb_lower.iloc[-1]) if not bb_lower.empty else None,
                'bb_squeeze': int(bb_squeeze),
                'price_near_upper_bb': int(price_near_upper_bb),
                'price_near_lower_bb': int(price_near_lower_bb),
                
                # ATR para stop loss
                'atr': float(atr.iloc[-1]) if not atr.empty else None,
                'atr_stop_long': float(current_price - (atr.iloc[-1] * 1.5)) if not atr.empty else None,
                'atr_stop_short': float(current_price + (atr.iloc[-1] * 1.5)) if not atr.empty else None,
                
                # Stochastic
                'stoch_k': float(k_percent.iloc[-1]) if not k_percent.empty else None,
                'stoch_d': float(d_percent.iloc[-1]) if not d_percent.empty else None,
                'stoch_oversold': int(k_percent.iloc[-1] < 20) if not k_percent.empty else 0,
                'stoch_overbought': int(k_percent.iloc[-1] > 80) if not k_percent.empty else 0,
                
                # Momentum
                'momentum_5': float(momentum_5.iloc[-1]) if not momentum_5.empty else None,
                'momentum_10': float(momentum_10.iloc[-1]) if not momentum_10.empty else None,
                
                # Niveles clave
                'resistance_level': float(recent_high.iloc[-1]) if not recent_high.empty else None,
                'support_level': float(recent_low.iloc[-1]) if not recent_low.empty else None,
                
                # Volumen
                'volume_ratio': float(volume_ratio.iloc[-1]) if not volume_ratio.empty else None,
                'volume_spike': int(volume_ratio.iloc[-1] > 2) if not volume_ratio.empty else 0,
                
                # Datos actuales
                'current_price': float(current_price),
                'current_high': float(data['High'].iloc[-1]),
                'current_low': float(data['Low'].iloc[-1]),
                'current_volume': int(data['Volume'].iloc[-1]),
                
                # Análisis de tendencia intradía
                'trend_short': 'bullish' if ema_fast_line.iloc[-1] > ema_slow_line.iloc[-1] else 'bearish',
                'price_above_vwap': int(current_price > bb_middle.iloc[-1]) if not bb_middle.empty else 0,
                
                # Señales de scalping
                'scalp_buy_signal': int(scalp_buy_signal),
                'scalp_sell_signal': int(scalp_sell_signal),
                'range_trading': int(bb_squeeze)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculando indicadores intradía: {e}")
            return {}
    
    def get_market_news(self) -> List[Dict[str, str]]:
        """Obtener noticias relevantes del mercado desde múltiples fuentes con enlaces reales"""
        news = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Fuente 1: Investing.com NASDAQ 100 News - MEJORADO
        try:
            logger.info("Obteniendo noticias específicas del NASDAQ 100...")
            
            # URLs específicas para NASDAQ 100
            nasdaq_urls = [
                'https://es.investing.com/indices/nq-100-news',
                'https://es.investing.com/news/technology-news',
                'https://es.investing.com/news/stock-market-news'
            ]
            
            for url in nasdaq_urls:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Buscar artículos con selectores más específicos
                        articles = soup.find_all(['article', 'div'], class_=re.compile(r'.*article.*|.*news.*|.*story.*|.*item.*', re.I))
                        
                        for article in articles[:2]:  # 2 noticias por fuente
                            title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'.*title.*|.*headline.*', re.I))
                            if not title_elem:
                                title_elem = article.find('a')
                            
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                
                                # Filtrar noticias relevantes para NASDAQ/tecnología
                                relevant_keywords = ['nasdaq', 'technology', 'tech', 'apple', 'microsoft', 'google', 
                                                   'amazon', 'tesla', 'meta', 'nvidia', 'netflix', 'fed', 'inflation',
                                                   'earnings', 'market', 'stock', 'índice', 'tecnología']
                                
                                if any(keyword.lower() in title.lower() for keyword in relevant_keywords):
                                    # Obtener enlace real
                                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                                    if not link_elem:
                                        link_elem = article.find('a')
                                    
                                    article_url = ''
                                    if link_elem and link_elem.get('href'):
                                        href = link_elem.get('href')
                                        if href.startswith('http'):
                                            article_url = href
                                        elif href.startswith('/'):
                                            article_url = 'https://es.investing.com' + href
                                        else:
                                            article_url = 'https://es.investing.com/' + href
                                    
                                    if title and len(title) > 15:  # Filtrar títulos muy cortos
                                        summary_elem = article.find(['p', 'div'], class_=re.compile(r'.*summary.*|.*excerpt.*|.*description.*', re.I))
                                        summary = summary_elem.get_text(strip=True) if summary_elem else title[:200] + '...'
                                        
                                        news.append({
                                            'title': title[:150],
                                            'summary': summary[:300],
                                            'source': 'Investing.com',
                                            'url': article_url,
                                            'timestamp': datetime.now().isoformat(),
                                            'relevance': 'high',
                                            'category': 'nasdaq_tech'
                                        })
                                        
                except Exception as e:
                    logger.warning(f"Error obteniendo noticias de {url}: {e}")
                    continue
                            
        except Exception as e:
            logger.warning(f"Error general obteniendo noticias de Investing.com: {e}")
        
        # Fuente 2: FinancialJuice
        try:
            logger.info("Obteniendo noticias de FinancialJuice...")
            response = requests.get('https://www.financialjuice.com/home', 
                                  headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar contenido de noticias financieras
                articles = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'.*news.*|.*article.*|.*post.*', re.I))
                
                for article in articles[:2]:  # Limitar a 2 noticias
                    title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        
                        # Obtener enlace real
                        link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                        if not link_elem:
                            link_elem = article.find('a')
                        
                        article_url = ''
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            if href.startswith('http'):
                                article_url = href
                            elif href.startswith('/'):
                                article_url = 'https://www.financialjuice.com' + href
                            else:
                                article_url = 'https://www.financialjuice.com/' + href
                        
                        if title and len(title) > 10:
                            summary_elem = article.find(['p', 'div'])
                            summary = summary_elem.get_text(strip=True) if summary_elem else title[:200] + '...'
                            
                            news.append({
                                'title': title[:150],
                                'summary': summary[:300],
                                'source': 'FinancialJuice',
                                'url': article_url,
                                'timestamp': datetime.now().isoformat(),
                                'relevance': 'medium'
                            })
                            
        except Exception as e:
            logger.warning(f"Error obteniendo noticias de FinancialJuice: {e}")
        
        # Fuente 3: Análisis de sentimiento del mercado
        try:
            # Obtener datos del VIX para sentimiento del mercado
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="5d")
            
            if not vix_data.empty:
                current_vix = vix_data['Close'].iloc[-1]
                prev_vix = vix_data['Close'].iloc[-2] if len(vix_data) > 1 else current_vix
                vix_change = current_vix - prev_vix
                
                sentiment = "neutral"
                if current_vix > 30:
                    sentiment = "fearful"
                elif current_vix < 15:
                    sentiment = "greedy"
                
                news.append({
                    'title': f'Índice de Volatilidad VIX: {current_vix:.2f} ({vix_change:+.2f})',
                    'summary': f'El VIX indica un sentimiento de mercado {sentiment}. Niveles actuales suggen {"alta volatilidad" if current_vix > 25 else "baja volatilidad" if current_vix < 15 else "volatilidad moderada"}.',
                    'source': 'Análisis VIX',
                    'timestamp': datetime.now().isoformat(),
                    'relevance': 'high',
                    'sentiment': sentiment
                })
                
        except Exception as e:
            logger.warning(f"Error obteniendo datos del VIX: {e}")
        
        # Fuente 4: Eventos económicos simulados
        try:
            economic_events = [
                {
                    'title': 'Datos de Empleo No Agrícola (NFP) - Próxima publicación',
                    'summary': 'Los datos de empleo estadounidense son clave para el sentimiento del mercado tecnológico.',
                    'source': 'Calendario Económico',
                    'relevance': 'high'
                },
                {
                    'title': 'Decisión de Tipos de Interés de la Fed',
                    'summary': 'Las decisiones de política monetaria impactan directamente en las valoraciones tecnológicas.',
                    'source': 'Calendario Económico',
                    'relevance': 'high'
                },
                {
                    'title': 'Resultados Trimestrales de Empresas Tecnológicas',
                    'summary': 'Los resultados de las principales empresas del NASDAQ 100 influyen en la dirección del índice.',
                    'source': 'Calendario Económico',
                    'relevance': 'medium'
                }
            ]
            
            # Agregar un evento aleatorio
            import random
            selected_event = random.choice(economic_events)
            selected_event['timestamp'] = datetime.now().isoformat()
            news.append(selected_event)
            
        except Exception as e:
            logger.warning(f"Error generando eventos económicos: {e}")
        
        # Si no se obtuvieron noticias, agregar análisis por defecto
        if not news:
            news.append({
                'title': 'Análisis técnico automático del NASDAQ 100',
                'summary': 'Sistema de análisis técnico automatizado recopilando datos de múltiples fuentes para proporcionar insights del mercado.',
                'source': 'Sistema Automático',
                'timestamp': datetime.now().isoformat(),
                'relevance': 'medium'
            })
        
        logger.info(f"Obtenidas {len(news)} noticias de mercado")
        return news[:5]  # Limitar a máximo 5 noticias
    
    def get_vix_detailed_analysis(self) -> Dict[str, Any]:
        """Análisis detallado del VIX con múltiples métricas"""
        try:
            # Obtener datos del VIX
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="60d")  # 60 días para percentiles
            
            # Obtener datos del SPX para ratio SPX/VIX
            spx_ticker = yf.Ticker("^GSPC")
            spx_data = spx_ticker.history(period="5d")
            
            if vix_data.empty:
                return {'error': 'No se pudieron obtener datos del VIX'}
            
            current_vix = vix_data['Close'].iloc[-1]
            prev_vix = vix_data['Close'].iloc[-2] if len(vix_data) > 1 else current_vix
            vix_change_1d = current_vix - prev_vix
            vix_change_1d_pct = (vix_change_1d / prev_vix) * 100 if prev_vix > 0 else 0
            
            # Calcular percentil de 30 días
            vix_30d_data = vix_data['Close'].tail(30)
            vix_30d_percentile = (vix_30d_data < current_vix).sum() / len(vix_30d_data) * 100
            
            # Clasificar sentimiento
            if current_vix > 30:
                sentiment = "Fear"
                sentiment_score = -2
            elif current_vix < 15:
                sentiment = "Greed"
                sentiment_score = 2
            else:
                sentiment = "Neutral"
                sentiment_score = 0
            
            # Calcular SPX/VIX ratio
            spx_vix_ratio = None
            if not spx_data.empty:
                current_spx = spx_data['Close'].iloc[-1]
                spx_vix_ratio = current_spx / current_vix
            
            # Análisis de extremos
            vix_extreme_high = current_vix > vix_data['Close'].quantile(0.95)
            vix_extreme_low = current_vix < vix_data['Close'].quantile(0.05)
            
            return {
                'vix_value': float(current_vix),
                'vix_change_1d': float(vix_change_1d),
                'vix_change_1d_pct': float(vix_change_1d_pct),
                'vix_30d_percentile': float(vix_30d_percentile),
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'spx_vix_ratio': float(spx_vix_ratio) if spx_vix_ratio else None,
                'vix_extreme_high': int(vix_extreme_high),
                'vix_extreme_low': int(vix_extreme_low),
                'market_fear_level': 'extreme' if current_vix > 40 else 'high' if current_vix > 25 else 'moderate' if current_vix > 15 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis detallado del VIX: {e}")
            return {'error': str(e)}
    
    def get_tick_index_approximation(self) -> Dict[str, Any]:
        """Aproximación del TICK Index usando datos disponibles"""
        try:
            # Lista de símbolos representativos del NASDAQ 100
            nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM']
            
            advancing = 0
            declining = 0
            unchanged = 0
            
            for symbol in nasdaq_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="2d")
                    
                    if len(data) >= 2:
                        current_close = data['Close'].iloc[-1]
                        prev_close = data['Close'].iloc[-2]
                        change = current_close - prev_close
                        
                        if change > 0:
                            advancing += 1
                        elif change < 0:
                            declining += 1
                        else:
                            unchanged += 1
                            
                except Exception:
                    continue
            
            total_stocks = advancing + declining + unchanged
            if total_stocks == 0:
                return {'error': 'No se pudieron obtener datos para TICK approximation'}
            
            # Calcular TICK approximation
            tick_value = advancing - declining
            tick_ratio = advancing / total_stocks if total_stocks > 0 else 0.5
            
            # Clasificar extremos
            if tick_value >= 7:
                tick_sentiment = 'extremely_bullish'
            elif tick_value >= 4:
                tick_sentiment = 'bullish'
            elif tick_value <= -7:
                tick_sentiment = 'extremely_bearish'
            elif tick_value <= -4:
                tick_sentiment = 'bearish'
            else:
                tick_sentiment = 'neutral'
            
            return {
                'tick_approximation': tick_value,
                'advancing_stocks': advancing,
                'declining_stocks': declining,
                'unchanged_stocks': unchanged,
                'total_stocks_sampled': total_stocks,
                'advance_decline_ratio': tick_ratio,
                'tick_sentiment': tick_sentiment,
                'market_breadth': 'strong' if tick_ratio > 0.7 else 'weak' if tick_ratio < 0.3 else 'moderate'
            }
            
        except Exception as e:
            logger.error(f"Error en TICK Index approximation: {e}")
            return {'error': str(e)}
    
    def calculate_tape_trading_metrics(self, data: pd.DataFrame = None) -> Dict[str, Any]:
        """Calcular métricas de Tape Trading / Order Flow"""
        try:
            if data is None:
                # Obtener datos intradía recientes
                data = self.get_intraday_data('1m')
            
            if data.empty or len(data) < 2:
                return {'error': 'Datos insuficientes para tape trading'}
             
            # Bid/Ask Imbalance aproximado usando precio y volumen
            price_changes = data['Close'].diff()
            volume_changes = data['Volume'].diff()
            
            # Aproximar Buy/Sell Pressure
            buy_pressure = 0
            sell_pressure = 0
            
            for i in range(1, len(data)):
                price_change = price_changes.iloc[i]
                volume = data['Volume'].iloc[i]
                
                if price_change > 0:
                    buy_pressure += volume
                elif price_change < 0:
                    sell_pressure += volume
            
            total_volume = buy_pressure + sell_pressure
            buy_sell_ratio = buy_pressure / sell_pressure if sell_pressure > 0 else float('inf')
            buy_pressure_pct = (buy_pressure / total_volume * 100) if total_volume > 0 else 50
            sell_pressure_pct = (sell_pressure / total_volume * 100) if total_volume > 0 else 50
            
            # Time & Sales resumen
            avg_trade_size = data['Volume'].mean()
            large_trades = (data['Volume'] > avg_trade_size * 2).sum()
            total_trades = len(data)
            large_trade_ratio = large_trades / total_trades if total_trades > 0 else 0
            
            # Bid/Ask Imbalance aproximado
            recent_data = data.tail(10)  # Últimas 10 barras
            up_moves = (recent_data['Close'] > recent_data['Open']).sum()
            down_moves = (recent_data['Close'] < recent_data['Open']).sum()
            imbalance_ratio = up_moves / (up_moves + down_moves) if (up_moves + down_moves) > 0 else 0.5
            
            return {
                'buy_pressure': float(buy_pressure),
                'sell_pressure': float(sell_pressure),
                'buy_sell_ratio': float(buy_sell_ratio) if buy_sell_ratio != float('inf') else 999.0,
                'buy_pressure_pct': float(buy_pressure_pct),
                'sell_pressure_pct': float(sell_pressure_pct),
                'avg_trade_size': float(avg_trade_size),
                'large_trades_count': int(large_trades),
                'large_trade_ratio': float(large_trade_ratio),
                'bid_ask_imbalance': float(imbalance_ratio),
                'order_flow_sentiment': 'bullish' if buy_pressure_pct > 60 else 'bearish' if buy_pressure_pct < 40 else 'neutral'
            }
            
        except Exception as e:
            logger.error(f"Error en tape trading metrics: {e}")
            return {'error': str(e)}
    
    def calculate_vwap_multi_timeframe(self, data_1m: pd.DataFrame = None, data_5m: pd.DataFrame = None, 
                                      data_15m: pd.DataFrame = None, data_4h: pd.DataFrame = None) -> Dict[str, Any]:
        """Calcular VWAP para múltiples marcos temporales"""
        try:
            # Obtener datos si no se proporcionan
            if data_1m is None:
                data_1m = self.get_intraday_data('1m')
            if data_5m is None:
                data_5m = self.get_intraday_data('5m')
            if data_15m is None:
                data_15m = self.get_intraday_data('15m')
            if data_4h is None:
                data_4h = self.get_intraday_data('4h')
            
            vwap_results = {}
            
            timeframes = {
                '1m': data_1m,
                '5m': data_5m,
                '15m': data_15m,
                '4h': data_4h
            }
            
            for tf, data in timeframes.items():
                if data is None or data.empty:
                    vwap_results[f'vwap_{tf}'] = None
                    vwap_results[f'vwap_{tf}_distance'] = None
                    continue
                
                # Calcular VWAP
                typical_price = (data['High'] + data['Low'] + data['Close']) / 3
                vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
                
                current_price = data['Close'].iloc[-1]
                current_vwap = vwap.iloc[-1]
                vwap_distance = ((current_price - current_vwap) / current_vwap) * 100
                
                vwap_results[f'vwap_{tf}'] = float(current_vwap)
                vwap_results[f'vwap_{tf}_distance'] = float(vwap_distance)
                vwap_results[f'price_above_vwap_{tf}'] = int(current_price > current_vwap)
            
            return vwap_results
            
        except Exception as e:
            logger.error(f"Error en VWAP multi-timeframe: {e}")
            return {'error': str(e)}
    
    def analyze_trend(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar tendencia basada en indicadores técnicos avanzados"""
        if not indicators:
            return {'trend': 'neutral', 'confidence': 0, 'signals': [], 'strength': 'weak'}
        
        signals = []
        bullish_signals = 0
        bearish_signals = 0
        neutral_signals = 0
        signal_weights = []  # Para calcular confianza ponderada
        
        # Análisis RSI (peso: 2)
        rsi = indicators.get('rsi')
        if rsi:
            if rsi < 30:
                signals.append(f'RSI oversold ({rsi:.1f}) - señal alcista fuerte')
                bullish_signals += 1
                signal_weights.append(('bullish', 2))
            elif rsi > 70:
                signals.append(f'RSI overbought ({rsi:.1f}) - señal bajista fuerte')
                bearish_signals += 1
                signal_weights.append(('bearish', 2))
            elif 30 <= rsi <= 45:
                signals.append(f'RSI ({rsi:.1f}) - zona de acumulación')
                bullish_signals += 0.5
                signal_weights.append(('bullish', 1))
            elif 55 <= rsi <= 70:
                signals.append(f'RSI ({rsi:.1f}) - zona de distribución')
                bearish_signals += 0.5
                signal_weights.append(('bearish', 1))
            else:
                signals.append(f'RSI neutral ({rsi:.1f})')
                neutral_signals += 1
        
        # Análisis MACD (peso: 2)
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_histogram = indicators.get('macd_histogram')
        if macd and macd_signal:
            if macd > macd_signal:
                if macd_histogram and macd_histogram > 0:
                    signals.append('MACD alcista con momentum creciente')
                    bullish_signals += 1
                    signal_weights.append(('bullish', 2))
                else:
                    signals.append('MACD alcista con momentum decreciente')
                    bullish_signals += 0.5
                    signal_weights.append(('bullish', 1))
            else:
                if macd_histogram and macd_histogram < 0:
                    signals.append('MACD bajista con momentum creciente')
                    bearish_signals += 1
                    signal_weights.append(('bearish', 2))
                else:
                    signals.append('MACD bajista con momentum decreciente')
                    bearish_signals += 0.5
                    signal_weights.append(('bearish', 1))
        
        # Análisis de medias móviles múltiples (peso: 1.5)
        close = indicators.get('last_close')
        sma_10 = indicators.get('sma_10')
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        
        ma_bullish = 0
        ma_bearish = 0
        
        if close and sma_10:
            if close > sma_10:
                ma_bullish += 1
            else:
                ma_bearish += 1
                
        if close and sma_20:
            if close > sma_20:
                ma_bullish += 1
                signals.append('Precio por encima de SMA20 - alcista')
            else:
                ma_bearish += 1
                signals.append('Precio por debajo de SMA20 - bajista')
                
        if close and sma_50:
            if close > sma_50:
                ma_bullish += 1
                signals.append('Precio por encima de SMA50 - tendencia alcista')
            else:
                ma_bearish += 1
                signals.append('Precio por debajo de SMA50 - tendencia bajista')
                
        if close and sma_200:
            if close > sma_200:
                ma_bullish += 1
                signals.append('Precio por encima de SMA200 - tendencia alcista a largo plazo')
            else:
                ma_bearish += 1
                signals.append('Precio por debajo de SMA200 - tendencia bajista a largo plazo')
        
        if ma_bullish > ma_bearish:
            bullish_signals += 1
            signal_weights.append(('bullish', 1.5))
        elif ma_bearish > ma_bullish:
            bearish_signals += 1
            signal_weights.append(('bearish', 1.5))
        
        # Análisis de osciladores (peso: 1)
        stoch_k = indicators.get('stoch_k')
        stoch_d = indicators.get('stoch_d')
        if stoch_k and stoch_d:
            if stoch_k < 20 and stoch_d < 20:
                signals.append(f'Stochastic oversold ({stoch_k:.1f}) - señal alcista')
                bullish_signals += 1
                signal_weights.append(('bullish', 1))
            elif stoch_k > 80 and stoch_d > 80:
                signals.append(f'Stochastic overbought ({stoch_k:.1f}) - señal bajista')
                bearish_signals += 1
                signal_weights.append(('bearish', 1))
        
        williams_r = indicators.get('williams_r')
        if williams_r:
            if williams_r < -80:
                signals.append(f'Williams %R oversold ({williams_r:.1f}) - señal alcista')
                bullish_signals += 0.5
                signal_weights.append(('bullish', 0.5))
            elif williams_r > -20:
                signals.append(f'Williams %R overbought ({williams_r:.1f}) - señal bajista')
                bearish_signals += 0.5
                signal_weights.append(('bearish', 0.5))
        
        # Análisis de volumen (peso: 1.5)
        volume_above_avg = indicators.get('volume_above_average', 0)
        obv_trend = indicators.get('obv_trend', 'neutral')
        daily_change_pct = indicators.get('daily_change_pct', 0)
        
        if volume_above_avg:
            if daily_change_pct > 0:
                signals.append('Volumen alto con precio al alza - confirmación alcista')
                bullish_signals += 1
                signal_weights.append(('bullish', 1.5))
            elif daily_change_pct < 0:
                signals.append('Volumen alto con precio a la baja - confirmación bajista')
                bearish_signals += 1
                signal_weights.append(('bearish', 1.5))
        
        if obv_trend == 'bullish':
            signals.append('OBV en tendencia alcista - flujo de dinero positivo')
            bullish_signals += 0.5
            signal_weights.append(('bullish', 1))
        elif obv_trend == 'bearish':
            signals.append('OBV en tendencia bajista - flujo de dinero negativo')
            bearish_signals += 0.5
            signal_weights.append(('bearish', 1))
        
        # Análisis de volatilidad (peso: 1)
        bb_squeeze = indicators.get('bb_squeeze', 0)
        volatility_high = indicators.get('volatility_high', 0)
        
        if bb_squeeze:
            signals.append('Bollinger Bands squeeze - posible ruptura inminente')
            neutral_signals += 1
        
        if volatility_high:
            signals.append('Alta volatilidad detectada - mercado inestable')
            neutral_signals += 1
        
        # Análisis de Money Flow Index (peso: 1)
        mfi = indicators.get('mfi')
        if mfi:
            if mfi < 20:
                signals.append(f'MFI oversold ({mfi:.1f}) - posible entrada de dinero')
                bullish_signals += 0.5
                signal_weights.append(('bullish', 1))
            elif mfi > 80:
                signals.append(f'MFI overbought ({mfi:.1f}) - posible salida de dinero')
                bearish_signals += 0.5
                signal_weights.append(('bearish', 1))
        
        # Calcular confianza ponderada
        total_bullish_weight = sum(weight for trend, weight in signal_weights if trend == 'bullish')
        total_bearish_weight = sum(weight for trend, weight in signal_weights if trend == 'bearish')
        total_weight = total_bullish_weight + total_bearish_weight
        
        # Determinar tendencia general y fuerza
        if total_bullish_weight > total_bearish_weight:
            trend = 'bullish'
            confidence = min(95, (total_bullish_weight / total_weight) * 100) if total_weight > 0 else 50
            strength = 'strong' if confidence > 75 else 'moderate' if confidence > 60 else 'weak'
        elif total_bearish_weight > total_bullish_weight:
            trend = 'bearish'
            confidence = min(95, (total_bearish_weight / total_weight) * 100) if total_weight > 0 else 50
            strength = 'strong' if confidence > 75 else 'moderate' if confidence > 60 else 'weak'
        else:
            trend = 'neutral'
            confidence = 50
            strength = 'weak'
        
        # Ajustar confianza basada en número de señales
        signal_count = len(signal_weights)
        if signal_count < 3:
            confidence *= 0.8  # Reducir confianza si hay pocas señales
        elif signal_count > 8:
            confidence = min(confidence * 1.1, 95)  # Aumentar confianza si hay muchas señales
        
        return {
            'trend': trend,
            'confidence': round(confidence, 1),
            'strength': strength,
            'signals': signals,
            'bullish_signals': round(bullish_signals, 1),
            'bearish_signals': round(bearish_signals, 1),
            'neutral_signals': neutral_signals,
            'total_signals': len(signals),
            'bullish_weight': round(total_bullish_weight, 1),
            'bearish_weight': round(total_bearish_weight, 1)
        }
    
    def predict_daily_levels(self, data: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, float]:
        """Predecir niveles de soporte y resistencia avanzados para el día"""
        if data.empty or not indicators:
            return {}
        
        try:
            # Usar datos de diferentes períodos para análisis completo
            recent_data_5 = data.tail(5)
            recent_data_10 = data.tail(10)
            recent_data_20 = data.tail(20)
            
            current_close = indicators.get('last_close', 0)
            current_high = indicators.get('last_high', 0)
            current_low = indicators.get('last_low', 0)
            atr = indicators.get('atr', 0)
            
            # 1. Niveles basados en Bandas de Bollinger
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)
            bb_middle = indicators.get('bb_middle', 0)
            
            # 2. Niveles basados en máximos y mínimos recientes (múltiples períodos)
            recent_high_5 = recent_data_5['High'].max()
            recent_low_5 = recent_data_5['Low'].min()
            recent_high_10 = recent_data_10['High'].max()
            recent_low_10 = recent_data_10['Low'].min()
            recent_high_20 = recent_data_20['High'].max()
            recent_low_20 = recent_data_20['Low'].min()
            
            # 3. Niveles de Fibonacci (múltiples rangos)
            # Fibonacci en rango de 5 días
            price_range_5 = recent_high_5 - recent_low_5
            fib_23_6_5d = recent_high_5 - (price_range_5 * 0.236)
            fib_38_2_5d = recent_high_5 - (price_range_5 * 0.382)
            fib_50_0_5d = recent_high_5 - (price_range_5 * 0.500)
            fib_61_8_5d = recent_high_5 - (price_range_5 * 0.618)
            fib_78_6_5d = recent_high_5 - (price_range_5 * 0.786)
            
            # Fibonacci en rango de 20 días
            price_range_20 = recent_high_20 - recent_low_20
            fib_38_2_20d = recent_high_20 - (price_range_20 * 0.382)
            fib_61_8_20d = recent_high_20 - (price_range_20 * 0.618)
            
            # 4. Puntos Pivot tradicionales
            pivot_point = (current_high + current_low + current_close) / 3
            
            # Resistencias
            r1 = (2 * pivot_point) - current_low
            r2 = pivot_point + (current_high - current_low)
            r3 = current_high + 2 * (pivot_point - current_low)
            
            # Soportes
            s1 = (2 * pivot_point) - current_high
            s2 = pivot_point - (current_high - current_low)
            s3 = current_low - 2 * (current_high - pivot_point)
            
            # 5. Niveles basados en ATR (Average True Range)
            atr_resistance_1 = current_close + atr
            atr_resistance_2 = current_close + (atr * 2)
            atr_support_1 = current_close - atr
            atr_support_2 = current_close - (atr * 2)
            
            # 6. Niveles psicológicos (números redondos)
            def find_psychological_levels(price, range_pct=0.05):
                """Encontrar niveles psicológicos cercanos"""
                levels = []
                base = int(price / 100) * 100  # Redondear a centenas
                
                for i in range(-2, 3):
                    level = base + (i * 100)
                    if abs(level - price) / price <= range_pct:
                        levels.append(level)
                
                # Niveles de 50 puntos
                base_50 = int(price / 50) * 50
                for i in range(-1, 2):
                    level = base_50 + (i * 50)
                    if abs(level - price) / price <= range_pct:
                        levels.append(level)
                
                return sorted(set(levels))
            
            psychological_levels = find_psychological_levels(current_close)
            
            # 7. Medias móviles como soporte/resistencia
            sma_10 = indicators.get('sma_10', 0)
            sma_20 = indicators.get('sma_20', 0)
            sma_50 = indicators.get('sma_50', 0)
            ema_12 = indicators.get('ema_12', 0)
            ema_26 = indicators.get('ema_26', 0)
            
            # 8. Niveles de volumen (VWAP mejorado) - ACTUALIZADO
            vwap_data = {}
            if len(recent_data_20) > 0:
                # VWAP estándar (20 períodos)
                typical_price_20 = (recent_data_20['High'] + recent_data_20['Low'] + recent_data_20['Close']) / 3
                vwap = (typical_price_20 * recent_data_20['Volume']).sum() / recent_data_20['Volume'].sum()
                vwap_data['vwap_20'] = vwap
                
                # VWAP de 10 períodos si hay suficientes datos
                if len(recent_data_20) >= 10:
                    recent_10 = recent_data_20.tail(10)
                    typical_price_10 = (recent_10['High'] + recent_10['Low'] + recent_10['Close']) / 3
                    vwap_10 = (typical_price_10 * recent_10['Volume']).sum() / recent_10['Volume'].sum()
                    vwap_data['vwap_10'] = vwap_10
                
                # VWAP de 5 períodos
                if len(recent_data_20) >= 5:
                    recent_5 = recent_data_20.tail(5)
                    typical_price_5 = (recent_5['High'] + recent_5['Low'] + recent_5['Close']) / 3
                    vwap_5 = (typical_price_5 * recent_5['Volume']).sum() / recent_5['Volume'].sum()
                    vwap_data['vwap_5'] = vwap_5
                
                # Análisis de desviación del VWAP
                vwap_deviation = ((current_close - vwap) / vwap) * 100
                vwap_data['vwap_deviation_pct'] = round(vwap_deviation, 2)
                vwap_data['above_vwap'] = int(current_close > vwap)
            else:
                vwap = current_close
                vwap_data = {'vwap_20': vwap, 'vwap_deviation_pct': 0, 'above_vwap': 1}
            
            # Compilar todos los niveles
            all_resistance_levels = [
                bb_upper, recent_high_5, recent_high_10, recent_high_20,
                fib_23_6_5d, fib_38_2_5d, fib_38_2_20d,
                r1, r2, atr_resistance_1, atr_resistance_2
            ]
            
            all_support_levels = [
                bb_lower, recent_low_5, recent_low_10, recent_low_20,
                fib_61_8_5d, fib_78_6_5d, fib_61_8_20d,
                s1, s2, atr_support_1, atr_support_2
            ]
            
            # Filtrar niveles válidos (por encima/debajo del precio actual)
            valid_resistances = [r for r in all_resistance_levels if r and r > current_close]
            valid_supports = [s for s in all_support_levels if s and s < current_close]
            
            # Ordenar y seleccionar los más cercanos
            valid_resistances.sort()
            valid_supports.sort(reverse=True)
            
            # Agregar medias móviles según su posición relativa al precio
            ma_levels = [sma_10, sma_20, sma_50, ema_12, ema_26, vwap]
            for ma in ma_levels:
                if ma:
                    if ma > current_close:
                        valid_resistances.append(ma)
                    elif ma < current_close:
                        valid_supports.append(ma)
            
            # Re-ordenar después de agregar MAs
            valid_resistances.sort()
            valid_supports.sort(reverse=True)
            
            return {
                # Resistencias principales
                'resistance_1': float(valid_resistances[0]) if valid_resistances else float(recent_high_5),
                'resistance_2': float(valid_resistances[1]) if len(valid_resistances) > 1 else float(recent_high_10),
                'resistance_3': float(valid_resistances[2]) if len(valid_resistances) > 2 else float(r2),
                
                # Soportes principales
                'support_1': float(valid_supports[0]) if valid_supports else float(recent_low_5),
                'support_2': float(valid_supports[1]) if len(valid_supports) > 1 else float(recent_low_10),
                'support_3': float(valid_supports[2]) if len(valid_supports) > 2 else float(s2),
                
                # Niveles de Fibonacci clave
                'fibonacci_23_6': float(fib_23_6_5d),
                'fibonacci_38_2': float(fib_38_2_5d),
                'fibonacci_50_0': float(fib_50_0_5d),
                'fibonacci_61_8': float(fib_61_8_5d),
                'fibonacci_78_6': float(fib_78_6_5d),
                
                # Puntos Pivot
                'pivot_point': float(pivot_point),
                'pivot_r1': float(r1),
                'pivot_r2': float(r2),
                'pivot_r3': float(r3),
                'pivot_s1': float(s1),
                'pivot_s2': float(s2),
                'pivot_s3': float(s3),
                
                # Niveles ATR
                'atr_resistance': float(atr_resistance_1),
                'atr_support': float(atr_support_1),
                
                # Bandas de Bollinger
                'bb_upper': float(bb_upper) if bb_upper else 0,
                'bb_middle': float(bb_middle) if bb_middle else 0,
                'bb_lower': float(bb_lower) if bb_lower else 0,
                
                # VWAP mejorado - ACTUALIZADO
            'vwap': float(vwap),
            'vwap_data': vwap_data,  # Incluir todos los datos de VWAP
                
                # Niveles psicológicos
                'psychological_levels': [float(level) for level in psychological_levels],
                
                # Información adicional
                'current_price': float(current_close),
                'daily_range': float(current_high - current_low),
                'atr_value': float(atr) if atr else 0,
                'volatility_adjusted_range': float(atr * 2) if atr else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculando niveles diarios: {e}")
            return {}
    
    def generate_daily_analysis(self) -> Dict[str, Any]:
        """Generar análisis completo del día con datos intradía"""
        logger.info("Iniciando análisis diario del NASDAQ 100")
        
        # Obtener datos de mercado
        market_data = self.get_market_data()
        if market_data.empty:
            logger.error("No se pudieron obtener datos de mercado")
            return {}
        
        # Calcular indicadores técnicos
        indicators = self.calculate_technical_indicators(market_data)
        
        # Calcular análisis probabilístico - NUEVO
        probabilistic_analysis = self.calculate_probabilistic_analysis(market_data, indicators)
        
        # Calcular nuevos indicadores - NUEVOS INDICADORES IMPLEMENTADOS
        vix_analysis = self.get_vix_detailed_analysis()
        tick_analysis = self.get_tick_index_approximation()
        tape_trading = self.calculate_tape_trading_metrics()
        vwap_multi = self.calculate_vwap_multi_timeframe()
        
        # Analizar tendencia
        trend_analysis = self.analyze_trend(indicators)
        
        # Predecir niveles del día
        daily_levels = self.predict_daily_levels(market_data, indicators)
        
        # Obtener datos intradía para múltiples temporalidades
        intraday_analysis = {}
        chart_data = {}
        
        timeframes = ['1m', '5m', '15m', '4h', '1d']
        for timeframe in timeframes:
            try:
                logger.info(f"Obteniendo datos intradía para {timeframe}")
                intraday_data = self.get_intraday_data(timeframe)
                
                if not intraday_data.empty:
                    # Análisis técnico específico para la temporalidad
                    intraday_indicators = self.calculate_intraday_indicators(intraday_data, timeframe)
                    intraday_analysis[timeframe] = intraday_indicators
                    
                    # Datos para gráficos - convertir a formato simple para JSON
                    chart_data[timeframe] = [{
                        'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume'])
                    } for dt, row in intraday_data.iterrows()]
                    
                    logger.info(f"Análisis intradía completado para {timeframe}: {len(intraday_data)} barras")
                else:
                    logger.warning(f"No se pudieron obtener datos intradía para {timeframe}")
                    intraday_analysis[timeframe] = {}
                    chart_data[timeframe] = []
                    
            except Exception as e:
                logger.error(f"Error obteniendo datos intradía para {timeframe}: {e}")
                intraday_analysis[timeframe] = {}
                chart_data[timeframe] = []
        
        # Obtener noticias
        news = self.get_market_news()
        
        # Datos del día anterior
        yesterday_data = {
            'high': float(market_data['High'].iloc[-1]),
            'low': float(market_data['Low'].iloc[-1]),
            'close': float(market_data['Close'].iloc[-1]),
            'volume': int(market_data['Volume'].iloc[-1])
        }
        
        # Compilar análisis completo
        analysis = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'symbol': self.symbol,
            'yesterday_data': yesterday_data,
            'technical_indicators': indicators,
            'trend_analysis': trend_analysis,
            'daily_levels': daily_levels,
            'probabilistic_analysis': probabilistic_analysis,  # NUEVO
            'vix_detailed_analysis': vix_analysis,  # NUEVO - VIX detallado
            'tick_index_analysis': tick_analysis,  # NUEVO - TICK Index
            'tape_trading_metrics': tape_trading,  # NUEVO - Order Flow
            'vwap_multi_timeframe': vwap_multi,  # NUEVO - VWAP múltiples marcos
            'intraday_analysis': intraday_analysis,
            'chart_data': chart_data,
            'news': news,
            'summary': self.generate_summary(trend_analysis, daily_levels, indicators, intraday_analysis, probabilistic_analysis, vix_analysis, tick_analysis, tape_trading)
        }
        
        return analysis
    
    def generate_summary(self, trend_analysis: Dict, daily_levels: Dict, indicators: Dict, intraday_analysis: Dict = None, probabilistic_analysis: Dict = None, vix_analysis: Dict = None, tick_analysis: Dict = None, tape_trading: Dict = None) -> Dict:
        """Generar resumen consolidado del análisis como objeto estructurado"""
        trend = trend_analysis.get('trend', 'neutral')
        confidence = trend_analysis.get('confidence', 0)
        
        # SECCIÓN 1: TENDENCIA PRINCIPAL
        main_trend = {
            'direction': trend.upper(),
            'confidence': confidence,
            'emoji': '🟢' if trend == 'bullish' else '🔴' if trend == 'bearish' else '🟡'
        }
        
        # SECCIÓN 2: NIVELES CLAVE
        key_levels = {}
        if daily_levels:
            key_levels = {
                'resistance': daily_levels.get('resistance_1', 0),
                'support': daily_levels.get('support_1', 0)
            }
        
        # SECCIÓN 3: INDICADORES TÉCNICOS
        rsi = indicators.get('rsi')
        rsi_status = "SOBREVENTA" if rsi and rsi < 30 else "SOBRECOMPRA" if rsi and rsi > 70 else "NEUTRAL"
        
        macd_bullish = indicators.get('macd_bullish', False)
        macd_status = "ALCISTA" if macd_bullish else "BAJISTA"
        
        adx = indicators.get('adx_daily', 0)
        trend_strength = "FUERTE" if adx > 25 else "DÉBIL" if adx < 20 else "MODERADA"
        
        technical_indicators = {
            'rsi': {
                'value': rsi,
                'status': rsi_status,
                'emoji': '🔴' if rsi_status == 'SOBRECOMPRA' else '🟢' if rsi_status == 'SOBREVENTA' else '🟡'
            },
            'macd': {
                'status': macd_status,
                'bullish': macd_bullish,
                'emoji': '🟢' if macd_bullish else '🔴'
            },
            'adx': {
                'value': adx,
                'strength': trend_strength,
                'emoji': '🟢' if trend_strength == 'FUERTE' else '🔴' if trend_strength == 'DÉBIL' else '🟡'
            }
        }
        
        # SECCIÓN 4: VOLUMEN Y LIQUIDEZ
        rvol = indicators.get('rvol', 1.0)
        volume_status = "ALTO" if rvol > 1.5 else "BAJO" if rvol < 0.8 else "NORMAL"
        big_print = indicators.get('big_print_detected', False)
        
        volume_analysis = {
            'rvol': rvol,
            'status': volume_status,
            'big_prints_detected': big_print,
            'emoji': '🟢' if volume_status == 'ALTO' else '🔴' if volume_status == 'BAJO' else '🟡'
        }
        
        # SECCIÓN 5: SENTIMIENTO DE MERCADO
        market_sentiment = {}
        
        # VIX
        if vix_analysis:
            vix_value = vix_analysis.get('vix_value', 0)
            vix_change = vix_analysis.get('vix_change_1d', 0)
            vix_sentiment = vix_analysis.get('sentiment', 'neutral')
            market_sentiment['vix'] = {
                'value': vix_value,
                'change': vix_change,
                'sentiment': vix_sentiment.upper(),
                'emoji': '😱' if vix_sentiment == 'fear' else '😎' if vix_sentiment == 'greed' else '😐'
            }
        
        # TICK Index
        if tick_analysis:
            tick_value = tick_analysis.get('tick_value', 0)
            tick_sentiment = tick_analysis.get('sentiment', 'neutral')
            market_sentiment['tick'] = {
                'value': tick_value,
                'sentiment': tick_sentiment.upper(),
                'emoji': '🟢' if tick_sentiment == 'bullish' else '🔴' if tick_sentiment == 'bearish' else '🟡'
            }
        
        # Order Flow
        if tape_trading:
            buy_pressure = tape_trading.get('buy_pressure_pct', 50)
            flow_sentiment = tape_trading.get('order_flow_sentiment', 'neutral')
            market_sentiment['order_flow'] = {
                'buy_pressure': buy_pressure,
                'sentiment': flow_sentiment.upper(),
                'emoji': '🟢' if flow_sentiment == 'bullish' else '🔴' if flow_sentiment == 'bearish' else '🟡'
            }
        
        # SECCIÓN 6: SEÑALES INTRADÍA
        intraday_signals = []
        
        if intraday_analysis:
            # Señales de 1 minuto
            if '1m' in intraday_analysis and intraday_analysis['1m']:
                intraday_1m = intraday_analysis['1m']
                if intraday_1m.get('scalp_buy_signal'):
                    intraday_signals.append({
                        'timeframe': '1m',
                        'signal': 'COMPRA',
                        'type': 'scalping',
                        'emoji': '🟢'
                    })
                elif intraday_1m.get('scalp_sell_signal'):
                    intraday_signals.append({
                        'timeframe': '1m',
                        'signal': 'VENTA',
                        'type': 'scalping',
                        'emoji': '🔴'
                    })
                
                if intraday_1m.get('range_trading'):
                    intraday_signals.append({
                        'timeframe': '1m',
                        'signal': 'RANGO',
                        'type': 'range_trading',
                        'emoji': '🔄'
                    })
            
            # Señales de 5 minutos
            if '5m' in intraday_analysis and intraday_analysis['5m']:
                intraday_5m = intraday_analysis['5m']
                if intraday_5m.get('ema_bullish_cross'):
                    intraday_signals.append({
                        'timeframe': '5m',
                        'signal': 'CRUCE ALCISTA EMAs',
                        'type': 'ema_cross',
                        'emoji': '🟢'
                    })
                elif intraday_5m.get('ema_bearish_cross'):
                    intraday_signals.append({
                        'timeframe': '5m',
                        'signal': 'CRUCE BAJISTA EMAs',
                        'type': 'ema_cross',
                        'emoji': '🔴'
                    })
        
        # SECCIÓN 7: ANÁLISIS PROBABILÍSTICO
        probabilistic_prediction = {}
        if probabilistic_analysis and 'trend_prediction' in probabilistic_analysis:
            trend_pred = probabilistic_analysis.get('trend_prediction', 'neutral')
            bullish_prob = probabilistic_analysis.get('bullish_probability', 50)
            bearish_prob = probabilistic_analysis.get('bearish_probability', 50)
            confidence_prob = probabilistic_analysis.get('prediction_confidence', 0)
            
            probabilistic_prediction = {
                'prediction': trend_pred.upper(),
                'bullish_probability': bullish_prob,
                'bearish_probability': bearish_prob,
                'confidence': confidence_prob,
                'emoji': '🟢' if trend_pred == 'bullish' else '🔴' if trend_pred == 'bearish' else '🟡'
            }
        
        # SECCIÓN 8: RESUMEN EJECUTIVO
        # Validar señales principales
        bullish_signals = []
        bearish_signals = []
        
        # Evaluar señales técnicas
        if rsi and rsi < 30:
            bullish_signals.append("RSI sobreventa")
        elif rsi and rsi > 70:
            bearish_signals.append("RSI sobrecompra")
        
        if macd_bullish:
            bullish_signals.append("MACD alcista")
        else:
            bearish_signals.append("MACD bajista")
        
        # Evaluar volumen
        if rvol > 1.5:
            bullish_signals.append("Volumen alto")
        elif rvol < 0.8:
            bearish_signals.append("Volumen bajo")
        
        # Evaluar VIX
        if vix_analysis:
            vix_sentiment = vix_analysis.get('sentiment', 'neutral')
            if vix_sentiment == 'fear':
                bullish_signals.append("VIX en zona de miedo")
            elif vix_sentiment == 'greed':
                bearish_signals.append("VIX en zona de codicia")
        
        # Determinar sesgo general
        total_bullish = len(bullish_signals)
        total_bearish = len(bearish_signals)
        
        if total_bullish > total_bearish:
            bias = "ALCISTA"
            bias_emoji = "🟢"
            recommendation = "Buscar oportunidades de compra en retrocesos"
        elif total_bearish > total_bullish:
            bias = "BAJISTA"
            bias_emoji = "🔴"
            recommendation = "Considerar ventas en rebotes"
        else:
            bias = "NEUTRAL"
            bias_emoji = "🟡"
            recommendation = "Esperar confirmación direccional"
        
        # Factores clave (máximo 3)
        key_factors = []
        if bullish_signals:
            key_factors.extend(bullish_signals[:2])
        if bearish_signals:
            key_factors.extend(bearish_signals[:2])
        
        executive_summary = {
            'bias': bias,
            'bias_emoji': bias_emoji,
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals,
            'key_factors': key_factors[:3],
            'recommendation': recommendation,
            'total_bullish': total_bullish,
            'total_bearish': total_bearish
        }
        
        # Retornar objeto estructurado
        return {
             'main_trend': main_trend,
             'key_levels': key_levels,
             'technical_indicators': technical_indicators,
             'volume_analysis': volume_analysis,
             'market_sentiment': market_sentiment,
             'intraday_signals': intraday_signals,
             'probabilistic_prediction': probabilistic_prediction,
             'executive_summary': executive_summary
         }
    
    def clean_nan_values(self, obj):
        """Recursivamente limpia valores NaN, Infinity y los convierte a None para JSON"""
        if isinstance(obj, dict):
            return {key: self.clean_nan_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.clean_nan_values(item) for item in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def save_analysis(self, analysis: Dict[str, Any]) -> str:
        """Guardar análisis en archivo JSON"""
        if not analysis:
            logger.error("No hay análisis para guardar")
            return ""
        
        filename = f"{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            # Limpiar valores NaN antes de guardar
            clean_analysis = self.clean_nan_values(analysis)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(clean_analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Análisis guardado en {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error guardando análisis: {e}")
            return ""
    
    def run_daily_analysis(self):
        """Ejecutar análisis diario completo"""
        try:
            analysis = self.generate_daily_analysis()
            if analysis:
                filepath = self.save_analysis(analysis)
                if filepath:
                    logger.info("Análisis diario completado exitosamente")
                    return True
            
            logger.error("Falló el análisis diario")
            return False
        except Exception as e:
            logger.error(f"Error en análisis diario: {e}")
            return False

def main():
    """Función principal"""
    analyzer = NasdaqAnalyzer()
    success = analyzer.run_daily_analysis()
    
    if success:
        print("✅ Análisis diario completado")
    else:
        print("❌ Error en el análisis diario")
        exit(1)

if __name__ == "__main__":
    main()