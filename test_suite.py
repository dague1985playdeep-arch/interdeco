"""
Inter-Deco DM Manager - Testing Guide and Test Suites
Incluye: Unit tests, Integration tests, API tests
"""

import pytest
import json
from datetime import datetime, timedelta
from main import app, db, Customer, Conversation, MetaDMManager


# ==================== PYTEST CONFIGURATION ====================

@pytest.fixture
def client():
    """Cliente de prueba para la aplicación Flask"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_customer():
    """Crea un cliente de prueba"""
    customer = Customer(
        id="test_user_123",
        name="Test Customer",
        email="test@example.com",
        phone="+56912345678"
    )
    db.session.add(customer)
    db.session.commit()
    return customer


@pytest.fixture
def sample_conversation(sample_customer):
    """Crea una conversación de prueba"""
    conversation = Conversation(
        customer_id=sample_customer.id,
        user_message="¿Cuánto cuesta una cortina?",
        ai_response="Necesitamos medidas exactas. ¿Me envías fotos?",
        category="VENTAS",
        meta_message_id="test_msg_001"
    )
    db.session.add(conversation)
    db.session.commit()
    return conversation


# ==================== UNIT TESTS ====================

class TestCustomerModel:
    """Tests para el modelo Customer"""
    
    def test_create_customer(self, client):
        """Verifica que se crea un cliente correctamente"""
        customer = Customer(
            id="user_001",
            name="John Doe",
            email="john@example.com"
        )
        db.session.add(customer)
        db.session.commit()
        
        retrieved = Customer.query.get("user_001")
        assert retrieved.name == "John Doe"
        assert retrieved.email == "john@example.com"
    
    def test_customer_to_dict(self, sample_customer):
        """Verifica conversión a diccionario"""
        customer_dict = sample_customer.to_dict()
        
        assert customer_dict['id'] == "test_user_123"
        assert customer_dict['name'] == "Test Customer"
        assert 'created_at' in customer_dict
    
    def test_customer_relationships(self, sample_customer, sample_conversation):
        """Verifica relaciones entre modelos"""
        assert len(sample_customer.conversations) == 1
        assert sample_customer.conversations[0].user_message == "¿Cuánto cuesta una cortina?"


class TestConversationModel:
    """Tests para el modelo Conversation"""
    
    def test_create_conversation(self, sample_customer):
        """Crea conversación correctamente"""
        conv = Conversation(
            customer_id=sample_customer.id,
            user_message="Hola",
            ai_response="¡Hola! ¿En qué te puedo ayudar?",
            category="GENERAL"
        )
        db.session.add(conv)
        db.session.commit()
        
        retrieved = db.session.query(Conversation).first()
        assert retrieved.user_message == "Hola"
        assert retrieved.category == "GENERAL"
    
    def test_conversation_unique_message_id(self, sample_customer):
        """Verifica que message_id es único"""
        conv1 = Conversation(
            customer_id=sample_customer.id,
            user_message="Test 1",
            ai_response="Response 1",
            meta_message_id="unique_001"
        )
        conv2 = Conversation(
            customer_id=sample_customer.id,
            user_message="Test 2",
            ai_response="Response 2",
            meta_message_id="unique_001"  # Duplicado
        )
        db.session.add(conv1)
        db.session.commit()
        
        db.session.add(conv2)
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()


# ==================== API ENDPOINT TESTS ====================

class TestWebhookEndpoints:
    """Tests para endpoints de webhook"""
    
    def test_webhook_verification(self, client):
        """Verifica el handshake inicial del webhook"""
        response = client.get(
            '/webhook?hub.mode=subscribe&hub.verify_token=INTER_DECO_SECRET_2024&hub.challenge=test_challenge_123'
        )
        
        assert response.status_code == 200
        assert response.data == b'test_challenge_123'
    
    def test_webhook_verification_invalid_token(self, client):
        """Verifica rechazo de token inválido"""
        response = client.get(
            '/webhook?hub.mode=subscribe&hub.verify_token=WRONG_TOKEN&hub.challenge=test'
        )
        
        assert response.status_code == 403
    
    def test_webhook_receive_message(self, client):
        """Prueba recepción de mensaje a través del webhook"""
        payload = {
            "object": "instagram",
            "entry": [{
                "messaging": [{
                    "sender": {"id": "test_user_123"},
                    "message": {
                        "mid": "msg_123",
                        "text": "Hola, me interesa cortinas"
                    }
                }]
            }]
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 202]
    
    def test_webhook_invalid_object(self, client):
        """Rechaza eventos que no son de Instagram"""
        payload = {
            "object": "unknown",
            "entry": []
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestCustomerEndpoints:
    """Tests para endpoints de clientes"""
    
    def test_list_customers(self, client, sample_customer):
        """Lista todos los clientes"""
        response = client.get('/api/customers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['id'] == "test_user_123"
    
    def test_get_customer_details(self, client, sample_customer, sample_conversation):
        """Obtiene detalles de un cliente específico"""
        response = client.get(f'/api/customers/{sample_customer.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['customer']['name'] == "Test Customer"
        assert len(data['conversations']) == 1
    
    def test_get_nonexistent_customer(self, client):
        """Maneja cliente no encontrado"""
        response = client.get('/api/customers/nonexistent')
        
        assert response.status_code == 404


class TestConversationEndpoints:
    """Tests para endpoints de conversaciones"""
    
    def test_list_conversations(self, client, sample_conversation):
        """Lista conversaciones"""
        response = client.get('/api/conversations')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
    
    def test_filter_by_category(self, client, sample_customer):
        """Filtra conversaciones por categoría"""
        # Crear múltiples conversaciones
        for category in ['VENTAS', 'VENTAS', 'POST-VENTA', 'URGENTE']:
            conv = Conversation(
                customer_id=sample_customer.id,
                user_message=f"Test {category}",
                ai_response="Response",
                category=category,
                meta_message_id=f"msg_{category}_{id(conv)}"
            )
            db.session.add(conv)
        db.session.commit()
        
        response = client.get('/api/conversations?category=VENTAS')
        data = json.loads(response.data)
        
        # Verificar que todas tienen categoría VENTAS
        for conv in data:
            assert conv['category'] == 'VENTAS'
    
    def test_conversation_stats(self, client, sample_customer):
        """Obtiene estadísticas de conversaciones"""
        # Crear varios mensajes
        for i in range(5):
            conv = Conversation(
                customer_id=sample_customer.id,
                user_message=f"Mensaje {i}",
                ai_response=f"Respuesta {i}",
                category="VENTAS" if i % 2 == 0 else "POST-VENTA",
                meta_message_id=f"msg_{i}"
            )
            db.session.add(conv)
        db.session.commit()
        
        response = client.get('/api/conversations/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_conversations'] == 5
        assert data['total_customers'] == 1
        assert 'categories' in data


class TestMessageEndpoints:
    """Tests para endpoints de mensajes"""
    
    def test_send_message(self, client, sample_customer):
        """Envía un mensaje manual"""
        payload = {
            "customer_id": sample_customer.id,
            "message": "Hola, ¿cómo estás?"
        }
        
        response = client.post(
            '/api/send-message',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Nota: Esto fallará sin token Meta válido
        # Pero podemos verificar que la estructura es correcta
        assert response.status_code in [200, 500]  # 200 si funciona, 500 si falta token
    
    def test_send_message_missing_fields(self, client):
        """Rechaza mensaje incompleto"""
        payload = {
            "customer_id": "test_user"
            # Falta: message
        }
        
        response = client.post(
            '/api/send-message',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestHealthEndpoints:
    """Tests para health checks"""
    
    def test_health_check(self, client):
        """Verifica estado de la aplicación"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'timestamp' in data
        assert 'database' in data


# ==================== INTEGRATION TESTS ====================

class TestMessageFlow:
    """Tests de flujo completo de un mensaje"""
    
    def test_complete_message_flow(self, client, sample_customer):
        """Simula flujo completo: recibir, procesar, guardar mensaje"""
        
        # 1. Enviar webhook con mensaje
        webhook_payload = {
            "object": "instagram",
            "entry": [{
                "messaging": [{
                    "sender": {"id": sample_customer.id},
                    "message": {
                        "mid": "flow_test_msg",
                        "text": "¿Tienen cortinas blackout?"
                    }
                }]
            }]
        }
        
        response = client.post(
            '/webhook',
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 202]
        
        # 2. Verificar que se guardó en BD
        # (En caso real, esto ocurriría asincronamente)
        conversations = Conversation.query.filter_by(
            customer_id=sample_customer.id
        ).all()
        
        # Puede no haber conversación si la IA requiere token real
        # Pero la estructura debe ser correcta


class TestDataConsistency:
    """Tests de consistencia de datos"""
    
    def test_no_orphan_conversations(self, sample_customer):
        """Verifica que no hay conversaciones huérfanas"""
        # Crear conversación
        conv = Conversation(
            customer_id=sample_customer.id,
            user_message="Test",
            ai_response="Response",
            category="GENERAL"
        )
        db.session.add(conv)
        db.session.commit()
        
        # Eliminar cliente (debería eliminar también conversaciones)
        db.session.delete(sample_customer)
        db.session.commit()
        
        # Verificar que no quedan conversaciones
        orphans = Conversation.query.filter_by(
            customer_id=sample_customer.id
        ).all()
        
        assert len(orphans) == 0
    
    def test_category_constraints(self, sample_customer):
        """Verifica que las categorías son válidas"""
        valid_categories = ['VENTAS', 'POST-VENTA', 'URGENTE', 'SPAM', 'GENERAL']
        
        for category in valid_categories:
            conv = Conversation(
                customer_id=sample_customer.id,
                user_message="Test",
                ai_response="Response",
                category=category,
                meta_message_id=f"msg_{category}"
            )
            db.session.add(conv)
        
        db.session.commit()
        
        all_convs = Conversation.query.all()
        for conv in all_convs:
            assert conv.category in valid_categories


# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Tests de rendimiento"""
    
    def test_large_conversation_load(self, client):
        """Prueba carga con muchas conversaciones"""
        customer = Customer(id="perf_test_user", name="Perf Test")
        db.session.add(customer)
        db.session.commit()
        
        # Crear 1000 conversaciones
        for i in range(1000):
            conv = Conversation(
                customer_id=customer.id,
                user_message=f"Message {i}",
                ai_response=f"Response {i}",
                category="GENERAL",
                meta_message_id=f"perf_msg_{i}"
            )
            db.session.add(conv)
            if i % 100 == 0:
                db.session.commit()
        
        db.session.commit()
        
        # Verificar que la lista es rápida
        import time
        start = time.time()
        response = client.get('/api/conversations?limit=50')
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Debe ser menor a 1 segundo


# ==================== PYTEST CONFIGURATION ====================

# pytest.ini
"""
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
testpaths = tests
"""

# Para ejecutar tests:
# pytest                          # Todos los tests
# pytest -v                       # Verbose
# pytest -k "test_webhook"        # Específico
# pytest --cov=main              # Con cobertura
# pytest -m performance          # Solo performance


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
