from fastapi import FastAPI, HTTPException, Body
from models import Function, engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from docker_engine.runner import run_in_docker

# Add Pydantic model for request body validation
class FunctionCreate(BaseModel):
    name: str
    language: str
    code: str
    timeout: int = 5

Session = sessionmaker(bind=engine)
app = FastAPI()

# Updated to use JSON body
@app.post("/functions")
async def upload_function(function_data: FunctionCreate):
    session = Session()
    func = Function(
        name=function_data.name,
        language=function_data.language,
        code=function_data.code,
        timeout=function_data.timeout
    )
    session.add(func)
    session.commit()
    return {"id": func.id, "message": "Function uploaded"}

# No changes needed to this endpoint
@app.post("/functions/{func_id}/execute")
async def execute_function(func_id: int, input_data: dict):
    session = Session()
    func = session.query(Function).filter_by(id=func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    
    result = await run_in_docker(func.code, func.language, input_data, func.timeout)
    return {"result": result}