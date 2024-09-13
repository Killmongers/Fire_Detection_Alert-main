import asyncio
import websockets
import json
from app.video_feed import gen_frames

async def handle_client(websocket, path):
    global ip_camera_url

    try:
        async for message in websocket:
            data = json.loads(message)
            if 'ip_camera_url' in data:
                ip_camera_url = data['ip_camera_url']

                if not ip_camera_url:
                    await websocket.send(json.dumps({"error": "No IP camera URL provided"}))
                    continue

                # Notify client to start video streaming
                await websocket.send(json.dumps({"status": "video_streaming_started"}))

                # Stream video feed
                async for frame in gen_frames():
                    await websocket.send(frame)
                    await asyncio.sleep(0.01)  # Small delay to control frame rate

    except Exception as e:
        await websocket.send(json.dumps({"error": str(e)}))

async def main():
    async with websockets.serve(handle_client, "localhost", 8765):
        print("WebSocket server started at ws://localhost:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
