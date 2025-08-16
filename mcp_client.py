import asyncio
import json
import uuid

def json_rpc_request(method, params=None, request_id=None):
    return {
        "jsonrpc": "2.0",
        "id": request_id or str(uuid.uuid4()),
        "method": method,
        "params": params or {}
    }

async def run_mcp_client(server_cmd):
    proc = await asyncio.create_subprocess_exec(
        *server_cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    async def send_message(message):
        msg_str = json.dumps(message) + "\n"
        proc.stdin.write(msg_str.encode())
        await proc.stdin.drain()

    async def read_message():
        line = await proc.stdout.readline()
        if not line:
            return None
        return json.loads(line.decode())

    # 1. Initialize (fixed)
    init_msg = json_rpc_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "MyMCPClient", "version": "0.1"}
    })
    await send_message(init_msg)
    print("➡ Sent initialize")
    print("⬅", json.dumps(await read_message(), indent=2))

    # 2. Send proper initialized notification
    initialized_msg = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    await send_message(initialized_msg)

    # 3. List available tools
    list_tools_msg = json_rpc_request("tools/list", {})
    await send_message(list_tools_msg)
    tools_response = await read_message()
    print("🛠 Tools:", json.dumps(tools_response, indent=2))

    # 4. Call a tool if available
    try:
        tool_name = tools_response["result"]["tools"][0]["name"]
        print(f"📡 Calling tool: {tool_name}")
        call_tool_msg = json_rpc_request("tools/call", {
            "name": tool_name,
            "arguments": {}
        })
        await send_message(call_tool_msg)
        print("⬅", json.dumps(await read_message(), indent=2))
    except Exception as e:
        print(f"⚠ No tools found or error: {e}")

    proc.terminate()
    await proc.wait()

if __name__ == "__main__":
    asyncio.run(run_mcp_client([
        "python", "server.py"
    ]))
