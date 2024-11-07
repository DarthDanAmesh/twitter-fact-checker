import asyncio
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from dotenv import dotenv_values
from pydantic import BaseModel
from typing import List, Optional
import pprint
from ollama import AsyncClient
from fastapi.staticfiles import StaticFiles
import datetime

#Local dev usage: fastapi dev chat.py

# Initialize the Llama model locally
llm = AsyncClient()

app = FastAPI()

class SimplaText(BaseModel):
    id: Optional[int] = None
    url: str
    txt: str

summaries = []
clients = set()

app.mount("/static", StaticFiles(directory="static"), name="static")

html = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Chattie</title>
    <link rel="stylesheet" href="/static/styles.css" />
    <!-- Credit: Scaler https://www.scaler.com/topics/chat-interface-project-css/ --> 
    <!-- Import this CDN to use icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.9.1/font/bootstrap-icons.css" />
</head>
<body>
    <!-- Main container -->
    <div class="container">
        <!-- msg-header section starts -->
        <div class="msg-header">
            <div class="container1">
                <img src="http://images6.fanpop.com/image/photos/36700000/Game-of-Thrones-image-game-of-thrones-36704090-100-100.png" class="msgimg" />
                <div class="active">
                    <p>Chattie</p>
                </div>
            </div>
        </div>
        <!-- msg-header section ends -->
        <!-- Chat inbox  -->
        <div class="chat-page">
            <div class="msg-inbox">
                <div class="chats">
                    <!-- Message container -->
                    <div class="msg-page" id="messages">
                        <!-- Dynamic messages will be added here -->
                    </div>
                </div>
                <!-- msg-bottom section -->
                <div class="msg-bottom">
                    <div class="input-group">
                        <input type="text" id="messageText" class="form-control" placeholder="Write message..." />
                        <span class="input-group-text send-icon" onclick="sendMessage(event)">
                            <i class="bi bi-send"></i>
                        </span>
                        <span class="input-group-text send-icon">
                        <a href="#" download="history.txt">
                            <i class="bi bi-download"></i>
                        </a>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
        ws.onmessage = function(event) {
            var messages = document.getElementById('messages');
            var message = document.createElement('div');
            message.classList.add('received-chats'); // Adjust class as necessary for styling
            var content = document.createElement('p');
            content.textContent = event.data;
            message.appendChild(content);
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;  // Scroll to the bottom
        };
        function sendMessage(event) {
            var input = document.getElementById("messageText");
            ws.send(input.value);
            // Display the sent message
            var messages = document.getElementById('messages');
            var message = document.createElement('div');
            message.classList.add('outgoing-chats'); // Adjust class as necessary for styling
            var content = document.createElement('p');
            content.textContent = input.value;
            message.appendChild(content);
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;  // Scroll to the bottom
            input.value = '';
            event.preventDefault();
        }
    </script>
</body>
</html>

"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    conversation = []

    while True:
        data = await websocket.receive_text()
        summary = await process_summary(data)
        chat_time = datetime.datetime.now()
        # persisting the chat
        conversation.append((chat_time.strftime('%B %m, %Y %I:%M %p'), data, summary))

        await websocket.send_text(f"Chattie: {summary}")

        with open("history.txt", 'a') as f:
            print(conversation, end="", file=f)


async def process_summary(input_text: str) -> str:
    message = {
        "role": "user",
        "content": input_text
    }
    response = await llm.chat(
        model="llama3.2", messages=[message], stream=False
    )
    return response["message"]["content"]


@app.post("/summaries/", response_model=SimplaText)
async def create_summary(summary: SimplaText):
    summary.id = len(summaries) + 1
    summaries.append(summary)
    return summary

@app.get("/summaries/", response_model=List[SimplaText])
async def get_summary():
    return summaries

@app.get("/summaries/{summary_id}", response_model=SimplaText)
async def all_summaries(summary_id: int):
    try:
        return next(summary for summary in summaries if summary.id == summary_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Summary not found")

@app.put("/summaries/{summary_id}", response_model=SimplaText)
async def edit_summary(summary_id: int, summary: SimplaText):
    for i, s in enumerate(summaries):
        if s.id == summary_id:
            summary.id = summary_id
            summaries[i] = summary
            return summary
    raise HTTPException(status_code=404, detail="Summary not found")

@app.delete("/summaries/{summary_id}")
async def remove_summary(summary_id: int):
    for i, summary in enumerate(summaries):
        if summary.id == summary_id:
            del summaries[i]
            return {"message": "Summary deleted successfully"}
    raise HTTPException(status_code=404, detail="Summary not found")