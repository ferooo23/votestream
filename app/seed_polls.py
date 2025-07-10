# app/seed_polls.py

from sqlmodel import SQLModel, Session, select, create_engine
import datetime
import os
import logging
import random
import json
from models import Poll, Option, Vote

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Use environment variables or default values for the connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:pass@db:5432/votes")
engine = create_engine(DATABASE_URL)

def init_db():
    """Initialize the database by creating all tables"""
    logging.info("Initializing database tables")
    SQLModel.metadata.create_all(engine)

def seed():
    """Seed the database with themed polls, clearing existing ones first"""
    # Organized themes and polls
    themes = {
        "OnTrend": {
            "name": "#OnTrend",
            "slug": "on-trend", 
            "description": "The hottest topics of the moment. From technology and social media to the latest releases everyone's talking about. Vote and discover if you think like the majority!",
            "polls": [
                (
                    "What will be the next 'big social network' to dominate the market?",
                    ["A generative AI app", "A decentralized micro-video platform", "The resurgence of niche forums", "None, the market is saturated"]
                ),
                (
                    "Looking at the future of work, what's your ideal model?",
                    ["100% Remote, with total freedom", "Flexible hybrid (go to office when I want)", "Structured hybrid (fixed office days)", "100% In-person, the office is key"]
                ),
                (
                    "With so many cinematic universes, what do you prefer for the future of superhero movies?",
                    ["Complete reboots with new actors", "Smaller, more personal stories", "Fewer movies, but higher quality", "More massive crossovers between franchises!"]
                )
            ]
        },
        "MoralDilemmas": {
            "name": "Moral Dilemmas",
            "slug": "moral-dilemmas",
            "description": "Difficult questions with no right answer. Test your principles and discover how the world would react to these extreme situations.",
            "polls": [
                (
                    "An autonomous car with no brakes is about to hit 5 pedestrians. You can divert the car to hit only its single passenger. What should the car do?",
                    ["Save the 5 pedestrians", "Save the passenger", "The decision should be random", "It's impossible to program that morality"]
                ),
                (
                    "Would you give up part of your online privacy to ensure greater public safety and prevent serious crimes?",
                    ["Yes, security is a priority", "Only under strict judicial supervision", "No, privacy is an unbreakable right", "I'm not sure"]
                ),
                (
                    "If you could know a painful truth about your future, would you rather know it or live happily in ignorance?",
                    ["I want to know the truth, no matter the cost", "I prefer the happiness of ignorance", "It would depend on the type of truth", "Only if I can do something to change it"]
                )
            ]
        },
        "Sports": {
            "name": "⚽ Sports",
            "slug": "sports",
            "description": "The boldest predictions from the world of sports. Will you nail your forecasts?",
            "polls": [
                (
                    "Will Spain win the next World Cup?",
                    ["Yes", "No"]
                ),
                (
                    "Next winner of La Liga?",
                    ["Real Madrid", "FC Barcelona", "Atlético Madrid", "Another team"]
                ),
                (
                    "Next Ballon d'Or winner?",
                    ["Lamine Yamal", "Kylian Mbappé", "Ousmane Dembélé", "Another player"]
                )
            ]
        }
    }
    
    with Session(engine) as session:
        # Clear existing polls
        logging.info("Clearing all existing polls...")
        existing_polls = session.exec(select(Poll)).all()
        for poll in existing_polls:
            session.delete(poll)
        session.commit()
        logging.info(f"Cleared {len(existing_polls)} existing polls")
        
        # Create new polls by theme
        for theme_key, theme_data in themes.items():
            logging.info(f"Creating polls for theme: {theme_data['name']}")
            
            for question, opts in theme_data["polls"]:
                # Create new poll
                logging.info(f"Creating poll: {question}")
                p = Poll(
                    question=question,
                    theme=theme_key,  # Assign theme
                    created_at=datetime.datetime.utcnow(),
                )
                # Add options
                p.options = [Option(text=o) for o in opts]
                session.add(p)

        session.commit()
        
        # Generate random votes so there are statistics from the beginning
        logging.info("Generating random votes for statistics...")
        polls = session.exec(select(Poll)).all()
        
        for poll in polls:
            # Generate between 50 and 200 random votes per poll
            num_votes = random.randint(50, 200)
            
            for _ in range(num_votes):
                # Select random option
                random_option = random.choice(poll.options)
                
                # Create vote
                vote = Vote(
                    poll_id=poll.id,
                    option_id=random_option.id,
                    user_id=random.randint(1000, 9999),  # Fictitious user ID
                    voted_at=datetime.datetime.utcnow() - datetime.timedelta(
                        minutes=random.randint(0, 60*24*7)  # Votes in the last week
                    )
                )
                session.add(vote)
        
        session.commit()
        logging.info("All themed polls created successfully with random votes")

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
    topics = ["Economy", "Environment", "Politics", "Education", "Health", "Technology"]
    
    with Session(engine) as session:
        for i in range(count):
            topic = random.choice(topics)
            question = f"Random question about {topic} #{i+1}?"
            options = [f"Option {j+1}" for j in range(random.randint(2, 5))]
            
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
