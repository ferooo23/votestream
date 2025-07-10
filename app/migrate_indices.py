#!/usr/bin/env python3
"""
Script para migrar índices en la base de datos existente
"""

import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres:pass@db:5432/votes"

def create_indices():
    """Create indices to optimize performance"""
    engine = create_engine(DATABASE_URL)
    
    indices = [
        # Índices para la tabla vote
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vote_poll_id ON vote(poll_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vote_option_id ON vote(option_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vote_poll_option ON vote(poll_id, option_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vote_voted_at ON vote(voted_at);",
        
        # Índices para la tabla poll
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poll_is_active ON poll(is_active);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poll_created_at ON poll(created_at);",
        
        # Índices para la tabla de enlaces
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poll_option_poll_id ON polloption(poll_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poll_option_option_id ON polloption(option_id);",
    ]
    
    with engine.connect() as conn:
        for idx_sql in indices:
            try:
                logger.info(f"Creando índice: {idx_sql}")
                conn.execute(text(idx_sql))
                conn.commit()
                logger.info("✓ Índice creado exitosamente")
            except Exception as e:
                logger.warning(f"Error creando índice (puede que ya exista): {e}")
                continue

if __name__ == "__main__":
    try:
        create_indices()
        logger.info("✓ Index migration completed")
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        sys.exit(1)
