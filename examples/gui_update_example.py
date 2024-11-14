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

load_dotenv()

app = FastAPI()

# Store active WebSocket connections
active_connections = []

# Export the callback for other modules to use
websocket_gui_callback = None

async def initialize_websocket_callback():
    """Initialize the WebSocket callback function"""
    async def _websocket_gui_callback(update_info):
        """Send updates to all connected WebSocket clients"""
        for connection in active_connections[:]:  # Create a copy of the list to safely modify it
            try:
                # Add timestamp to updates
                update_info["timestamp"] = datetime.datetime.now().isoformat()
                await connection.send_json(update_info)
                logger.debug(f"Sent WebSocket update: {update_info['event']}")
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {e}")
                try:
                    active_connections.remove(connection)
                except ValueError:
                    pass  # Connection was already removed

    global websocket_gui_callback
    websocket_gui_callback = _websocket_gui_callback
    return websocket_gui_callback

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
                                    <pre>State: ${data.state}
Current Action: ${data.current_action || 'None'}</pre>
                                </div>`;
                            break;

                        case 'acting':
                            updateHtml = `
                                <div class="update acting">
                                    <strong>Acting - ${data.action}</strong>
                                    <pre>${data.description}</pre>
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
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

@app.get("/kickoff")
async def kickoff():
    # Initialize the WebSocket callback
    callback = await initialize_websocket_callback()

    # Define configurations for different models
    gpt4 = Config.default()
    gpt4.llm.model = "gpt-4o-mini"

    da1_action = Action(config=gpt4, name="DataAnalyst1", instruction="Analyze historical company data")
    da2_action = Action(config=gpt4, name="DataAnalyst2", instruction="Analyze historical company sales and marketing data")

    data_analyst_1 = DataInterpreter(name="Alex", profile="Data Analyst for sales", actions=[da1_action])
    data_analyst_2 = DataInterpreter(name="Bob", profile="Data Analyst for marketing", actions=[da2_action])

    env = Environment(desc="Sales and Marketing Data Analysis")

    # Set the WebSocket callback for the WebSocketClient
    WebSocketClient.set_callback(websocket_gui_callback)

    team = Team(investment=10.0, env=env, roles=[data_analyst_1, data_analyst_2],
                progress_callback=gui_update_callback)  # Use the standard gui_update_callback

    # Start the team's work in the background
    asyncio.create_task(team.run(idea="Create dummy sales data for a chocolate company and Analyze the sales data.", send_to="Alex", n_round=5, auto_archive=False))

    return {"status": "started"}
