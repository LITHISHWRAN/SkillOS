import asyncio

from app.gemini_client import gemini_client


async def main():

    response = await gemini_client.generate(
        system_prompt=(
            "You are an expert AI agent skill developer."
        ),
        user_prompt=(
            "Explain what SKILL.md is in one sentence."
        ),
    )

    print("\nMODEL RESPONSE:\n")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())