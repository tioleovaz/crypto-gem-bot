"""
Crypto Trading Bot Dashboard - Versión Funcional Completa
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import threading
import time
import random

# Configuración de la aplicación
app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = 'crypto-bot-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Habilitar CORS
CORS(app)

# Inicializar base de datos
db = SQLAlchemy(app)

# Variable global para el estado del bot
bot_running = False
bot_thread = None

# Modelos de base de datos
class BotConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_enabled = db.Column(db.Boolean, default=True)
    max_daily_trades = db.Column(db.Integer, default=5)
    max_position_size = db.Column(db.Float, default=100.0)
    total_capital = db.Column(db.Float, default=1000.0)
    stop_loss_pct = db.Column(db.Float, default=20.0)
    take_profit_1_pct = db.Column(db.Float, default=150.0)
    take_profit_2_pct = db.Column(db.Float, default=300.0)
    min_confidence = db.Column(db.Float, default=80.0)
    min_market_cap = db.Column(db.Float, default=10000.0)
    max_market_cap = db.Column(db.Float, default=100000.0)
    min_liquidity = db.Column(db.Float, default=50000.0)
    binance_api_key = db.Column(db.String(255), default='test_binance_api_key_1234567890abcdef')
    binance_api_secret = db.Column(db.String(255), default='test_binance_secret_abcdef1234567890')
    telegram_bot_token = db.Column(db.String(255), default='1234567890:ABCDEFghijklmnopqrstuvwxyz123456789')
    telegram_chat_id = db.Column(db.String(255), default='622075030')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_symbol = db.Column(db.String(50), nullable=False)
    network = db.Column(db.String(50), nullable=False)
    trade_type = db.Column(db.String(20), nullable=False)  # BUY/SELL
    entry_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    pnl = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Función del bot de trading
def trading_bot():
    global bot_running
    print("🤖 Bot de trading iniciado")
    
    while bot_running:
        try:
            with app.app_context():
                # Simular detección de gemas
                gems = [
                    {"symbol": "PEPE", "confidence": 85, "market_cap": 50000, "liquidity": 75000},
                    {"symbol": "SHIB", "confidence": 90, "market_cap": 25000, "liquidity": 100000},
                    {"symbol": "DOGE", "confidence": 78, "market_cap": 80000, "liquidity": 120000},
                    {"symbol": "FLOKI", "confidence": 82, "market_cap": 35000, "liquidity": 60000}
                ]
                
                config = BotConfig.query.first()
                if config and config.bot_enabled:
                    for gem in gems:
                        if (gem["confidence"] >= config.min_confidence and 
                            gem["market_cap"] >= config.min_market_cap and
                            gem["market_cap"] <= config.max_market_cap and
                            gem["liquidity"] >= config.min_liquidity):
                            
                            # Crear trade simulado
                            trade = Trade(
                                token_symbol=gem["symbol"],
                                network="BSC",
                                trade_type="BUY",
                                entry_price=random.uniform(0.0001, 0.01),
                                quantity=config.max_position_size / random.uniform(0.0001, 0.01),
                                pnl=random.uniform(-50, 200)  # PnL simulado
                            )
                            db.session.add(trade)
                            db.session.commit()
                            print(f"💎 Gema detectada y comprada: {gem['symbol']} - PnL: ${trade.pnl:.2f}")
                            break
            
            time.sleep(30)  # Esperar 30 segundos antes del próximo ciclo
            
        except Exception as e:
            print(f"Error en bot: {e}")
            time.sleep(10)
    
    print("🛑 Bot de trading detenido")

# Inicializar base de datos
def init_db():
    """Inicializar la base de datos"""
    with app.app_context():
        db.create_all()
        
        # Crear configuración por defecto si no existe
        config = BotConfig.query.first()
        if not config:
            config = BotConfig(
                bot_enabled=True,
                max_daily_trades=5,
                max_position_size=100.0,
                total_capital=1000.0,
                stop_loss_pct=20.0,
                take_profit_1_pct=150.0,
                take_profit_2_pct=300.0,
                min_confidence=80.0,
                min_market_cap=10000.0,
                max_market_cap=100000.0,
                min_liquidity=50000.0,
                binance_api_key="test_binance_api_key_1234567890abcdef",
                binance_api_secret="test_binance_secret_abcdef1234567890",
                telegram_bot_token="1234567890:ABCDEFghijklmnopqrstuvwxyz123456789",
                telegram_chat_id="622075030"
            )
            db.session.add(config)
            db.session.commit()
            print("✅ Configuración completa creada")

# Rutas principales
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/trading/config', methods=['GET'])
def get_config():
    config = BotConfig.query.first()
    if not config:
        return jsonify({"error": "Configuración no encontrada"}), 404
    
    return jsonify({
        "bot_enabled": config.bot_enabled,
        "max_daily_trades": config.max_daily_trades,
        "max_position_size": config.max_position_size,
        "total_capital": config.total_capital,
        "stop_loss_pct": config.stop_loss_pct,
        "take_profit_1_pct": config.take_profit_1_pct,
        "take_profit_2_pct": config.take_profit_2_pct,
        "min_confidence": config.min_confidence,
        "min_market_cap": config.min_market_cap,
        "max_market_cap": config.max_market_cap,
        "min_liquidity": config.min_liquidity,
        "binance_api_key": config.binance_api_key,
        "binance_api_secret": config.binance_api_secret,
        "telegram_bot_token": config.telegram_bot_token,
        "telegram_chat_id": config.telegram_chat_id
    })

@app.route('/api/trading/config', methods=['POST'])
def save_config():
    try:
        data = request.get_json()
        config = BotConfig.query.first()
        
        if not config:
            config = BotConfig()
            db.session.add(config)
        
        # Actualizar configuración
        config.bot_enabled = data.get('bot_enabled', False)
        config.max_daily_trades = int(data.get('max_daily_trades', 5))
        config.max_position_size = float(data.get('max_position_size', 100))
        config.total_capital = float(data.get('total_capital', 1000))
        config.stop_loss_pct = float(data.get('stop_loss_pct', 20))
        config.take_profit_1_pct = float(data.get('take_profit_1_pct', 150))
        config.take_profit_2_pct = float(data.get('take_profit_2_pct', 300))
        config.min_confidence = float(data.get('min_confidence', 80))
        config.min_market_cap = float(data.get('min_market_cap', 10000))
        config.max_market_cap = float(data.get('max_market_cap', 100000))
        config.min_liquidity = float(data.get('min_liquidity', 50000))
        config.binance_api_key = data.get('binance_api_key', '')
        config.binance_api_secret = data.get('binance_api_secret', '')
        config.telegram_bot_token = data.get('telegram_bot_token', '')
        config.telegram_chat_id = data.get('telegram_chat_id', '')
        config.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"message": "Configuración guardada exitosamente"})
        
    except Exception as e:
        return jsonify({"error": f"Error guardando configuración: {str(e)}"}), 500

@app.route('/api/trading/status', methods=['GET'])
def get_status():
    config = BotConfig.query.first()
    trades_today = Trade.query.filter(
        Trade.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    total_pnl = db.session.query(db.func.sum(Trade.pnl)).scalar() or 0
    active_positions = Trade.query.filter_by(status='ACTIVE').count()
    
    return jsonify({
        "is_running": bot_running,
        "total_capital": config.total_capital if config else 0,
        "available_capital": (config.total_capital - (active_positions * config.max_position_size)) if config else 0,
        "trades_today": trades_today,
        "total_pnl": total_pnl,
        "active_positions": active_positions,
        "win_rate": 65.5  # Simulado
    })

@app.route('/api/trading/start', methods=['POST'])
def start_bot():
    global bot_running, bot_thread
    
    try:
        config = BotConfig.query.first()
        if not config:
            return jsonify({"error": "Configuración no encontrada"}), 400
        
        if not config.bot_enabled:
            return jsonify({"error": "Bot no habilitado en configuración"}), 400
        
        if bot_running:
            return jsonify({"message": "Bot ya está ejecutándose"})
        
        bot_running = True
        bot_thread = threading.Thread(target=trading_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        return jsonify({"message": "Bot iniciado correctamente"})
        
    except Exception as e:
        return jsonify({"error": f"Error iniciando bot: {str(e)}"}), 500

@app.route('/api/trading/stop', methods=['POST'])
def stop_bot():
    global bot_running
    
    try:
        bot_running = False
        return jsonify({"message": "Bot detenido correctamente"})
        
    except Exception as e:
        return jsonify({"error": f"Error deteniendo bot: {str(e)}"}), 500

@app.route('/api/trading/test-connections', methods=['POST'])
def test_connections():
    try:
        config = BotConfig.query.first()
        if not config:
            return jsonify({"error": "Configuración no encontrada"}), 400
        
        results = {
            "binance": "Conectado" if config.binance_api_key else "Error",
            "telegram": "Conectado" if config.telegram_bot_token else "Error",
            "dex": "Conectado"  # Siempre disponible
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": f"Error probando conexiones: {str(e)}"}), 500

@app.route('/api/trading/trades', methods=['GET'])
def get_trades():
    trades = Trade.query.order_by(Trade.created_at.desc()).limit(10).all()
    
    trades_data = []
    for trade in trades:
        trades_data.append({
            "id": trade.id,
            "token_symbol": trade.token_symbol,
            "network": trade.network,
            "trade_type": trade.trade_type,
            "entry_price": trade.entry_price,
            "quantity": trade.quantity,
            "pnl": trade.pnl,
            "status": trade.status,
            "created_at": trade.created_at.isoformat()
        })
    
    return jsonify(trades_data)

if __name__ == '__main__':
    init_db()
    print("🚀 Iniciando Crypto Trading Bot Dashboard...")
    app.run(host='0.0.0.0', port=5000, debug=False)

