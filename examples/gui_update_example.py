import asyncio
import datetime
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.utils.websocket_client import WebSocketClient
from metagpt.gui_update_callback import gui_update_callback
from metagpt.config2 import Config
from metagpt.environment import Environment
from metagpt.roles.di.data_interpreter import DataInterpreter
from metagpt.team import Team
from metagpt.roles import Role
from dotenv import load_dotenv
from typing import List

load_dotenv()

app = FastAPI()

# Initialize WebSocket connections list
active_connections: List[WebSocket] = []

# Export the callback for other modules to use
websocket_gui_callback = None


async def initialize_websocket_callback():
    """Initialize the WebSocket callback function"""
    async def _websocket_gui_callback(update_info):
        """Send updates to all connected WebSocket clients"""
        logger.info(f"Active connections: {len(active_connections)}")
        if not active_connections:
            logger.warning("No active WebSocket connections to send updates to.")
            return

        for connection in active_connections[:]:
            try:
                # Add timestamp if not present
                if 'timestamp' not in update_info:
                    update_info["timestamp"] = datetime.datetime.now().isoformat()

                # Send update and immediately flush
                await connection.send_json(update_info)
                await asyncio.sleep(0.1)  # Small delay between messages

                logger.debug(f"Sent WebSocket update: {update_info}")
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
                try:
                    active_connections.remove(connection)
                except ValueError:
                    pass

    # Set both the global callback and the WebSocketClient callback
    global websocket_gui_callback
    websocket_gui_callback = _websocket_gui_callback
    WebSocketClient.set_callback(_websocket_gui_callback)
    logger.info("WebSocket callback initialized")


@app.get("/")
async def get():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>MetaGPT Team Monitor</title>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <style>
                #updates {
                    height: 500px;
                    overflow-y: auto;
                    border: 1px solid #ccc;
                    padding: 10px;
                    margin: 10px 0;
                    font-family: monospace;
                    background: #f5f5f5;
                }
                .update {
                    margin: 10px 0;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background: white;
                }
                .update strong {
                    color: #2c3e50;
                    display: block;
                    margin-bottom: 5px;
                }
                .update pre {
                    margin: 0;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
            </style>
        </head>
        <body>
            <h1>MetaGPT Team Monitor</h1>
            <button onclick="startTeam()">Start MetaGPT Team</button>
            <div id="updates"></div>
            <script>
                let ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`);

                ws.onopen = function() {
                    console.log('WebSocket connected');
                };

                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };

                ws.onclose = function() {
                    console.log('WebSocket closed');
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    let updateHtml = '';

                    switch(data.event) {
                        case 'thinking':
                            updateHtml = `
                                <div class="update thinking">
                                    <strong>Thinking</strong>
                                    <pre>State: ${data.state} Current Action: ${data.current_action || 'None'}</pre>
                                </div>`;
                            break;

                        case 'acting':
                            updateHtml = `
                                <div class="update acting">
                                    <strong>Acting - ${data.action}</strong>
                                    <pre>${data.description}</pre>
                                </div>`;
                            break;

                        case 'SIMPLE_UPDATE':
                            updateHtml = `
                                <div class="update">
                                    <strong>${data.role || 'System'}</strong>: ${data.status}
                                    <div class="timestamp" style="font-size: 0.8em; color: #666;">
                                        ${new Date(data.timestamp).toLocaleString()}
                                    </div>
                                </div>`;
                            break;

                        case 'planning_and_acting':
                            updateHtml = `
                                <div class="update planning">
                                    <strong>Planning - ${data.current_task}</strong>
                                    <pre>${data.task_description}</pre>
                                </div>`;
                            break;

                        case 'team_progress':
                            data.messages.forEach(msg => {
                                updateHtml += `
                                    <div class="update progress">
                                        <strong>Round ${data.round} - ${msg.role}:</strong>
                                        <pre>${msg.content}</pre>
                                    </div>`;
                            });
                            break;
                    }

                    if (updateHtml) {
                        $('#updates').append(updateHtml);
                    }

                    // Auto-scroll to bottom
                    const updates = document.getElementById('updates');
                    updates.scrollTop = updates.scrollHeight;
                };

                function startTeam() {
                    fetch('/kickoff')
                        .then(response => response.json())
                        .then(data => console.log('Team started:', data));
                }

                $(document).ready(function() {
                    initializeWebSocket();
                });
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    active_connections.append(websocket)
    try:
        while True:
            try:
                # Set WebSocket to text mode for lower latency
                data = await websocket.receive_text()
                # Immediately acknowledge receipt
                await websocket.send_json({"status": "received"})
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info("WebSocket connection closed")


@app.on_event("startup")
async def startup_event():
    logger.info("Running setup_callbacks at startup.")
    await initialize_websocket_callback()
    logger.info("WebSocket callback initialized.")
    print("Ready.")


@app.get("/kickoff")
async def kickoff():
    # Initialize the WebSocket callback
    callback = await initialize_websocket_callback()

    # Define configurations for different models
    gpt4 = Config.default()
    gpt4.llm.model = "gpt-4o-mini"

    logger.info("UPDATING GUI inside /kickoff...")
    update_info = {
        "event": "SIMPLE_UPDATE",
        "status": "Inside kickoff, starting exec...",
        "current_task": None,
        "progress": 0,
        "role": "Manager",
        "profile": "Profile"
    }
    await gui_update_callback(update_info)

    action1 = Action(config=gpt4, name="AlexSay", instruction="Express your opinion with emotion and don't repeat it")
    action2 = Action(config=gpt4, name="BobSay", instruction="Express your opinion with emotion and don't repeat it")
    alex = Role(name="Alex", profile="Democratic candidate", goal="Win the election", actions=[action1], watch=[action2])
    bob = Role(name="Bob", profile="Republican candidate", goal="Win the election", actions=[action2], watch=[action1])
    env = Environment(desc="US election live broadcast")
    WebSocketClient.set_callback(websocket_gui_callback)
    team = Team(investment=10.0, env=env, roles=[alex, bob], progress_callback=gui_update_callback)

    asyncio.create_task(
        team.run(
            idea="Topic: climate change. Under 80 words per message.",
            send_to="Alex",
            n_round=5,
            auto_archive=False
        )
    )

    return {"status": "started"}
