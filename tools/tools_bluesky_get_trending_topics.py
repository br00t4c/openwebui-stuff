"""
title: Bluesky Trending Topics
author: Peter Taylor
version: 0.1
license: MIT
"""

import requests
import json
from datetime import datetime


class Tools:
    """
    Open WebUI Tool to fetch trending topics via Bluesky public API.
    """

    def __init__(self):
        self.name = "Bluesky Trending Topics"
        self.description = "Fetches Bluesky tranding topics"

    async def get_bluesky_trending(self) -> dict:
        """
        Fetches and parses the json feed via the Bluesky public API.
        Returns structured items with topic and link.
        """
        try:
            response = requests.get(
                f"https://public.api.bsky.app/xrpc/app.bsky.unspecced.getTrendingTopics",
                timeout=10,
            )
            response.raise_for_status()

        except Exception as e:
            return {"error": f"Failed to fetch feed: {e}"}

        try:
            ts = str(datetime.now())
            items = []
            for item in json.loads(response.content)["topics"]:
                topic = item["topic"].strip()
                link = item["link"].strip()
                items.append({"topic": topic, "link": link, "ts": ts})
        except Exception as e:
            print({"error": f"Failed to parse feed: {e}"})

        return {"items": items}
