> ## Documentation Index
>
> Fetch the complete documentation index at: [/llms.txt](https://docs.langchain.com/llms.txt)
>
> Use this file to discover all available pages before exploring further.

[Skip to main content](https://docs.langchain.com/oss/python/langgraph/studio#content-area)

When building agents with LangChain locally, it’s helpful to visualize what’s happening inside your agent, interact with it in real-time, and debug issues as they occur. **LangSmith Studio** is a free visual interface for developing and testing your LangChain agents from your local machine.Studio connects to your locally running agent to show you each step your agent takes: the prompts sent to the model, tool calls and their results, and the final output. You can test different inputs, inspect intermediate states, and iterate on your agent’s behavior without additional code or deployment.This pages describes how to set up Studio with your local LangChain agent.

## [​](https://docs.langchain.com/oss/python/langgraph/studio\#prerequisites)  Prerequisites

Before you begin, ensure you have the following:

- **A LangSmith account**: Sign up (for free) or log in at [smith.langchain.com](https://smith.langchain.com/?utm_source=docs&utm_medium=cta&utm_campaign=langsmith-signup&utm_content=oss-langgraph-studio).
- **A LangSmith API key**: Follow the [Create an API key](https://docs.langchain.com/langsmith/create-account-api-key) guide.
- If you don’t want data [traced](https://docs.langchain.com/langsmith/observability-concepts#traces) to LangSmith, set `LANGSMITH_TRACING=false` in your application’s `.env` file. With tracing disabled, no data leaves your local server.

## [​](https://docs.langchain.com/oss/python/langgraph/studio\#set-up-local-agent-server)  Set up local Agent server

### [​](https://docs.langchain.com/oss/python/langgraph/studio\#1-install-the-langgraph-cli)  1\. Install the LangGraph CLI

The [LangGraph CLI](https://docs.langchain.com/langsmith/cli) provides a local development server (also called [Agent Server](https://docs.langchain.com/langsmith/agent-server)) that connects your agent to Studio.

```
# Python >= 3.11 is required.
pip install --upgrade "langgraph-cli[inmem]"
```

### [​](https://docs.langchain.com/oss/python/langgraph/studio\#2-prepare-your-agent)  2\. Prepare your agent

If you already have a LangChain agent, you can use it directly. This example uses a simple email agent:

agent.py

```
from langchain.agents import create_agent

def send_email(to: str, subject: str, body: str):
    """Send an email"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    # ... email sending logic

    return f"Email sent to {to}"

agent = create_agent(
    "gpt-5.5",
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
```

### [​](https://docs.langchain.com/oss/python/langgraph/studio\#3-environment-variables)  3\. Environment variables

Studio requires a LangSmith API key to connect your local agent. Create a `.env` file in the root of your project and add your API key from [LangSmith](https://smith.langchain.com/settings).

Ensure your `.env` file is not committed to version control, such as Git.

.env

```
LANGSMITH_API_KEY=lsv2...
```

### [​](https://docs.langchain.com/oss/python/langgraph/studio\#4-create-a-langgraph-config-file)  4\. Create a LangGraph config file

The LangGraph CLI uses a configuration file to locate your agent and manage dependencies. Create a `langgraph.json` file in your app’s directory:

langgraph.json

```
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent.py:agent"
  },
  "env": ".env"
}
```

The [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent) function automatically returns a compiled LangGraph graph, which is what the `graphs` key expects in the configuration file.

For detailed explanations of each key in the JSON object of the configuration file, refer to the [LangGraph configuration file reference](https://docs.langchain.com/langsmith/cli#configuration-file).

At this point, the project structure will look like this:

```
my-app/
├── src
│   └── agent.py
├── .env
└── langgraph.json
```

### [​](https://docs.langchain.com/oss/python/langgraph/studio\#5-install-dependencies)  5\. Install dependencies

Install your project dependencies from the root directory:

pip

uv

```
pip install langchain langchain-openai
```

### [​](https://docs.langchain.com/oss/python/langgraph/studio\#6-view-your-agent-in-studio)  6\. View your agent in Studio

Start the development server to connect your agent to Studio:

```
langgraph dev
```

Safari blocks `localhost` connections to Studio. To work around this, run the above command with `--tunnel` to access Studio via a secure tunnel. You’ll need to manually add the tunnel URL to allowed origins by clicking **Connect to a local server** in the Studio UI. See the [troubleshooting guide](https://docs.langchain.com/langsmith/troubleshooting-studio#safari-connection-issues) for steps.

Once the server is running, your agent is accessible both via API at `http://127.0.0.1:2024` and through the Studio UI at `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`:

![Agent view in the Studio UI](https://mintcdn.com/langchain-5e9cc07a/TCDks4pdsHdxWmuJ/oss/images/studio_create-agent.png?fit=max&auto=format&n=TCDks4pdsHdxWmuJ&q=85&s=ebd259e9fa24af7d011dfcc568f74be2)

With Studio connected to your local agent, you can iterate quickly on your agent’s behavior. Run a test input, inspect the full execution trace including prompts, tool arguments, return values, and token/latency metrics in [LangSmith](https://docs.langchain.com/langsmith/observability-studio). When something goes wrong, Studio captures exceptions with the surrounding state to help you understand what happened.The development server supports hot-reloading—make changes to prompts or tool signatures in your code, and Studio reflects them immediately. Re-run conversation threads from any step to test your changes without starting over. This workflow scales from simple single-tool agents to complex multi-node graphs.For more information on how to run Studio, refer to the following guides in the [LangSmith docs](https://docs.langchain.com/langsmith/observability):

- [Run application](https://docs.langchain.com/langsmith/use-studio#run-application)
- [Manage assistants](https://docs.langchain.com/langsmith/use-studio#manage-assistants)
- [Manage threads](https://docs.langchain.com/langsmith/use-studio#manage-threads)
- [Iterate on prompts](https://docs.langchain.com/langsmith/observability-studio)
- [Debug LangSmith traces](https://docs.langchain.com/langsmith/observability-studio#debug-langsmith-traces)
- [Add node to dataset](https://docs.langchain.com/langsmith/observability-studio#add-node-to-dataset)

## [​](https://docs.langchain.com/oss/python/langgraph/studio\#video-guide)  Video guide

LangSmith Studio v2: The Ultimate Agent Development Environment - YouTube

Tap to unmute

[LangSmith Studio v2: The Ultimate Agent Development Environment](https://www.youtube.com/watch?v=Mi1gSlHwZLM) [LangChain](https://www.youtube.com/channel/UCC-lyoTfSrcJzA1ab3APAgw)

LangChain187K subscribers

[Watch on](https://www.youtube.com/watch?v=Mi1gSlHwZLM)

* * *

[Connect these docs](https://docs.langchain.com/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.

[Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/langgraph/studio.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).

Was this page helpful?

YesNo

[Backward compatibility\\
\\
Previous](https://docs.langchain.com/oss/python/langgraph/backward-compatibility) [Agent Chat UI\\
\\
Next](https://docs.langchain.com/oss/python/langgraph/ui)

Ctrl+I

![Agent view in the Studio UI](https://mintcdn.com/langchain-5e9cc07a/TCDks4pdsHdxWmuJ/oss/images/studio_create-agent.png?w=840&fit=max&auto=format&n=TCDks4pdsHdxWmuJ&q=85&s=92991302ac24604022ab82ac22729f68)