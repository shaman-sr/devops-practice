import time

from fastapi import FastAPI, HTTPException, Depends
import requests
from model import Hero
from contextlib import asynccontextmanager
from sqlmodel import Session, select, SQLModel
from db import get_session, engine
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    for attempt in range(5):
        try:
            logger.info("Creating database tables")
            SQLModel.metadata.create_all(engine)
            logger.info("Tables created successfully")
            break
        except Exception as e:
            logger.error(f"DB not ready, retrying... ({attempt+1}/5): {e}")
            time.sleep(2)
    else:
        logger.error("Could not connect to DB after retries")

    yield  

app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return "Server running"

@app.get("/data")
def get_data():
    url = "https://jsonplaceholder.typicode.com/posts"
    
    response = requests.get(url=url)
    
    posts = response.json()
    
    for post in posts:
        user_id = post["userId"]
        
        print(user_id)
    
    return posts

@app.post("/hero")
def create_hero(hero: Hero, session: Session = Depends(get_session)):
    try:
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return {"Hero created successfully": hero}
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating new hero: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create hero"
        )
            

@app.get("/hero")
def get_all_hero(session: Session = Depends(get_session)):
    try: 
        statement = select(Hero)
        heros = session.exec(statement).all()
        return heros
    
    except Exception as e:
        logger.error(f"Error fecthing user: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
        
@app.put("/hero/{name}")
def update_hero(name: str, updatedHero: Hero, session: Session=Depends(get_session)):
    try:
        statement = select(Hero).where(Hero.name == name)
        hero = session.exec(statement).first()
        
        if not hero:
            raise HTTPException(
                status_code=400,
                detail="Hero not found"
            )
        
        hero.name = updatedHero.name
        hero.secret_name = updatedHero.secret_name
        hero.age = updatedHero.age
        
        session.add(hero)
        session.commit()
        session.refresh(hero)
        
        return hero
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating hero by name {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.delete("/hero/{name}")
def delete_hero(name: str, session: Session=Depends(get_session)):
    try:
        statement = select(Hero).where(Hero.name == name)
        hero = session.exec(statement).first()
        
        if not hero:
            raise HTTPException(
                status_code=400,
                detail="Hero not found"
            )
        
        session.delete(hero)
        session.commit()
        session.refresh(hero)
        
        return hero
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting user {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )