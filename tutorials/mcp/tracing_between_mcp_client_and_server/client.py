import asyncio

from agents import Agent, Runner
from agents.mcp import MCPServer, MCPServerStdio
from dotenv import load_dotenv
from phoenix.otel import register

load_dotenv()

tracer_provider = register(auto_instrument=True)


async def run(mcp_server: MCPServer):
    agent = Agent(
        name="助手",
        instructions="使用工具回答用户的问题。",
        mcp_servers=[mcp_server],
    )
    while True:
        message = input("\n\n请输入问题（输入 'exit' 或 'q' 退出）：")
        if message.lower() == "exit" or message.lower() == "q":
            break
        print(f"\n\n正在处理：{message}")
        result = await Runner.run(starting_agent=agent, input=message)
        print(result.final_output)


async def main():
    async with MCPServerStdio(
        name="金融分析服务端",
        params={
            "command": "fastmcp",
            "args": ["run", "./server.py"],
        },
        client_session_timeout_seconds=30,
    ) as server:
        await run(server)


if __name__ == "__main__":
    asyncio.run(main())
