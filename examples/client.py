import asyncio
import ai_streamer_twitch as ast

async def main():
    twitch_client = ast.TwitchClient("ws://localhost:8000")
    # Token with atleast these scopes: chat:read bits:read channel:read:subscriptions channel:manage:broadcast user:edit:broadcast
    await twitch_client.connect("user_name", "token", ["channels"])

    while True:
        print(twitch_client.get_newest_messages())
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())