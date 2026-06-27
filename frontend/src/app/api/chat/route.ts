import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  type UIMessage,
} from "ai";
import { ThinkStreamParser } from "@/lib/think-stream-parser";

const FORETELL_API_URL =
  process.env.FORETELL_API_URL ?? "http://127.0.0.1:8000";
const FORETELL_USER_ID = process.env.FORETELL_USER_ID ?? "test-user";

type ChatRequestBody = {
  messages: UIMessage[];
  thread_id?: string;
};

type ForetellSseEvent =
  | { event: "thread"; thread_id: string }
  | { event: "token"; content: string }
  | { event: "done"; thread_id: string };

function extractText(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();
}

function parseSseBlock(block: string): ForetellSseEvent | null {
  let eventName = "";
  let dataLine = "";

  for (const line of block.split("\n")) {
    if (line.startsWith("event: ")) {
      eventName = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      dataLine = line.slice(6);
    }
  }

  if (!eventName || !dataLine) {
    return null;
  }

  try {
    const data = JSON.parse(dataLine) as Record<string, unknown>;
    if (eventName === "thread" && typeof data.thread_id === "string") {
      return { event: "thread", thread_id: data.thread_id };
    }
    if (eventName === "token" && typeof data.content === "string") {
      return { event: "token", content: data.content };
    }
    if (eventName === "done" && typeof data.thread_id === "string") {
      return { event: "done", thread_id: data.thread_id };
    }
  } catch {
    return null;
  }

  return null;
}

async function* readForetellSse(
  body: ReadableStream<Uint8Array>,
): AsyncGenerator<ForetellSseEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const flush = (): ForetellSseEvent[] => {
    const events: ForetellSseEvent[] = [];

    while (true) {
      const boundary = buffer.indexOf("\n\n");
      if (boundary === -1) {
        break;
      }

      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const parsed = parseSseBlock(block);
      if (parsed) {
        events.push(parsed);
      }
    }

    return events;
  };

  while (true) {
    for (const event of flush()) {
      yield event;
    }

    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
  }

  buffer += decoder.decode();
  for (const event of flush()) {
    yield event;
  }
}

export async function POST(req: Request) {
  const { messages, thread_id }: ChatRequestBody = await req.json();
  const latestUserMessage = [...messages]
    .reverse()
    .find((message) => message.role === "user");
  const message = latestUserMessage ? extractText(latestUserMessage) : "";

  if (!message) {
    return Response.json({ error: "message is required" }, { status: 400 });
  }

  const response = await fetch(`${FORETELL_API_URL}/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-User-Id": FORETELL_USER_ID,
    },
    body: JSON.stringify({
      message,
      stream: true,
      ...(thread_id ? { thread_id } : {}),
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    return Response.json(
      { error: errorText || `Foretell API returned ${response.status}` },
      { status: response.status },
    );
  }

  if (!response.body) {
    return Response.json({ error: "Foretell API returned empty body" }, { status: 502 });
  }

  const sse = readForetellSse(response.body);
  const first = await sse.next();
  if (first.done || first.value.event !== "thread") {
    return Response.json({ error: "Invalid Foretell SSE stream" }, { status: 502 });
  }

  const threadId = first.value.thread_id;

  const stream = createUIMessageStream<UIMessage>({
    originalMessages: messages,
    async execute({ writer }) {
      const parser = new ThinkStreamParser(
        writer,
        "foretell-response",
        "foretell-reasoning",
      );

      for await (const event of sse) {
        if (event.event === "token" && event.content) {
          parser.push(event.content);
        }
      }

      parser.flush();
    },
    onError(error) {
      return error instanceof Error ? error.message : "Foretell request failed";
    },
  });

  return createUIMessageStreamResponse({
    stream,
    headers: {
      "X-Foretell-Thread-Id": threadId,
    },
  });
}
