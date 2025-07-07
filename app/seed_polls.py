# app/seed_polls.py

from sqlmodel import SQLModel, Session, select, create_engine
import datetime
import os
import logging
import random
import json
from models import Poll, Option

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Usar variables de entorno o valores por defecto para la conexión
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:pass@db:5432/votes")
engine = create_engine(DATABASE_URL)

def init_db():
    """Initialize the database by creating all tables"""
    logging.info("Initializing database tables")
    SQLModel.metadata.create_all(engine)

def seed():
    """Seed the database with initial polls if they don't exist"""
    # Categorías de encuestas
    polls = [
        (
            "¿Adelantarías a 2030 la prohibición de coches de combustión en la UE?",
            ["Sí", "No", "Solo para vehículos privados", "Necesitamos más tiempo"]
        ),
        (
            "¿Apoyas la semana laboral de 4 días en toda la UE?",
            ["Sí", "No", "Solo en ciertos sectores", "Depende de las condiciones"]
        ),
        (
            "¿Cuál es la prioridad más importante para la UE?",
            ["Cambio climático", "Migración", "Seguridad", "Economía", "Derechos sociales"]
        ),
        (
            "¿Debería la UE tener un ejército común?",
            ["Sí", "No", "Solo para operaciones específicas", "Ampliar OTAN en su lugar"]
        ),
        (
            "¿Qué política energética prefieres para la UE?",
            ["100% renovables", "Nuclear + renovables", "Diversificación de fuentes", "Autonomía energética"]
        )
    ]
    
    with Session(engine) as session:
        for question, opts in polls:
            # Evitar duplicados
            exists = session.exec(
                select(Poll).where(Poll.question == question)
            ).first()
            
            if exists:
                logging.info(f"Poll already exists: {question}")
                continue

            # Crear nueva encuesta
            logging.info(f"Creating new poll: {question}")
            p = Poll(
                question=question,
                created_at=datetime.datetime.utcnow(),
            )
            # Añadir opciones
            p.options = [Option(text=o) for o in opts]
            session.add(p)

        session.commit()

def clear_polls():
    """Remove all polls from the database"""
    with Session(engine) as session:
        polls = session.exec(select(Poll)).all()
        for poll in polls:
            session.delete(poll)
        session.commit()
        logging.info(f"Removed {len(polls)} polls from database")

def generate_random_polls(count=5):
    """Generate random polls for testing purposes"""
    topics = ["Economía", "Medio Ambiente", "Política", "Educación", "Sanidad", "Tecnología"]
    
    with Session(engine) as session:
        for i in range(count):
            topic = random.choice(topics)
            question = f"¿Pregunta aleatoria sobre {topic} #{i+1}?"
            options = [f"Opción {j+1}" for j in range(random.randint(2, 5))]
            
            p = Poll(
                question=question,
                created_at=datetime.datetime.utcnow(),
            )
            p.options = [Option(text=o) for o in options]
            session.add(p)
            
        session.commit()
        logging.info(f"Generated {count} random polls")

def export_polls(filename="polls_backup.json"):
    """Export all polls to a JSON file"""
    with Session(engine) as session:
        polls = session.exec(select(Poll)).all()
        data = []
        
        for poll in polls:
            poll_data = {
                "question": poll.question,
                "created_at": poll.created_at.isoformat(),
                "options": [option.text for option in poll.options]
            }
            data.append(poll_data)
            
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        logging.info(f"Exported {len(data)} polls to {filename}")
        return data

def import_polls(filename="polls_backup.json"):
    """Import polls from a JSON file"""
    try:
        with open(filename, 'r') as f:
            polls_data = json.load(f)
            
        with Session(engine) as session:
            imported = 0
            for poll_data in polls_data:
                # Check if poll already exists
                exists = session.exec(
                    select(Poll).where(Poll.question == poll_data["question"])
                ).first()
                
                if not exists:
                    p = Poll(
                        question=poll_data["question"],
                        created_at=datetime.datetime.fromisoformat(poll_data["created_at"])
                    )
                    p.options = [Option(text=o) for o in poll_data["options"]]
                    session.add(p)
                    imported += 1
                    
            session.commit()
            logging.info(f"Imported {imported} polls from {filename}")
            
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in file: {filename}")

if __name__ == "__main__":
    init_db()
    seed()
