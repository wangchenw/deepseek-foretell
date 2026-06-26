import {
  createUIMessageStream,
  createUIMessageStreamResponse,
  type UIMessage,
} from "ai";

const FORETELL_API_URL =
  process.env.FORETELL_API_URL ?? "http://127.0.0.1:8000";
const FORETELL_USER_ID = process.env.FORETELL_USER_ID ?? "test-user";

type ChatRequestBody = {
  messages: UIMessage[];
  thread_id?: string;
};

type ForetellChatResponse = {
  thread_id: string;
  content: string;
};

function extractText(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();
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

  const data = (await response.json()) as ForetellChatResponse;

  const stream = createUIMessageStream<UIMessage>({
    originalMessages: messages,
    execute({ writer }) {
      const textId = "foretell-response";

      writer.write({ type: "text-start", id: textId });
      writer.write({ type: "text-delta", id: textId, delta: data.content });
      writer.write({ type: "text-end", id: textId });
    },
    onError(error) {
      return error instanceof Error ? error.message : "Foretell request failed";
    },
  });

  return createUIMessageStreamResponse({
    stream,
    headers: {
      "X-Foretell-Thread-Id": data.thread_id,
    },
  });
}
