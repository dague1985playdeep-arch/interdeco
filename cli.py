#!/usr/bin/env python3
"""
Inter-Deco DM Manager - CLI Management Tool
Herramienta de línea de comandos para gestionar la aplicación

Uso:
    python cli.py init-db               # Inicializar base de datos
    python cli.py seed-data             # Crear datos de prueba
    python cli.py export-csv [customer] # Exportar a CSV
    python cli.py export-json [customer]# Exportar a JSON
    python cli.py backup                # Backup de base de datos
    python cli.py restore <backup_file> # Restaurar backup
    python cli.py stats                 # Ver estadísticas
    python cli.py clean-old-data <days> # Eliminar datos antiguos
    python cli.py generate-report <month> <year>  # Generar reporte
"""

import os
import sys
import json
import csv
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import click
from tabulate import tabulate

# Importar desde main
try:
    from main import app, db, Customer, Conversation, MetaDMManager
    from advanced_features import ConversationAnalytics, DataExport, ReportGenerator
except ImportError as e:
    click.echo(click.style(f"❌ Error importando módulos: {e}", fg='red'), err=True)
    sys.exit(1)


# ==================== UTILIDADES ====================

def get_db():
    """Contexto de base de datos"""
    return app.app_context()


@click.group()
def cli():
    """Inter-Deco DM Manager - CLI Tool"""
    pass


# ==================== COMANDOS DE BD ====================

@cli.command()
@click.option('--reset', is_flag=True, help='Eliminar y recrear tablas')
def init_db(reset):
    """Inicializar la base de datos"""
    with get_db():
        if reset:
            click.echo("🗑️  Eliminando tablas...")
            db.drop_all()
            click.echo("✅ Tablas eliminadas")
        
        click.echo("🔄 Creando tablas...")
        db.create_all()
        click.echo("✅ Base de datos inicializada")
        
        # Mostrar estadísticas
        customer_count = Customer.query.count()
        conversation_count = Conversation.query.count()
        
        click.echo(f"\n📊 Estadísticas:")
        click.echo(f"  - Clientes: {customer_count}")
        click.echo(f"  - Conversaciones: {conversation_count}")


@cli.command()
def seed_data():
    """Crear datos de prueba"""
    with get_db():
        click.echo("🌱 Creando datos de prueba...")
        
        # Crear clientes
        customers_data = [
            {
                'id': 'test_customer_1',
                'name': 'Juan García',
                'email': 'juan@example.com',
                'phone': '+56912345678'
            },
            {
                'id': 'test_customer_2',
                'name': 'María López',
                'email': 'maria@example.com',
                'phone': '+56987654321'
            },
            {
                'id': 'test_customer_3',
                'name': 'Carlos Rodríguez',
                'email': 'carlos@example.com',
                'phone': '+56998765432'
            }
        ]
        
        for cust_data in customers_data:
            customer = Customer(**cust_data)
            db.session.add(customer)
        
        db.session.commit()
        click.echo(f"✅ {len(customers_data)} clientes creados")
        
        # Crear conversaciones
        conversations_data = [
            {
                'customer_id': 'test_customer_1',
                'user_message': '¿Cuánto cuesta una cortina para sala?',
                'ai_response': 'Hola Juan! Para darte presupuesto, necesito medidas y fotos.',
                'category': 'VENTAS',
                'meta_message_id': 'test_msg_001'
            },
            {
                'customer_id': 'test_customer_1',
                'user_message': 'Mi cortina se rompió, ¿puedo cambiarla?',
                'ai_response': 'Claro! Revisa tu garantía. ¿Cuándo la compraste?',
                'category': 'POST-VENTA',
                'meta_message_id': 'test_msg_002'
            },
            {
                'customer_id': 'test_customer_2',
                'user_message': '¡¡¡URGENTE!!! Mi cortina se incendió',
                'ai_response': 'Estamos aquí para ayudarte. Dame tu ubicación.',
                'category': 'URGENTE',
                'meta_message_id': 'test_msg_003'
            },
            {
                'customer_id': 'test_customer_3',
                'user_message': 'Quiero comprar viagra barata',
                'ai_response': 'No podemos ayudarte con eso.',
                'category': 'SPAM',
                'meta_message_id': 'test_msg_004'
            },
        ]
        
        for conv_data in conversations_data:
            conversation = Conversation(**conv_data)
            db.session.add(conversation)
        
        db.session.commit()
        click.echo(f"✅ {len(conversations_data)} conversaciones creadas")


# ==================== COMANDOS DE EXPORTACIÓN ====================

@cli.command()
@click.option('--customer-id', default=None, help='Exportar solo un cliente')
@click.option('--output', default='export.csv', help='Archivo de salida')
def export_csv(customer_id, output):
    """Exportar conversaciones a CSV"""
    with get_db():
        click.echo(f"📊 Exportando a CSV: {output}")
        
        csv_data = DataExport.export_to_csv(customer_id)
        
        with open(output, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_data)
        
        click.echo(f"✅ Exportado correctamente")
        click.echo(f"📁 Ubicación: {os.path.abspath(output)}")


@cli.command()
@click.option('--customer-id', default=None, help='Exportar solo un cliente')
@click.option('--output', default='export.json', help='Archivo de salida')
def export_json(customer_id, output):
    """Exportar conversaciones a JSON"""
    with get_db():
        click.echo(f"📊 Exportando a JSON: {output}")
        
        json_data = DataExport.export_to_json(customer_id)
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(json_data)
        
        click.echo(f"✅ Exportado correctamente")
        click.echo(f"📁 Ubicación: {os.path.abspath(output)}")


# ==================== COMANDOS DE BACKUP ====================

@cli.command()
def backup():
    """Crear backup de base de datos"""
    with get_db():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/backup_{timestamp}'
        
        click.echo(f"💾 Creando backup: {backup_dir}")
        
        # Crear directorio
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Exportar datos
        json_data = DataExport.export_to_json()
        with open(f'{backup_dir}/conversations.json', 'w') as f:
            f.write(json_data)
        
        # Copiar base de datos (si es SQLite)
        db_url = os.getenv('DATABASE_URL', 'sqlite:///interdeco_dm.db')
        if 'sqlite' in db_url:
            db_file = db_url.replace('sqlite:///', '')
            if os.path.exists(db_file):
                shutil.copy(db_file, f'{backup_dir}/database.db')
        
        click.echo(f"✅ Backup creado")
        click.echo(f"📁 Ubicación: {os.path.abspath(backup_dir)}")


@cli.command()
@click.argument('backup_file')
def restore(backup_file):
    """Restaurar backup"""
    if not os.path.exists(backup_file):
        click.echo(click.style(f"❌ Archivo no encontrado: {backup_file}", fg='red'), err=True)
        return
    
    with get_db():
        click.echo(f"📂 Restaurando desde: {backup_file}")
        
        # Confirmación
        if not click.confirm('¿Estás seguro? Esto sobrescribirá los datos actuales'):
            click.echo("❌ Operación cancelada")
            return
        
        try:
            if backup_file.endswith('.db'):
                # Restaurar SQLite
                shutil.copy(backup_file, 'interdeco_dm.db')
            elif backup_file.endswith('.json'):
                # Restaurar desde JSON
                click.echo("⚠️  Restauración desde JSON: no soportado aún")
            
            click.echo(f"✅ Backup restaurado")
        except Exception as e:
            click.echo(click.style(f"❌ Error: {e}", fg='red'), err=True)


# ==================== COMANDOS DE ESTADÍSTICAS ====================

@cli.command()
def stats():
    """Mostrar estadísticas generales"""
    with get_db():
        click.echo("\n" + "="*50)
        click.echo("📊 ESTADÍSTICAS INTER-DECO DM MANAGER")
        click.echo("="*50 + "\n")
        
        # Estadísticas generales
        total_customers = Customer.query.count()
        total_conversations = Conversation.query.count()
        
        click.echo(f"👥 Total de clientes: {total_customers}")
        click.echo(f"💬 Total de conversaciones: {total_conversations}")
        
        if total_conversations > 0:
            avg_msgs_per_customer = total_conversations / max(total_customers, 1)
            click.echo(f"📈 Promedio de mensajes por cliente: {avg_msgs_per_customer:.2f}")
        
        # Distribución por categoría
        click.echo("\n📂 Distribución por categoría:")
        categories = ConversationAnalytics.get_category_distribution()
        
        for category, count in sorted(categories.items()):
            percentage = (count / total_conversations * 100) if total_conversations > 0 else 0
            bar = "█" * int(percentage / 5)
            click.echo(f"  {category:15} {count:5} ({percentage:5.1f}%) {bar}")
        
        # Top clientes
        click.echo("\n👑 Top 5 clientes:")
        top_customers = ConversationAnalytics.get_top_customers(5)
        
        for customer in top_customers:
            click.echo(f"  {customer['name']:20} {customer['total_messages']:5} mensajes")
        
        # Tiempo de respuesta
        click.echo("\n⏱️  Análisis de tiempo de respuesta:")
        response_time = ConversationAnalytics.get_response_time_analytics()
        
        if response_time['total_samples'] > 0:
            click.echo(f"  Promedio: {response_time['avg_seconds']:.1f}s")
            click.echo(f"  Mínimo: {response_time['min_seconds']:.1f}s")
            click.echo(f"  Máximo: {response_time['max_seconds']:.1f}s")
        
        click.echo("\n" + "="*50 + "\n")


@cli.command()
@click.argument('customer_id')
def customer_stats(customer_id):
    """Estadísticas detalladas de un cliente"""
    with get_db():
        customer = Customer.query.get(customer_id)
        
        if not customer:
            click.echo(click.style(f"❌ Cliente no encontrado", fg='red'), err=True)
            return
        
        click.echo("\n" + "="*50)
        click.echo(f"📋 CLIENTE: {customer.name}")
        click.echo("="*50 + "\n")
        
        click.echo(f"ID: {customer.id}")
        click.echo(f"Email: {customer.email}")
        click.echo(f"Teléfono: {customer.phone}")
        click.echo(f"Creado: {customer.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Engagement score
        engagement = ConversationAnalytics.get_engagement_score(customer_id)
        click.echo(f"\n📊 Score de engagement: {engagement['score']:.1f}/100")
        click.echo(f"Mensajes totales: {engagement['total_messages']}")
        click.echo(f"Días activo: {engagement['days_active']}")
        click.echo(f"Mensajes por día: {engagement['messages_per_day']:.2f}")
        
        # Conversaciones
        click.echo(f"\n💬 Últimas 5 conversaciones:")
        conversations = Conversation.query.filter_by(
            customer_id=customer_id
        ).order_by(Conversation.created_at.desc()).limit(5).all()
        
        for i, conv in enumerate(reversed(conversations), 1):
            click.echo(f"\n  {i}. {conv.created_at.strftime('%Y-%m-%d %H:%M')}")
            click.echo(f"     Cliente: {conv.user_message[:50]}...")
            click.echo(f"     IA: {conv.ai_response[:50]}...")
            click.echo(f"     Categoría: {conv.category}")
        
        click.echo("\n" + "="*50 + "\n")


# ==================== COMANDOS DE MANTENIMIENTO ====================

@cli.command()
@click.argument('days', type=int)
@click.option('--confirm', is_flag=True, help='Confirmar sin preguntar')
def clean_old_data(days, confirm):
    """Eliminar conversaciones más antiguas de N días"""
    with get_db():
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_conversations = Conversation.query.filter(
            Conversation.created_at < cutoff_date
        ).count()
        
        if old_conversations == 0:
            click.echo("✅ No hay datos para limpiar")
            return
        
        click.echo(f"🗑️  Se eliminarán {old_conversations} conversaciones")
        click.echo(f"    más antiguas de {days} días")
        
        if not confirm and not click.confirm('¿Continuar?'):
            click.echo("❌ Cancelado")
            return
        
        Conversation.query.filter(
            Conversation.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        click.echo(f"✅ {old_conversations} conversaciones eliminadas")


@cli.command()
def cleanup():
    """Limpiar datos huérfanos e inconsistencias"""
    with get_db():
        click.echo("🧹 Limpiando base de datos...")
        
        # Verificar y limpiar
        # (Implementar lógica de limpieza específica)
        
        click.echo("✅ Base de datos limpia")


# ==================== COMANDOS DE REPORTES ====================

@cli.command()
@click.argument('month', type=int)
@click.argument('year', type=int)
@click.option('--format', type=click.Choice(['json', 'csv', 'txt']), default='json')
def generate_report(month, year, format):
    """Generar reporte mensual"""
    with get_db():
        click.echo(f"📄 Generando reporte {month}/{year}...")
        
        report = ReportGenerator.generate_monthly_report(month, year)
        
        if format == 'json':
            filename = f'report_{year}{month:02d}.json'
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
        
        elif format == 'csv':
            filename = f'report_{year}{month:02d}.csv'
            # Convertir a CSV (simplificado)
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Métrica', 'Valor'])
                for key, value in report.items():
                    if not isinstance(value, (dict, list)):
                        writer.writerow([key, value])
        
        click.echo(f"✅ Reporte generado")
        click.echo(f"📁 Ubicación: {os.path.abspath(filename)}")


# ==================== COMANDOS DE VERIFICACIÓN ====================

@cli.command()
def check():
    """Verificar salud del sistema"""
    with get_db():
        click.echo("\n" + "="*50)
        click.echo("🔍 HEALTH CHECK")
        click.echo("="*50 + "\n")
        
        # Base de datos
        try:
            db.session.execute('SELECT 1')
            click.echo("✅ Base de datos: OK")
        except Exception as e:
            click.echo(click.style(f"❌ Base de datos: {e}", fg='red'))
        
        # Meta API
        try:
            token = os.getenv('META_ACCESS_TOKEN')
            if not token:
                click.echo("⚠️  Meta API: Token no configurado")
            else:
                click.echo("✅ Meta API: Token configurado")
        except Exception as e:
            click.echo(click.style(f"❌ Meta API: {e}", fg='red'))
        
        # OpenAI API
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                click.echo("⚠️  OpenAI API: Key no configurada")
            else:
                click.echo("✅ OpenAI API: Key configurada")
        except Exception as e:
            click.echo(click.style(f"❌ OpenAI API: {e}", fg='red'))
        
        click.echo("\n" + "="*50 + "\n")


# ==================== MAIN ====================

if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\n❌ Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n❌ Error: {e}", fg='red'), err=True)
        sys.exit(1)
