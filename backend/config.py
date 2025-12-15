"""
Configuration settings for the finance application
"""
import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
EXPORTS_DIR = DATA_DIR / 'exports'
IMPORTS_DIR = DATA_DIR / 'imports'
LOGS_DIR = BASE_DIR / 'logs'

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)
IMPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database settings
DATABASE_PATH = DATA_DIR / 'finance.db'
DATABASE_BACKUP_DIR = DATA_DIR / 'backups'
DATABASE_BACKUP_DIR.mkdir(exist_ok=True)

# ML settings
ML_CONFIDENCE_THRESHOLD = 0.7
ANOMALY_DETECTION_THRESHOLD = 2.0
MIN_TRANSACTIONS_FOR_TRAINING = 10

# Analytics settings
DEFAULT_ANALYSIS_DAYS = 30
RECENT_TRANSACTIONS_LIMIT = 100

# Application settings
APP_NAME = "Personal Finance Advisor"
APP_VERSION = "1.0.0"
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Logging
LOG_FILE = LOGS_DIR / 'app.log'
LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'

# Date formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

# Currency
DEFAULT_CURRENCY = 'USD'
CURRENCY_SYMBOL = '$'

# Budget settings
DEFAULT_BUDGET_PERIOD = 'monthly'
BUDGET_ALERT_THRESHOLD = 0.7  #70% of budget usage

# CSV Import settings
CSV_DATE_FORMATS = [
    '%Y-%m-%d',
    '%m/%d/%Y',
    '%d/%m/%Y',
    '%Y/%m/%d'
]

CSV_COLUMN_MAPPINGS = {
    'date': ['date', 'transaction date', 'posting date', 'trans date'],
    'amount': ['amount', 'debit', 'credit', 'value'],
    'merchant': ['merchant', 'description', 'name', 'payee', 'details'],
    'category': ['category', 'type', 'class']
}