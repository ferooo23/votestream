# app/main.py

import json
from fastapi import FastAPI, WebSocket, Depends, HTTPException, Query, status
from sqlmodel import SQLModel, Session, select, create_engine
from sqlalchemy import func
from sqlalchemy.orm import selectinload
import redis as redis_py
from typing import Optional, List
from datetime import datetime

from models import Poll, Option, Vote

DATABASE_URL = "postgresql://postgres:pass@db:5432/votes"
REDIS_URL = "redis://redis:6379/0"

engine = create_engine(DATABASE_URL, echo=True)
redis_client = redis_py.from_url(REDIS_URL, decode_responses=True)

SQLModel.metadata.create_all(engine)

app = FastAPI(title="Vote Stream")

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/health")
def health():
    return {"status": "ok"}

# 1) Listar todas las encuestas
@app.get("/polls", response_model=list[Poll])
def list_polls(
    session: Session = Depends(get_session),
    active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    query = select(Poll)
    if active is not None:
        query = query.where(Poll.active == active)
    return session.exec(query.offset(skip).limit(limit)).all()

# 2) Leer una encuesta concreta (sin votos)
@app.get("/polls/{poll_id}", response_model=Poll)
def read_poll(poll_id: int, session: Session = Depends(get_session)):
    poll = session.exec(
        select(Poll)
        .options(selectinload(Poll.options))
        .where(Poll.id == poll_id)
    ).one_or_none()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll

# 3) Resultados agregados
@app.get("/polls/{poll_id}/results")
def results(poll_id: int, session: Session = Depends(get_session)):
    stmt = (
        select(Option.text, func.count(Vote.id))
        .join(Vote, Vote.option_id == Option.id)
        .where(Vote.poll_id == poll_id)
        .group_by(Option.id)
    )
    rows = session.exec(stmt).all()
    return {text: count for text, count in rows}

# 4) Votar y publicar por Redis
@app.post("/polls/{poll_id}/vote")
def vote(poll_id: int, payload: dict, session: Session = Depends(get_session)):
    choice_idx = payload.get("choice")
    poll = session.get(Poll, poll_id)
    if not poll or choice_idx not in range(len(poll.options)):
        raise HTTPException(status_code=400, detail="Invalid poll or choice")
    option = poll.options[choice_idx]

    vote = Vote(poll_id=poll_id, option_id=option.id)
    session.add(vote)
    session.commit()

    # recalcular y publicar
    res = results(poll_id, session)
    redis_client.publish(f"poll_{poll_id}", json.dumps(res))

    return {"status": "ok"}

# 5) WebSocket en tiempo real
@app.websocket("/polls/{poll_id}/stream")
async def stream(ws: WebSocket, poll_id: int):
    await ws.accept()
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"poll_{poll_id}")
    for message in pubsub.listen():
        if message["type"] == "message":
            await ws.send_text(message["data"])

# 6) Crear nueva encuesta
@app.post("/polls", response_model=Poll, status_code=status.HTTP_201_CREATED)
def create_poll(poll: Poll, session: Session = Depends(get_session)):
    session.add(poll)
    session.commit()
    session.refresh(poll)
    return poll

# 7) Actualizar encuesta
@app.put("/polls/{poll_id}", response_model=Poll)
def update_poll(poll_id: int, poll_data: dict, session: Session = Depends(get_session)):
    poll = session.get(Poll, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    for key, value in poll_data.items():
        if hasattr(poll, key):
            setattr(poll, key, value)
    
    session.add(poll)
    session.commit()
    session.refresh(poll)
    return poll

# 8) Añadir opciones a una encuesta existente
@app.post("/polls/{poll_id}/options", response_model=Option)
def add_option(poll_id: int, option: Option, session: Session = Depends(get_session)):
    poll = session.get(Poll, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    option.poll_id = poll_id
    session.add(option)
    session.commit()
    session.refresh(option)
    return option

# 9) Eliminar encuesta
@app.delete("/polls/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poll(poll_id: int, session: Session = Depends(get_session)):
    poll = session.get(Poll, poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    session.delete(poll)
    session.commit()
    return None

# 10) Estadísticas generales
@app.get("/stats")
def get_stats(session: Session = Depends(get_session)):
    total_polls = session.exec(select(func.count(Poll.id))).one()
    total_votes = session.exec(select(func.count(Vote.id))).one()
    polls_with_votes = session.exec(
        select(func.count(func.distinct(Vote.poll_id)))
    ).one()
    
    return {
        "total_polls": total_polls,
        "total_votes": total_votes,
        "polls_with_votes": polls_with_votes
    }
