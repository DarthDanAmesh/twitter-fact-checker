import asyncio
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from dotenv import dotenv_values
from pydantic import BaseModel
from typing import List, Optional
import pprint
from ollama import AsyncClient

# Initialize the Llama model locally
llm = AsyncClient()

app = FastAPI()

class SimplaText(BaseModel):
    id: Optional[int] = None
    url: str
    txt: str

summaries = []
clients = set()

html = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        #chat-container {
            background: white;
            width: 400px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            overflow: hidden;
        }
        #chat-header {
            background-color: #007bff;
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 1.2em;
        }
        #messages {
            list-style: none;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        #messages li {
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
            background-color: #f1f1f1;
        }
        #message-form {
            display: flex;
            border-top: 1px solid #ddd;
        }
        #messageText {
            border: none;
            padding: 15px;
            flex: 1;
        }
        #sendButton {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 15px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div id="chat-container">
        <div id="chat-header">WebSocket Chat</div>
        <ul id='messages'></ul>
        <form id="message-form" action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" placeholder="Type your message here..."/>
            <button id="sendButton">Send</button>
        </form>
    </div>
    <script>
        var ws = new WebSocket("ws://localhost:8000/ws");
        ws.onmessage = function(event) {
            var messages = document.getElementById('messages');
            var message = document.createElement('li');
            var content = document.createTextNode(event.data);
            message.appendChild(content);
            messages.appendChild(message);
        };
        function sendMessage(event) {
            var input = document.getElementById("messageText");
            ws.send(input.value);
            input.value = '';
            event.preventDefault();
        }
    </script>
</body>
</html>"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    while True:
        data = await websocket.receive_text()
        summary = await process_summary(data)
        await websocket.send_text(f"Summary: {summary}")

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