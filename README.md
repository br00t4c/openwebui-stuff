# Playwright Web Scrape

## Overview
* Type: FUNCTION 
* Original Post: https://openwebui.com/posts/f48d1120-7c69-4a3b-88cc-c49682c3663d

Here is a very simple function that will: 

* Detect and extract URLs in the body of a user message 
* Connect to a running instance of Playwright via websocket connection 
* Load the first detected URL 
* Extract text content from the loaded web page 
* Inject the content as context and emit a source/citation.

Very rough, but functional enough to be useful.  This one has been done many times by far more competent developers, but here is my version anyways! 

With default valve settings you will need playwright running in docker, listening on port 3000 for websocket connections. Here is a sample launch command for your Playwright container:

```bash
docker run \
  --restart always \
  --name playwright \
  -p 3000:3000 \
  -d \
  --init \
  -it \
  mcr.microsoft.com/playwright:v1.57.0-noble \
  /bin/sh -c "npx -y playwright:v1.57.0-noble run-server --port 3000 --host 0.0.0.0"
```

When the server starts, it typically prints the WebSocket URL to the console. The URL will look something like:  `ws://0.0.0.0:3000/` .

I made this function to scrape pages that I was not able to fetch using jina.ai. You will generally get more use out of this if you change the user agent to something other than the default (using the "User Agent" valve) as many sites block headless browsers. 

Happy scraping!

## Screenshot

![](./assets/Screenshot%20from%202026-01-01%2016-37-14.png)

# Bluesky Trending Topics

## Overview
* Type: TOOL
* Original Post: https://openwebui.com/posts/cdc48a4b-5173-4aea-9284-e32f02c7d9df

Here's a very simple tool that allows you to fetch currently trending topics on [Bluesky](https://bsky.app/)
## Screenshot
![](./assets/Screenshot%20from%202026-01-01%2016-41-13.png)


