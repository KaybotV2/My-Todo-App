import os
import time
import boto3
from typing import Optional
from enum import Enum
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel
from boto3.dynamodb.conditions import Key

app = FastAPI()
handler = Mangum(app)


# Define the possible task statuses
class TaskStatus(str, Enum):
    pending = "Pending"
    completed = "Completed"

class PutTaskRequest(BaseModel):
    description: str  # Task description
    is_done: TaskStatus = TaskStatus.pending  # Default is_done is "Pending"
    user_id: Optional[str] = None  # Optional user ID
    task_id: Optional[str] = None  # Optional task ID

class TaskResponse(BaseModel):
    task_id: str
    description: str
    is_done: TaskStatus
    created_time: int
    user_id: Optional[str]    


@app.get("/")
async def root():
    return {"message": "Hello from ToDo API!"}


@app.put("/create-task")
async def create_task(put_task_request: PutTaskRequest):
    created_time = int(time.time())
    item = {
        "user_id": put_task_request.user_id,
        "description": put_task_request.description,
        "is_done": put_task_request.is_done.value,
        "created_time": created_time,
        "task_id": f"task_{uuid4().hex}",
    }

    # Put it into the table.
    table = _get_table()
    table.put_item(Item=item)
    return {"task": item}


@app.get("/get-task/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    # Get the task from the table.
    table = _get_table()
    response = table.get_item(Key={"task_id": task_id})
    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Ensure is_done is present for older tasks
    item["is_done"] = item.get("is_done", TaskStatus.pending.value)
    return item


@app.get("/list-tasks/{user_id}")
async def list_tasks(user_id: str):
    # Get the task from the table.
    table = _get_table()
    response = table.query(
        IndexName="user-index",
        KeyConditionExpression=Key("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=10,
    )
    tasks = response.get("Items")
    return {"tasks": tasks}



@app.put("/update-task")
async def update_task(put_task_request: PutTaskRequest):
    try:
        # Ensure task_id is provided
        if not put_task_request.task_id:
            raise HTTPException(status_code=400, detail="Task ID is required for updating a task.")

        # Update the task in the table.
        table = _get_table()

        # Use ExpressionAttributeNames to avoid reserved keyword issue
        response = table.update_item(
            Key={"task_id": put_task_request.task_id},
            UpdateExpression="SET description = :description, is_done = :is_done",
            ExpressionAttributeValues={
                ":description": put_task_request.description,
                ":is_done": put_task_request.is_done.value  
            },
            ReturnValues="ALL_NEW",
        )
        return {"updated_task_id": put_task_request.task_id, "response": response}

    except Exception as e:
        # Log the error and return an appropriate message
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



@app.delete("/delete-task/{task_id}")
async def delete_task(task_id: str):
    # Delete the task from the table.
    table = _get_table()
    table.delete_item(Key={"task_id": task_id})
    return {"deleted_task_id": task_id}


def _get_table():
    table_name = os.environ.get("TABLE_NAME")
    if not table_name:
        raise ValueError("TABLE_NAME environment variable is not set.")
    return boto3.resource("dynamodb").Table(table_name)


