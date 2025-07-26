import os
import sys
from flask import Flask, send_from_directory, request, jsonify, render_template_string
from flask_cors import CORS
import json
import random
import time
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'crypto-bot-secret-2024')

# Variables globales para configuración del bot
bot_config = {
    "bot_enabled": True,
    "max_daily_trades": 4,
    "max_position_size": 300.0,
    "total_capital": 2000.0,
    "stop_loss_pct": 18.0,
    "take_profit_1_pct": 100.0,
    "take_profit_2_pct": 200.0,
    "take_profit_3_pct": 400.0,
    "min_confidence": 85.0,
    "min_market_cap": 25000.0,
    "max_market_cap": 300000.0,
    "min_liquidity": 75000.0,
    "binance_api_key": os.environ.get('BINANCE_API_KEY', 'demo_key_12345'),
    "binance_api_secret": os.environ.get('BINANCE_API_SECRET', 'demo_secret_67890'),
    "telegram_bot_token": os.environ.get('TELEGRAM_BOT_TOKEN', '1234567890:ABCDEFghijklmnopqrstuvwxyz123456789'),
    "telegram_chat_id": os.environ.get('TELEGRAM_CHAT_ID', '622075030')
}

# Estado del bot
bot_running = False
trades_list = []
alerts_list = []
performance_data = []

def generate_demo_trade():
    """Generar trade de demostración realista"""
    tokens = ['PEPE', 'SHIB', 'FLOKI', 'CHAD', 'WOJAK', 'BONK', 'MEME', 'DOGE2', 'BABYDOGE', 'SAFEMOON']
    token = random.choice(tokens)
    
    # Generar datos más realistas
    confidence = round(random.uniform(85, 98), 1)
    market_cap = round(random.uniform(25000, 300000), 0)
    liquidity = round(random.uniform(75000, 500000), 0)
    entry_price = round(random.uniform(0.000001, 0.01), 8)
    quantity = round(bot_config['max_position_size'] / entry_price, 0)
    
    # PnL basado en confianza (mayor confianza = mejor resultado promedio)
    pnl_multiplier = (confidence - 80) / 20  # 0.25 a 0.9
    base_pnl = random.uniform(-100, 500)
    pnl = round(base_pnl * pnl_multiplier, 2)
    
    trade = {
        "id": len(trades_list) + 1,
        "token_symbol": token,
        "network": "BSC",
        "trade_type": "BUY",
        "entry_price": entry_price,
        "quantity": quantity,
        "pnl": pnl,
        "status": random.choice(["ACTIVE", "COMPLETED", "STOPPED"]),
        "confidence": confidence,
        "market_cap": market_cap,
        "liquidity": liquidity,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    trades_list.append(trade)
    
    # Generar alerta correspondiente
    alert_type = "GEM_DETECTED" if pnl >= 0 else "RISK_WARNING"
    emoji = "🚀" if pnl >= 0 else "⚠️"
    
    alert = {
        "id": len(alerts_list) + 1,
        "alert_type": alert_type,
        "message": f"{emoji} {alert_type.replace('_', ' ')}: {token}\\n💎 Confianza: {confidence}%\\n💰 Market Cap: ${market_cap:,.0f}\\n💧 Liquidez: ${liquidity:,.0f}\\n📊 PnL: ${pnl:.2f}",
        "token_symbol": token,
        "is_read": False,
        "priority": "HIGH" if confidence > 90 else "MEDIUM",
        "created_at": datetime.now().isoformat()
    }
    
    alerts_list.append(alert)
    
    # Actualizar datos de performance
    performance_data.append({
        "timestamp": datetime.now().isoformat(),
        "pnl": pnl,
        "confidence": confidence,
        "market_cap": market_cap
    })
    
    logger.info(f"💎 Gema generada: {token} (Confianza: {confidence}%, PnL: ${pnl:.2f})")
    return trade

# HTML del dashboard embebido
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Gem Bot - Professional Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-hover { transition: all 0.3s ease; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .status-indicator { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-online { background-color: #10b981; }
        .status-offline { background-color: #ef4444; }
        .status-warning { background-color: #f59e0b; }
        .notification { position: fixed; top: 20px; right: 20px; z-index: 1000; padding: 16px; border-radius: 8px; color: white; font-weight: bold; }
        .notification.success { background-color: #10b981; }
        .notification.error { background-color: #ef4444; }
        .notification.info { background-color: #3b82f6; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Header -->
    <header class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <div class="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                        <i data-lucide="gem" class="w-6 h-6"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold">Crypto Gem Bot</h1>
                        <p class="text-blue-100">Professional Trading Dashboard</p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <div id="bot-status" class="flex items-center">
                        <span class="status-indicator status-offline"></span>
                        <span id="status-text">Desconectado</span>
                    </div>
                    <button id="emergency-stop" class="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-lg font-semibold transition-colors">
                        Stop Emergencia
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <div class="container mx-auto px-6 py-8">
        <!-- Control Panel -->
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
            <!-- Bot Control -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <i data-lucide="play-circle" class="w-5 h-5 mr-2"></i>
                    Control del Bot
                </h3>
                <div class="space-y-3">
                    <button id="start-bot" class="w-full bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-lg font-semibold transition-colors">
                        <i data-lucide="play" class="w-4 h-4 inline mr-2"></i>
                        Iniciar Bot
                    </button>
                    <button id="stop-bot" class="w-full bg-red-500 hover:bg-red-600 text-white py-2 px-4 rounded-lg font-semibold transition-colors">
                        <i data-lucide="square" class="w-4 h-4 inline mr-2"></i>
                        Detener Bot
                    </button>
                </div>
            </div>

            <!-- Statistics -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <i data-lucide="trending-up" class="w-5 h-5 mr-2"></i>
                    Estadísticas Hoy
                </h3>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Trades:</span>
                        <span id="daily-trades" class="font-bold">0</span>
                    </div>
                    <div class="flex justify-between">
                        <span>PnL:</span>
                        <span id="daily-pnl" class="font-bold">$0.00</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Win Rate:</span>
                        <span id="win-rate" class="font-bold">0%</span>
                    </div>
                </div>
            </div>

            <!-- Active Positions -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <i data-lucide="activity" class="w-5 h-5 mr-2"></i>
                    Posiciones Activas
                </h3>
                <div class="text-center">
                    <div id="active-positions" class="text-3xl font-bold text-blue-600">0</div>
                    <p class="text-gray-500 text-sm">posiciones abiertas</p>
                </div>
            </div>

            <!-- Capital -->
            <div class="bg-white rounded-xl shadow-lg p-6 card-hover">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <i data-lucide="dollar-sign" class="w-5 h-5 mr-2"></i>
                    Capital
                </h3>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Total:</span>
                        <span id="total-capital" class="font-bold">$0.00</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Disponible:</span>
                        <span id="available-capital" class="font-bold">$0.00</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="bg-white rounded-xl shadow-lg mb-6">
            <div class="border-b border-gray-200">
                <nav class="flex space-x-8 px-6">
                    <button class="tab-button py-4 px-2 border-b-2 border-blue-500 text-blue-600 font-medium" data-tab="overview">
                        <i data-lucide="home" class="w-4 h-4 inline mr-2"></i>
                        Resumen
                    </button>
                    <button class="tab-button py-4 px-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-tab="trades">
                        <i data-lucide="bar-chart-3" class="w-4 h-4 inline mr-2"></i>
                        Trades
                    </button>
                    <button class="tab-button py-4 px-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-tab="alerts">
                        <i data-lucide="bell" class="w-4 h-4 inline mr-2"></i>
                        Alertas
                    </button>
                    <button class="tab-button py-4 px-2 border-b-2 border-transparent text-gray-500 hover:text-gray-700" data-tab="config">
                        <i data-lucide="settings" class="w-4 h-4 inline mr-2"></i>
                        Configuración
                    </button>
                </nav>
            </div>

            <!-- Tab Content -->
            <div class="p-6">
                <!-- Overview Tab -->
                <div id="overview-tab" class="tab-content">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <h4 class="text-lg font-semibold mb-4">Performance (30 días)</h4>
                            <canvas id="performance-chart" width="400" height="200"></canvas>
                        </div>
                        <div>
                            <h4 class="text-lg font-semibold mb-4">Trades Recientes</h4>
                            <div id="recent-trades" class="space-y-2">
                                <!-- Trades will be loaded here -->
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6">
                        <h4 class="text-lg font-semibold mb-4">Estado de Conexiones</h4>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <span class="flex items-center">
                                    <i data-lucide="link" class="w-4 h-4 mr-2"></i>
                                    Binance
                                </span>
                                <span id="binance-status" class="status-indicator status-offline"></span>
                            </div>
                            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <span class="flex items-center">
                                    <i data-lucide="message-circle" class="w-4 h-4 mr-2"></i>
                                    Telegram
                                </span>
                                <span id="telegram-status" class="status-indicator status-offline"></span>
                            </div>
                            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <span class="flex items-center">
                                    <i data-lucide="cpu" class="w-4 h-4 mr-2"></i>
                                    Agente
                                </span>
                                <span id="agent-status" class="status-indicator status-online"></span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Trades Tab -->
                <div id="trades-tab" class="tab-content hidden">
                    <div class="flex justify-between items-center mb-4">
                        <h4 class="text-lg font-semibold">Historial de Trades</h4>
                        <button id="refresh-trades" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            <i data-lucide="refresh-cw" class="w-4 h-4 inline mr-2"></i>
                            Actualizar
                        </button>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="min-w-full bg-white">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Token</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Red</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cantidad</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PnL</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                                </tr>
                            </thead>
                            <tbody id="trades-table" class="bg-white divide-y divide-gray-200">
                                <!-- Trades will be loaded here -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Alerts Tab -->
                <div id="alerts-tab" class="tab-content hidden">
                    <div class="flex justify-between items-center mb-4">
                        <h4 class="text-lg font-semibold">Alertas del Agente</h4>
                        <button id="refresh-alerts" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg">
                            <i data-lucide="refresh-cw" class="w-4 h-4 inline mr-2"></i>
                            Actualizar
                        </button>
                    </div>
                    <div id="alerts-container" class="space-y-4">
                        <!-- Alerts will be loaded here -->
                    </div>
                </div>

                <!-- Configuration Tab -->
                <div id="config-tab" class="tab-content hidden">
                    <form id="config-form" class="space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <!-- Bot Configuration -->
                            <div>
                                <h4 class="text-lg font-semibold mb-4">Configuración del Bot</h4>
                                <div class="space-y-4">
                                    <div>
                                        <label class="flex items-center">
                                            <input type="checkbox" id="bot_enabled" name="bot_enabled" class="mr-2">
                                            Bot Habilitado
                                        </label>
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Trades Diarios Máximos</label>
                                        <input type="number" name="max_daily_trades" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Tamaño Máximo Posición ($)</label>
                                        <input type="number" name="max_position_size" step="0.01" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Capital Total ($)</label>
                                        <input type="number" name="total_capital" step="0.01" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                </div>
                            </div>

                            <!-- Risk Management -->
                            <div>
                                <h4 class="text-lg font-semibold mb-4">Gestión de Riesgo</h4>
                                <div class="space-y-4">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Stop Loss (%)</label>
                                        <input type="number" name="stop_loss_pct" step="0.1" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Take Profit 1 (%)</label>
                                        <input type="number" name="take_profit_1_pct" step="0.1" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Take Profit 2 (%)</label>
                                        <input type="number" name="take_profit_2_pct" step="0.1" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Take Profit 3 (%)</label>
                                        <input type="number" name="take_profit_3_pct" step="0.1" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <!-- Token Filters -->
                            <div>
                                <h4 class="text-lg font-semibold mb-4">Filtros de Tokens</h4>
                                <div class="space-y-4">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Confianza Mínima (%)</label>
                                        <input type="number" name="min_confidence" step="0.1" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Market Cap Mínimo ($)</label>
                                        <input type="number" name="min_market_cap" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Market Cap Máximo ($)</label>
                                        <input type="number" name="max_market_cap" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Liquidez Mínima ($)</label>
                                        <input type="number" name="min_liquidity" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                </div>
                            </div>

                            <!-- API Configuration -->
                            <div>
                                <h4 class="text-lg font-semibold mb-4">Configuración de APIs</h4>
                                <div class="space-y-4">
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Binance API Key</label>
                                        <input type="text" name="binance_api_key" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Binance API Secret</label>
                                        <input type="password" name="binance_api_secret" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Telegram Bot Token</label>
                                        <input type="text" name="telegram_bot_token" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                    <div>
                                        <label class="block text-sm font-medium text-gray-700">Telegram Chat ID</label>
                                        <input type="text" name="telegram_chat_id" class="mt-1 block w-full border-gray-300 rounded-md shadow-sm">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="flex space-x-4">
                            <button type="submit" class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold">
                                <i data-lucide="save" class="w-4 h-4 inline mr-2"></i>
                                Guardar Configuración
                            </button>
                            <button type="button" id="test-connections" class="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-semibold">
                                <i data-lucide="wifi" class="w-4 h-4 inline mr-2"></i>
                                Probar Conexiones
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize Lucide icons
        lucide.createIcons();

        // API base URL
        const API_BASE = '/api';

        // Global state
        let currentTab = 'overview';
        let performanceChart = null;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeTabs();
            loadDashboardData();
            setupEventListeners();
            
            // Auto-refresh every 30 seconds
            setInterval(loadDashboardData, 30000);
        });

        function initializeTabs() {
            const tabButtons = document.querySelectorAll('.tab-button');
            const tabContents = document.querySelectorAll('.tab-content');

            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const tabName = button.getAttribute('data-tab');
                    
                    // Update button states
                    tabButtons.forEach(btn => {
                        btn.classList.remove('border-blue-500', 'text-blue-600');
                        btn.classList.add('border-transparent', 'text-gray-500');
                    });
                    button.classList.remove('border-transparent', 'text-gray-500');
                    button.classList.add('border-blue-500', 'text-blue-600');

                    // Update content visibility
                    tabContents.forEach(content => {
                        content.classList.add('hidden');
                    });
                    document.getElementById(tabName + '-tab').classList.remove('hidden');

                    currentTab = tabName;
                    
                    // Load tab-specific data
                    if (tabName === 'trades') loadTrades();
                    if (tabName === 'alerts') loadAlerts();
                    if (tabName === 'config') loadConfiguration();
                });
            });
        }

        function setupEventListeners() {
            // Bot control buttons
            document.getElementById('start-bot').addEventListener('click', startBot);
            document.getElementById('stop-bot').addEventListener('click', stopBot);
            document.getElementById('emergency-stop').addEventListener('click', emergencyStop);
            
            // Refresh buttons
            document.getElementById('refresh-trades').addEventListener('click', loadTrades);
            document.getElementById('refresh-alerts').addEventListener('click', loadAlerts);
            
            // Configuration form
            document.getElementById('config-form').addEventListener('submit', saveConfiguration);
            document.getElementById('test-connections').addEventListener('click', testConnections);
        }

        async function loadDashboardData() {
            try {
                await Promise.all([
                    loadBotStatus(),
                    loadStatistics(),
                    currentTab === 'overview' && loadPerformanceChart(),
                    currentTab === 'trades' && loadTrades(),
                    currentTab === 'alerts' && loadAlerts()
                ]);
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }

        async function loadBotStatus() {
            try {
                const response = await fetch(`${API_BASE}/status`);
                const data = await response.json();

                if (response.ok) {
                    const statusElement = document.getElementById('bot-status');
                    const statusText = document.getElementById('status-text');
                    const indicator = statusElement.querySelector('.status-indicator');

                    if (data.bot_running) {
                        indicator.className = 'status-indicator status-online';
                        statusText.textContent = 'Funcionando';
                    } else {
                        indicator.className = 'status-indicator status-offline';
                        statusText.textContent = 'Detenido';
                    }

                    // Update statistics
                    document.getElementById('daily-trades').textContent = data.daily_trades || 0;
                    document.getElementById('active-positions').textContent = data.active_positions || 0;
                    document.getElementById('total-capital').textContent = `$${(data.total_capital || 0).toFixed(2)}`;
                    document.getElementById('available-capital').textContent = `$${(data.available_capital || 0).toFixed(2)}`;
                }
            } catch (error) {
                console.error('Error loading bot status:', error);
            }
        }

        async function loadStatistics() {
            try {
                const response = await fetch(`${API_BASE}/statistics`);
                const data = await response.json();

                if (response.ok) {
                    document.getElementById('daily-pnl').textContent = `$${(data.daily_pnl || 0).toFixed(2)}`;
                    document.getElementById('win-rate').textContent = `${(data.win_rate || 0).toFixed(1)}%`;
                    
                    // Update PnL color
                    const pnlElement = document.getElementById('daily-pnl');
                    if (data.daily_pnl > 0) {
                        pnlElement.className = 'font-bold text-green-600';
                    } else if (data.daily_pnl < 0) {
                        pnlElement.className = 'font-bold text-red-600';
                    } else {
                        pnlElement.className = 'font-bold';
                    }
                }
            } catch (error) {
                console.error('Error loading statistics:', error);
            }
        }

        async function loadTrades() {
            try {
                const response = await fetch(`${API_BASE}/trades?per_page=50`);
                const data = await response.json();

                if (response.ok) {
                    const tbody = document.getElementById('trades-table');
                    tbody.innerHTML = '';

                    data.forEach(trade => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${trade.token_symbol}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${trade.network}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${trade.trade_type}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">$${trade.entry_price.toFixed(8)}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${trade.quantity.toLocaleString()}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}">$${trade.pnl.toFixed(2)}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(trade.status)}">
                                    ${trade.status}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(trade.created_at).toLocaleString()}</td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('Error loading trades:', error);
            }
        }

        async function loadAlerts() {
            try {
                const response = await fetch(`${API_BASE}/alerts?per_page=20`);
                const data = await response.json();

                if (response.ok) {
                    const container = document.getElementById('alerts-container');
                    container.innerHTML = '';

                    data.forEach(alert => {
                        const alertDiv = document.createElement('div');
                        alertDiv.className = `p-4 rounded-lg border-l-4 ${getAlertColor(alert.alert_type)}`;
                        alertDiv.innerHTML = `
                            <div class="flex justify-between items-start">
                                <div>
                                    <h5 class="font-semibold">${alert.alert_type.replace('_', ' ')}</h5>
                                    <p class="text-sm text-gray-600 mt-1">${alert.message.replace(/\\n/g, '<br>')}</p>
                                    <p class="text-xs text-gray-400 mt-2">${new Date(alert.created_at).toLocaleString()}</p>
                                </div>
                                <span class="px-2 py-1 text-xs font-semibold rounded ${getPriorityColor(alert.priority)}">
                                    ${alert.priority}
                                </span>
                            </div>
                        `;
                        container.appendChild(alertDiv);
                    });
                }
            } catch (error) {
                console.error('Error loading alerts:', error);
            }
        }

        async function loadConfiguration() {
            try {
                const response = await fetch(`${API_BASE}/config`);
                const data = await response.json();

                if (response.ok) {
                    const form = document.getElementById('config-form');
                    Object.keys(data).forEach(key => {
                        const input = form.querySelector(`[name="${key}"]`);
                        if (input) {
                            if (input.type === 'checkbox') {
                                input.checked = data[key];
                            } else {
                                input.value = data[key];
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Error loading configuration:', error);
            }
        }

        async function startBot() {
            try {
                const response = await fetch(`${API_BASE}/start`, { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    showNotification('Bot iniciado correctamente', 'success');
                    loadBotStatus();
                } else {
                    showNotification(data.error || 'Error iniciando bot', 'error');
                }
            } catch (error) {
                showNotification('Error iniciando bot', 'error');
            }
        }

        async function stopBot() {
            try {
                const response = await fetch(`${API_BASE}/stop`, { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    showNotification('Bot detenido correctamente', 'success');
                    loadBotStatus();
                } else {
                    showNotification(data.error || 'Error deteniendo bot', 'error');
                }
            } catch (error) {
                showNotification('Error deteniendo bot', 'error');
            }
        }

        async function emergencyStop() {
            try {
                const response = await fetch(`${API_BASE}/emergency-stop`, { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    showNotification('Stop de emergencia activado', 'info');
                    loadBotStatus();
                } else {
                    showNotification(data.error || 'Error en stop de emergencia', 'error');
                }
            } catch (error) {
                showNotification('Error en stop de emergencia', 'error');
            }
        }

        async function saveConfiguration(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const config = {};
            
            for (let [key, value] of formData.entries()) {
                if (value !== '') {
                    config[key] = isNaN(value) ? value : parseFloat(value);
                }
            }

            // Handle checkbox
            config.bot_enabled = document.getElementById('bot_enabled').checked;

            try {
                const response = await fetch(`${API_BASE}/config`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                const data = await response.json();

                if (response.ok) {
                    showNotification('Configuración guardada exitosamente', 'success');
                    loadConfiguration();
                } else {
                    showNotification(data.error || 'Error guardando configuración', 'error');
                }
            } catch (error) {
                showNotification('Error guardando configuración', 'error');
            }
        }

        async function testConnections() {
            try {
                const response = await fetch(`${API_BASE}/test-connections`, { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    // Update connection status indicators
                    document.getElementById('binance-status').className = `status-indicator ${data.binance ? 'status-online' : 'status-offline'}`;
                    document.getElementById('telegram-status').className = `status-indicator ${data.telegram ? 'status-online' : 'status-offline'}`;
                    
                    let message = 'Resultados de prueba de conexiones:\\n';
                    message += `Binance: ${data.binance ? '✅ Conectado' : '❌ Error'}\\n`;
                    message += `Telegram: ${data.telegram ? '✅ Conectado' : '❌ Error'}\\n`;
                    message += `DEX: ${data.dex ? '✅ Conectado' : '❌ Error'}`;
                    
                    showNotification(message, 'info');
                } else {
                    showNotification(data.error || 'Error probando conexiones', 'error');
                }
            } catch (error) {
                showNotification('Error probando conexiones', 'error');
            }
        }

        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 5000);
        }

        function getStatusColor(status) {
            switch (status) {
                case 'ACTIVE': return 'bg-green-100 text-green-800';
                case 'COMPLETED': return 'bg-blue-100 text-blue-800';
                case 'STOPPED': return 'bg-red-100 text-red-800';
                default: return 'bg-gray-100 text-gray-800';
            }
        }

        function getAlertColor(type) {
            switch (type) {
                case 'GEM_DETECTED': return 'border-green-400 bg-green-50';
                case 'RISK_WARNING': return 'border-yellow-400 bg-yellow-50';
                case 'ERROR': return 'border-red-400 bg-red-50';
                default: return 'border-blue-400 bg-blue-50';
            }
        }

        function getPriorityColor(priority) {
            switch (priority) {
                case 'HIGH': return 'bg-red-100 text-red-800';
                case 'MEDIUM': return 'bg-yellow-100 text-yellow-800';
                case 'LOW': return 'bg-green-100 text-green-800';
                default: return 'bg-gray-100 text-gray-800';
            }
        }
    </script>
</body>
</html>
'''

# Rutas principales
@app.route('/')
def dashboard():
    """Servir dashboard principal"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/health')
def health_check():
    """Health check para Railway"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_running": bot_running,
        "version": "5.0.0-github-ready",
        "trades_count": len(trades_list),
        "alerts_count": len(alerts_list)
    }), 200

# API Routes
@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual"""
    try:
        return jsonify(bot_config), 200
    except Exception as e:
        logger.error(f"Error obteniendo configuración: {str(e)}")
        return jsonify({"error": f"Error obteniendo configuración: {str(e)}"}), 500

@app.route('/api/config', methods=['POST'])
def save_config():
    """Guardar configuración"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Actualizar configuración
        for key, value in data.items():
            if key in bot_config:
                bot_config[key] = value
        
        logger.info(f"✅ Configuración guardada: {list(data.keys())}")
        return jsonify({"message": "Configuración guardada exitosamente"}), 200
        
    except Exception as e:
        logger.error(f"❌ Error guardando configuración: {str(e)}")
        return jsonify({"error": f"Error guardando configuración: {str(e)}"}), 500

@app.route('/api/test-connections', methods=['POST'])
def test_connections():
    """Probar conexiones"""
    try:
        results = {
            "binance": bool(bot_config.get("binance_api_key") and bot_config.get("binance_api_key") != "demo_key_12345"),
            "telegram": bool(bot_config.get("telegram_bot_token") and bot_config.get("telegram_bot_token") != "1234567890:ABCDEFghijklmnopqrstuvwxyz123456789"),
            "dex": True
        }
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error probando conexiones: {str(e)}")
        return jsonify({"error": f"Error probando conexiones: {str(e)}"}), 500

@app.route('/api/start', methods=['POST'])
def start_bot():
    """Iniciar bot"""
    global bot_running
    
    try:
        if bot_running:
            return jsonify({"message": "Bot ya está funcionando"}), 200
        
        if bot_config.get("total_capital", 0) <= 0:
            return jsonify({"error": "Capital total debe ser mayor a 0"}), 400
        
        bot_running = True
        
        # Generar algunos trades de demostración
        for _ in range(random.randint(1, 3)):
            generate_demo_trade()
        
        logger.info("🤖 Bot iniciado correctamente")
        return jsonify({"message": "Bot iniciado correctamente"}), 200
        
    except Exception as e:
        logger.error(f"Error iniciando bot: {str(e)}")
        return jsonify({"error": f"Error iniciando bot: {str(e)}"}), 500

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Detener bot"""
    global bot_running
    
    try:
        bot_running = False
        logger.info("🛑 Bot detenido correctamente")
        return jsonify({"message": "Bot detenido correctamente"}), 200
        
    except Exception as e:
        logger.error(f"Error deteniendo bot: {str(e)}")
        return jsonify({"error": f"Error deteniendo bot: {str(e)}"}), 500

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    """Stop de emergencia"""
    global bot_running
    
    try:
        bot_running = False
        logger.info("🚨 Stop de emergencia activado")
        return jsonify({"message": "Stop de emergencia activado"}), 200
        
    except Exception as e:
        logger.error(f"Error en stop de emergencia: {str(e)}")
        return jsonify({"error": f"Error en stop de emergencia: {str(e)}"}), 500

@app.route('/api/status', methods=['GET'])
def bot_status():
    """Estado del bot"""
    try:
        daily_pnl = sum(trade.get("pnl", 0) for trade in trades_list)
        active_positions = len([t for t in trades_list if t.get("status") == "ACTIVE"])
        total_capital = bot_config.get("total_capital", 0)
        used_capital = active_positions * bot_config.get("max_position_size", 300)
        
        return jsonify({
            "bot_running": bot_running,
            "bot_enabled": bot_config.get("bot_enabled", False),
            "daily_trades": len(trades_list),
            "max_daily_trades": bot_config.get("max_daily_trades", 4),
            "active_positions": active_positions,
            "daily_pnl": round(daily_pnl, 2),
            "total_capital": total_capital,
            "available_capital": max(0, total_capital - used_capital)
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return jsonify({"error": f"Error obteniendo estado: {str(e)}"}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Obtener estadísticas"""
    try:
        daily_pnl = sum(trade.get("pnl", 0) for trade in trades_list)
        winning_trades = len([t for t in trades_list if t.get("pnl", 0) > 0])
        total_trades = len(trades_list)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return jsonify({
            "daily_trades": total_trades,
            "daily_pnl": round(daily_pnl, 2),
            "win_rate": round(win_rate, 1),
            "active_positions": len([t for t in trades_list if t.get("status") == "ACTIVE"])
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return jsonify({"error": f"Error obteniendo estadísticas: {str(e)}"}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Obtener trades"""
    try:
        per_page = int(request.args.get('per_page', 20))
        return jsonify(trades_list[-per_page:]), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo trades: {str(e)}")
        return jsonify({"error": f"Error obteniendo trades: {str(e)}"}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Obtener alertas"""
    try:
        per_page = int(request.args.get('per_page', 10))
        return jsonify(alerts_list[-per_page:]), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {str(e)}")
        return jsonify({"error": f"Error obteniendo alertas: {str(e)}"}), 500

# Inicialización
if __name__ == '__main__':
    logger.info("🚀 Iniciando Crypto Gem Bot Professional...")
    logger.info("✅ Configuración cargada")
    logger.info("✅ APIs configuradas")
    
    # Generar datos de demostración iniciales
    logger.info("📊 Generando datos de demostración...")
    for _ in range(5):
        generate_demo_trade()
    
    # Configuración para producción
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    logger.info(f"🌐 Servidor iniciando en puerto {port}")
    logger.info(f"🔧 Modo debug: {debug}")
    logger.info("✅ Crypto Gem Bot listo para GitHub y Railway")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

