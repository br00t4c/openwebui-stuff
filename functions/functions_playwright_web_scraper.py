"""
title: OpenWebUI Playwright Simple Webscraper
description: Retrieves a web page using Playwright via websocket connection
author: Peter Taylor
requirements: playwright
version: 0.1
"""

import asyncio
import re
import json
import requests
import os
import subprocess
import tempfile
import shutil
import html
from pydantic import BaseModel, Field
from open_webui.utils.misc import get_last_user_message
from typing import Callable, Awaitable, Any, Optional, Literal
from playwright.async_api import async_playwright


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )

    async def emit_source(self, name="test", link="Unknown State", content="Text"):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "chat:completion",
                    "data": {
                        "sources": [
                            {
                                "source": {
                                    "type": "doc",
                                    "name": name,
                                    "collection_name": f"playwright-scraped-pages",
                                    "status": "uploaded",
                                    "url": link,
                                    "error": "",
                                    "file": {
                                        "data": {"content": content},
                                        "meta": {"name": name},
                                    },
                                },
                                "document": [content],
                                "metadata": [
                                    {
                                        "language": "en-US",
                                        "source": link,
                                        "start_index": 0,
                                        "title": name,
                                    },
                                ],
                            }
                        ]
                    },
                }
            )


class Filter:
    class Valves(BaseModel):
        """
        Configuration options for the Playwright WebSocket scraper filter.
        """

        playwright_ws_url: str = Field(
            default="ws://localhost:3000",
            description="WebSocket URL for the Playwright server connection",
        )
        request_timeout: int = Field(
            default=30,
            ge=5,
            le=120,
            description="Timeout in seconds for page load operations",
        )
        wait_until: str = Field(
            default="domcontentloaded",
            description="When to consider navigation complete",
            json_schema_extra={
                "enum": ["domcontentloaded", "load", "networkidle", "commit"]
            },
        )
        user_agent: str = Field(
            default="",
            description="Specify this to override the default user agent string sent by playwright when scraping a url",
        )
        extract_main_content: bool = Field(
            default=True,
            description="Extract only main content (attempts to remove nav, footer, etc.)",
        )
        include_metadata: bool = Field(
            default=False, description="Include page metadata (title, URL) in output"
        )
        remove_scripts: bool = Field(
            default=True,
            description="Remove script tags and their content from extracted text",
        )
        max_content_length: Optional[int] = Field(
            default=None,
            ge=100,
            le=50000,
            description="Maximum characters to return (None for unlimited)",
        )

    class UserValves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()
        self.toggle = True
        self.icon = """data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGZpbGw9Im5vbmUiIHZpZXdCb3g9IjAgMCAyNCAyNCIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZT0iY3VycmVudENvbG9yIiBjbGFzcz0ic2l6ZS02Ij48cGF0aCBkPSJNMTIgM2EyLjgzIDIuODMgMCAwIDAtLjczLjA3TDUuNyA1LjA3YTIuODMgMi44MyAwIDAgMC0uMDcuNzNsNiA2LjM5N2wuMzMuMzMzYTIuODMgMi44MyAwIDAgMCAuNzMuMDdoLjM1bC02LjM5NyA2YTIuODMgMi44MyAwIDAgMCAuMDcuNzNsMS4zMzEgMS4zMzFhMi44MyAyLjgzIDAgMCAwIDMuODUtMy44NWwtNi02LjM5N2wuMzMzLS4zMzNhMi44MyAyLjgzIDAgMCAwIC4wNy0uNzN6Ii8+PC9zdmc+"""

    async def scrape_page(self, url: str):
        async with async_playwright() as p:
            browser = await p.chromium.connect(self.valves.playwright_ws_url)
            if self.valves.user_agent == "":
                page = await browser.new_page()
            else:
                context = await browser.new_context(user_agent=self.valves.user_agent)
                page = await context.new_page()
            try:
                await page.goto(url, wait_until="networkidle")
                content = await page.content()
                # Extract visible text content
                text_content = await page.evaluate(
                    """() => {
                    const body = document.body;
                    const scripts = body.querySelectorAll('script, style, noscript, header, footer, nav, iframe, object, embed');
                    scripts.forEach(script => script.remove());
                    return document.body.innerText;
                }"""
                )
                return {
                    "url": url,
                    "title": await page.title(),
                    "content": text_content.strip(),
                    "error": "",
                    "success": True,
                }
            except Exception as e:
                return {
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": str(e),
                    "success": False,
                }
            finally:
                await browser.close()

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict] = None,
    ) -> dict:
        try:
            emitter = EventEmitter(__event_emitter__)
            user_valves = __user__.get("valves") if __user__ else None
            if not user_valves:
                user_valves = self.UserValves()
            await emitter.emit(
                description=f"Checking for URLs to scrape in message body"
            )
            messages = body["messages"]
            last_message = get_last_user_message(messages)
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, last_message)
            if urls:
                url_to_scrape = urls[0]
                await emitter.emit(description=f"Scraping URL: {url_to_scrape}")
                scraped_content = await self.scrape_page(url_to_scrape)
                if scraped_content["success"]:
                    await emitter.emit(
                        status="complete",
                        description=f"Scraped {url_to_scrape} successfully",
                        done=True,
                    )
                    await emitter.emit_source(
                        name=scraped_content["title"],
                        link=scraped_content["url"],
                        content=scraped_content["content"],
                    )
                    message_to_cache = (
                        f"## Web page scrape details:\n"
                        f"- URL: {scraped_content['url']}\n"
                        f"- Title: {scraped_content['title']}\n"
                        f"---\n\n"
                        f"## web page contents:\n{scraped_content['content']}"
                    ).strip()
                    original_text = re.sub(
                        url_to_scrape,
                        "<URL REMOVED>",
                        last_message,
                    ).strip()
                    combined_message = (
                        f"## Original User Message:\n"
                        f"{original_text}\n"
                        f"---\n\n"
                        f"{message_to_cache}"
                    ).strip()
                    messages[-1]["content"] = combined_message
                    body["messages"] = messages
                    return body
                else:
                    await emitter.emit(
                        status="error",
                        description=f"Failed to scrape url {url_to_scrape}",
                        done=True,
                    )
                    return body
            else:
                await emitter.emit(
                    status="complete",
                    description=f"No URLs to scrape in body",
                    done=True,
                )
                return body
        except Exception as e:
            await emitter.emit(
                status="error",
                description=f"Error: {str(e)}",
                done=True,
            )
            return body
