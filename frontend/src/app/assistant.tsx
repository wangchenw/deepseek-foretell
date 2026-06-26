"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import {
  useChatRuntime,
  AssistantChatTransport,
} from "@assistant-ui/react-ai-sdk";
import { lastAssistantMessageIsCompleteWithToolCalls } from "ai";
import { Thread } from "@/components/thread";

const THREAD_STORAGE_KEY = "foretell.thread_id";

export const Assistant = () => {
  const runtime = useChatRuntime({
    sendAutomaticallyWhen: lastAssistantMessageIsCompleteWithToolCalls,
    transport: new AssistantChatTransport({
      api: "/api/chat",
      fetch: async (input, init) => {
        const response = await fetch(input, init);
        const threadId = response.headers.get("X-Foretell-Thread-Id");
        if (threadId) {
          window.localStorage.setItem(THREAD_STORAGE_KEY, threadId);
        }
        return response;
      },
      prepareSendMessagesRequest: async (options) => ({
        body: {
          ...options.body,
          id: options.id,
          messages: options.messages,
          trigger: options.trigger,
          messageId: options.messageId,
          metadata: options.requestMetadata,
          thread_id: window.localStorage.getItem(THREAD_STORAGE_KEY) ?? undefined,
        },
      }),
    }),
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="h-dvh bg-background">
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
};
