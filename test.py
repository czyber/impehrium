import asyncio
from openai import OpenAI, AsyncOpenAI
import os

from dotenv import load_dotenv
load_dotenv()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://api.deepseek.com")


async def main():
    messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
    response = await client.chat.completions.create(
        model="deepseek-reasoner",
        messages=messages,
        stream=True
    )
    async for message in response:
        if hasattr(message.choices[0], "delta") and hasattr(message.choices[0].delta, "reasoning_content") and message.choices[0].delta.reasoning_content:
            print(message.choices[0].delta.reasoning_content, end="")


if __name__ == "__main__":
    asyncio.run(main())




