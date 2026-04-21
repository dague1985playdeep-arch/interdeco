"""
Inter-Deco DM Manager - Advanced Features Module
Características avanzadas: Analytics, Scheduling, Integrations
"""

import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify
from main import app, db, Conversation, Customer
from sqlalchemy import func, and_


# ==================== DECORADORES ====================

def require_api_key(f):
    """Decorador para proteger endpoints sensibles con API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.getenv("ADMIN_API_KEY", "inter-deco-secret-2024")
        provided_key = request.headers.get('X-API-Key')
        
        if provided_key != api_key:
            return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# ==================== ANALYTICS ====================

class ConversationAnalytics:
    """Análisis avanzado de conversaciones"""
    
    @staticmethod
    def get_daily_stats(days=30):
        """Estadísticas diarias de los últimos N días"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        daily_stats = db.session.query(
            func.date(Conversation.created_at).label('date'),
            func.count(Conversation.id).label('total_messages'),
            func.count(func.distinct(Conversation.customer_id)).label('unique_customers')
        ).filter(
            Conversation.created_at >= start_date
        ).group_by(
            func.date(Conversation.created_at)
        ).all()
        
        return [
            {
                'date': str(stat.date),
                'total_messages': stat.total_messages,
                'unique_customers': stat.unique_customers
            }
            for stat in daily_stats
        ]
    
    @staticmethod
    def get_category_distribution():
        """Distribución de categorías de mensajes"""
        categories = db.session.query(
            Conversation.category,
            func.count(Conversation.id).label('count')
        ).group_by(Conversation.category).all()
        
        return {
            category: count for category, count in categories
        }
    
    @staticmethod
    def get_top_customers(limit=10):
        """Clientes con más conversaciones"""
        top = db.session.query(
            Customer.id,
            Customer.name,
            func.count(Conversation.id).label('message_count')
        ).join(Conversation).group_by(
            Customer.id
        ).order_by(
            func.count(Conversation.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'customer_id': c.id,
                'name': c.name,
                'total_messages': c.message_count
            }
            for c in top
        ]
    
    @staticmethod
    def get_response_time_analytics():
        """Análisis de tiempo de respuesta"""
        # Tiempo promedio entre mensaje de cliente y respuesta de IA
        
        conversations = db.session.query(Conversation).order_by(
            Conversation.created_at
        ).all()
        
        response_times = []
        for i in range(1, len(conversations)):
            if conversations[i].customer_id == conversations[i-1].customer_id:
                time_diff = (conversations[i].created_at - 
                           conversations[i-1].created_at).total_seconds()
                response_times.append(time_diff)
        
        if not response_times:
            return {"avg": 0, "min": 0, "max": 0}
        
        return {
            'avg_seconds': sum(response_times) / len(response_times),
            'min_seconds': min(response_times),
            'max_seconds': max(response_times),
            'total_samples': len(response_times)
        }
    
    @staticmethod
    def get_engagement_score(customer_id):
        """Puntuación de engagement por cliente"""
        total_msgs = db.session.query(func.count(Conversation.id)).filter_by(
            customer_id=customer_id
        ).scalar()
        
        customer = Customer.query.get(customer_id)
        if not customer:
            return 0
        
        days_since_creation = (datetime.utcnow() - customer.created_at).days + 1
        msg_per_day = total_msgs / days_since_creation if days_since_creation > 0 else 0
        
        # Score: 0-100
        # Basado en: mensajes por día, recencia, categoría
        score = min(100, msg_per_day * 10)
        
        return {
            'customer_id': customer_id,
            'score': round(score, 2),
            'total_messages': total_msgs,
            'days_active': days_since_creation,
            'messages_per_day': round(msg_per_day, 2)
        }


class SentimentAnalysis:
    """Análisis de sentimiento de mensajes (extensión futura)"""
    
    @staticmethod
    def classify_sentiment(text):
        """
        Clasifica el sentimiento de un mensaje
        Implementación básica por palabras clave
        Puede mejorar con TextBlob o transformers
        """
        positive_words = ['bueno', 'excelente', 'perfecto', 'gracias', 'feliz', 'genial']
        negative_words = ['malo', 'terrible', 'problema', 'error', 'enojado', 'decepción']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'


# ==================== SCHEDULING ====================

class MessageScheduler:
    """Programación de mensajes automáticos"""
    
    # Esta clase requería APScheduler
    # pip install APScheduler
    
    @staticmethod
    def schedule_message(customer_id, message, send_time):
        """
        Programa un mensaje para enviarse a una hora específica
        
        Args:
            customer_id: ID del cliente
            message: Texto del mensaje
            send_time: datetime cuando enviar
        """
        # Ejemplo de implementación:
        # from apscheduler.schedulers.background import BackgroundScheduler
        # scheduler = BackgroundScheduler()
        # scheduler.add_job(
        #     func=send_scheduled_message,
        #     args=[customer_id, message],
        #     trigger="date",
        #     run_date=send_time
        # )
        # scheduler.start()
        pass
    
    @staticmethod
    def schedule_bulk_message(customer_ids, message, send_time):
        """Programa mensaje para múltiples clientes"""
        pass


# ==================== EMAIL NOTIFICATIONS ====================

class EmailNotifications:
    """Notificaciones por email de eventos importantes"""
    
    # Requiere: pip install Flask-Mail
    
    @staticmethod
    def send_urgent_notification(customer_id, message):
        """Envía email cuando hay un mensaje URGENTE"""
        # from flask_mail import Mail, Message
        # mail = Mail(app)
        # msg = Message(
        #     'Mensaje Urgente en Inter-Deco',
        #     recipients=[os.getenv('ADMIN_EMAIL')],
        #     body=f"Cliente {customer_id}: {message}"
        # )
        # mail.send(msg)
        pass
    
    @staticmethod
    def send_daily_summary():
        """Envía resumen diario por email"""
        pass


# ==================== EXPORTACIÓN DE DATOS ====================

class DataExport:
    """Exportación de datos en varios formatos"""
    
    @staticmethod
    def export_to_csv(customer_id=None):
        """Exporta conversaciones a CSV"""
        import csv
        from io import StringIO
        
        query = Conversation.query
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        
        conversations = query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Customer ID', 'Date', 'User Message', 
            'AI Response', 'Category'
        ])
        
        # Data
        for conv in conversations:
            writer.writerow([
                conv.id,
                conv.customer_id,
                conv.created_at.isoformat(),
                conv.user_message,
                conv.ai_response,
                conv.category
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_to_json(customer_id=None):
        """Exporta conversaciones a JSON"""
        query = Conversation.query
        if customer_id:
            query = query.filter_by(customer_id=customer_id)
        
        conversations = query.all()
        
        data = {
            'exported_at': datetime.utcnow().isoformat(),
            'conversations': [
                {
                    'id': conv.id,
                    'customer_id': conv.customer_id,
                    'date': conv.created_at.isoformat(),
                    'user_message': conv.user_message,
                    'ai_response': conv.ai_response,
                    'category': conv.category
                }
                for conv in conversations
            ]
        }
        
        return json.dumps(data, indent=2)
    
    @staticmethod
    def export_to_pdf(customer_id=None):
        """Exporta conversaciones a PDF"""
        # from reportlab.lib.pagesizes import letter
        # from reportlab.pdfgen import canvas
        # 
        # c = canvas.Canvas("conversations.pdf", pagesize=letter)
        # # ... generar PDF
        # c.save()
        pass


# ==================== INTEGRACIONES ====================

class ExternalIntegrations:
    """Integraciones con servicios externos"""
    
    # Salesforce CRM
    @staticmethod
    def sync_to_salesforce(customer_id):
        """Sincroniza datos de cliente a Salesforce"""
        # import requests
        # customer = Customer.query.get(customer_id)
        # sf_data = {
        #     'Name': customer.name,
        #     'Phone': customer.phone,
        #     'Email': customer.email
        # }
        # requests.post('https://salesforce.com/api/...', json=sf_data)
        pass
    
    # Slack Notifications
    @staticmethod
    def send_slack_notification(message, channel="#inter-deco"):
        """Envía notificación a Slack"""
        # import requests
        # webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        # requests.post(webhook_url, json={'text': message})
        pass
    
    # WhatsApp Business API
    @staticmethod
    def send_whatsapp_message(phone, message):
        """Envía mensaje por WhatsApp Business API"""
        # Este requeriría WhatsApp Business API credentials
        # Similar a Meta API pero para WhatsApp
        pass
    
    # Google Sheets Integration
    @staticmethod
    def sync_to_google_sheets(spreadsheet_id):
        """Sincroniza conversaciones a Google Sheets"""
        # from google.oauth2.service_account import Credentials
        # from google.auth.transport.requests import Request
        # 
        # # Autenticar y actualizar sheet
        pass
    
    # Telegram Bot
    @staticmethod
    def send_telegram_notification(message):
        """Envía notificación a bot de Telegram"""
        # import requests
        # bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        # chat_id = os.getenv('TELEGRAM_CHAT_ID')
        # 
        # url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        # requests.post(url, json={
        #     'chat_id': chat_id,
        #     'text': message
        # })
        pass


# ==================== RUTAS PARA ADVANCED FEATURES ====================

def register_advanced_routes(app):
    """Registra rutas para características avanzadas"""
    
    @app.route('/api/analytics/daily-stats', methods=['GET'])
    def get_daily_stats():
        """Estadísticas diarias"""
        days = request.args.get('days', 30, type=int)
        stats = ConversationAnalytics.get_daily_stats(days)
        return jsonify(stats)
    
    @app.route('/api/analytics/categories', methods=['GET'])
    def get_categories():
        """Distribución de categorías"""
        dist = ConversationAnalytics.get_category_distribution()
        return jsonify(dist)
    
    @app.route('/api/analytics/top-customers', methods=['GET'])
    def get_top_customers():
        """Top clientes"""
        limit = request.args.get('limit', 10, type=int)
        top = ConversationAnalytics.get_top_customers(limit)
        return jsonify(top)
    
    @app.route('/api/analytics/response-time', methods=['GET'])
    def get_response_time():
        """Análisis de tiempo de respuesta"""
        stats = ConversationAnalytics.get_response_time_analytics()
        return jsonify(stats)
    
    @app.route('/api/analytics/engagement/<customer_id>', methods=['GET'])
    def get_engagement(customer_id):
        """Score de engagement del cliente"""
        score = ConversationAnalytics.get_engagement_score(customer_id)
        return jsonify(score)
    
    @app.route('/api/export/csv', methods=['GET'])
    def export_csv():
        """Exporta a CSV"""
        customer_id = request.args.get('customer_id')
        csv_data = DataExport.export_to_csv(customer_id)
        
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=conversations.csv'
        }
    
    @app.route('/api/export/json', methods=['GET'])
    def export_json():
        """Exporta a JSON"""
        customer_id = request.args.get('customer_id')
        json_data = DataExport.export_to_json(customer_id)
        return json_data, 200, {
            'Content-Type': 'application/json'
        }
    
    @app.route('/api/sentiment/<int:conversation_id>', methods=['GET'])
    def get_sentiment(conversation_id):
        """Análisis de sentimiento de una conversación"""
        conv = Conversation.query.get(conversation_id)
        if not conv:
            return jsonify({"error": "Not found"}), 404
        
        sentiment = SentimentAnalysis.classify_sentiment(conv.user_message)
        return jsonify({
            'conversation_id': conversation_id,
            'sentiment': sentiment,
            'message': conv.user_message[:100]
        })


# ==================== UTILIDADES ====================

class ReportGenerator:
    """Generador de reportes avanzados"""
    
    @staticmethod
    def generate_monthly_report(month, year):
        """Genera reporte mensual completo"""
        from datetime import date
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        conversations = Conversation.query.filter(
            and_(
                Conversation.created_at >= start_date,
                Conversation.created_at < end_date
            )
        ).all()
        
        customers = Customer.query.filter(
            and_(
                Customer.created_at >= start_date,
                Customer.created_at < end_date
            )
        ).all()
        
        report = {
            'period': f"{month}/{year}",
            'total_conversations': len(conversations),
            'new_customers': len(customers),
            'categories': ConversationAnalytics.get_category_distribution(),
            'top_customers': ConversationAnalytics.get_top_customers(5),
            'response_time': ConversationAnalytics.get_response_time_analytics(),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    @staticmethod
    def generate_customer_report(customer_id):
        """Reporte detallado por cliente"""
        customer = Customer.query.get(customer_id)
        if not customer:
            return None
        
        conversations = Conversation.query.filter_by(
            customer_id=customer_id
        ).all()
        
        categories = {}
        for conv in conversations:
            categories[conv.category] = categories.get(conv.category, 0) + 1
        
        report = {
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'created_at': customer.created_at.isoformat()
            },
            'total_messages': len(conversations),
            'categories': categories,
            'first_contact': conversations[0].created_at.isoformat() if conversations else None,
            'last_contact': conversations[-1].created_at.isoformat() if conversations else None,
            'conversation_history': [
                {
                    'date': conv.created_at.isoformat(),
                    'user_message': conv.user_message,
                    'ai_response': conv.ai_response,
                    'category': conv.category
                }
                for conv in conversations
            ]
        }
        
        return report


# ==================== HEALTH CHECKS ====================

class HealthCheck:
    """Verificaciones de salud del sistema"""
    
    @staticmethod
    def check_database():
        """Verifica conexión a BD"""
        try:
            db.session.execute('SELECT 1')
            return {'status': 'healthy', 'database': 'ok'}
        except Exception as e:
            return {'status': 'unhealthy', 'database': f'error: {str(e)}'}
    
    @staticmethod
    def check_meta_api():
        """Verifica conexión a Meta API"""
        import requests
        try:
            from main import dm_manager
            response = requests.get(
                f"https://graph.instagram.com/v21.0/me",
                params={'access_token': os.getenv('META_ACCESS_TOKEN')},
                timeout=5
            )
            if response.status_code == 200:
                return {'status': 'healthy', 'meta_api': 'ok'}
            else:
                return {'status': 'unhealthy', 'meta_api': f'status {response.status_code}'}
        except Exception as e:
            return {'status': 'unhealthy', 'meta_api': f'error: {str(e)}'}
    
    @staticmethod
    def check_openai_api():
        """Verifica conexión a OpenAI"""
        from main import client
        try:
            # Verificación simple
            response = client.models.list()
            return {'status': 'healthy', 'openai_api': 'ok'}
        except Exception as e:
            return {'status': 'unhealthy', 'openai_api': f'error: {str(e)}'}
    
    @staticmethod
    def full_health_check():
        """Verificación completa del sistema"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'database': HealthCheck.check_database(),
            'meta_api': HealthCheck.check_meta_api(),
            'openai_api': HealthCheck.check_openai_api()
        }


if __name__ == "__main__":
    # Test analytics
    print("Sample Analytics:")
    print(ConversationAnalytics.get_category_distribution())
    print(ConversationAnalytics.get_top_customers(5))
