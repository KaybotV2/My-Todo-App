from uuid import uuid4
from enum import Enum
import requests

ENDPOINT = "https://lnp5n7ywijpzmt7qegq3xfh7w40utqiq.lambda-url.us-east-1.on.aws/"

class TaskStatus(str, Enum):
    pending = "Pending"
    completed = "Completed"

def test_can_create_and_get_task():
    user_id = f"user_{uuid4().hex}"
    random_task_description = f"task description: {uuid4().hex}"
    create_response = create_task(user_id, random_task_description)
    assert create_response.status_code == 200

    task_id = create_response.json()["task"]["task_id"]
    get_response = get_task(task_id)
    assert get_response.status_code == 200

    task = get_response.json()
    assert task["user_id"] == user_id
    assert task["description"] == random_task_description


def test_can_list_tasks():
    # Create a new user for this test.
    user_id = f"user_{uuid4().hex}"

    # Create 3 tasks for this user.
    for i in range(3):
        create_task(user_id, f"task_{i}")

    # List the tasks for this user.
    response = list_tasks(user_id)
    tasks = response.json()["tasks"]
    assert len(tasks) == 3


def test_can_update_task():
    # Create a new user for this test.
    user_id = f"user_{uuid4().hex}"
    create_response = create_task(user_id, "task description")
    task_id = create_response.json()["task"]["task_id"]

    # Update the task with new content.
    new_task_content = f"updated task description: {uuid4().hex}"
    payload = {
        "description": new_task_content,
        "task_id": task_id,
        "is_done": TaskStatus.completed,  # Use the TaskStatus enum
    }
    update_task_response = update_task(payload)
    assert update_task_response.status_code == 200

    get_task_response = get_task(task_id)
    assert get_task_response.status_code == 200
    assert get_task_response.json()["description"] == new_task_content
    assert get_task_response.json()["is_done"] == TaskStatus.completed  # Check against the enum



def test_can_delete_task():
    user_id = f"user_{uuid4().hex}"
    create_response = create_task(user_id, "task1")
    task_id = create_response.json()["task"]["task_id"]

    # Delete the task.
    delete_task(task_id)

    # We shouldn't be able to get the task anymore.
    get_task_response = get_task(task_id)
    assert get_task_response.status_code == 404


def list_tasks(user_id: str) -> dict:
    return requests.get(f"{ENDPOINT}/list-tasks/{user_id}")


def create_task(user_id: str, description: str) -> dict:    
    payload = {
        "user_id": user_id,
        "description": description,
    }
    return requests.put(f"{ENDPOINT}/create-task", json=payload)


def get_task(task_id: str) -> dict:
    return requests.get(f"{ENDPOINT}/get-task/{task_id}")  


def delete_task(task_id: str) -> dict:
    return requests.delete(f"{ENDPOINT}/delete-task/{task_id}")


def update_task(payload: dict) -> dict:
    return requests.put(f"{ENDPOINT}/update-task", json=payload)

