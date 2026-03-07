from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid 

app = FastAPI(title="todo api")

todos: dict[str, dict] = {}

class TodoCreate(BaseModel):
    title: str 
    description: Optional[str] = None 

class TodoUpdate(BaseModel):
    title: Optional[str] = None 
    description: Optional[str] = None 
    completed: Optional[bool] = None 
    
@app.get("/todos")
def get_all():
    return list(todos.values())

@app.post("/todos", status_code=201)
def create(todo: TodoCreate):
    id = str(uuid.uuid4())
    todos[id] = {"id": id, "title": todo.title, "description": todo.description, "completed": False}
    return todos[id]

@app.get("/todos/{id}")
def get_one(id: str): 
    if id not in todos: 
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos[id]

@app.patch("/todos/{id}")
def update(id: str, data: TodoUpdate): 
    if id not in todos:
        raise HTTPException(status_code=404, detail="todo not found")
    todos[id].update({k: v for k, v in data.model_dump().items() if v is not None})
    return todos[id]

@app.delete("/todos/{id}")
def delete(id: str):
    if id not in todos: 
        raise HTTPException(status_code=404, detail="Todo not found")
    del todos[id]

