type UiStreamChunk =
  | { type: "text-start"; id: string }
  | { type: "text-delta"; id: string; delta: string }
  | { type: "text-end"; id: string }
  | { type: "reasoning-start"; id: string }
  | { type: "reasoning-delta"; id: string; delta: string }
  | { type: "reasoning-end"; id: string };

type UiStreamWriter = {
  write: (chunk: UiStreamChunk) => void;
};

const THINK_OPEN_TAGS = [
  "\u003cthink\u003e",
  "\u003credacted_thinking\u003e",
] as const;

const THINK_CLOSE_TAGS = [
  "\u003c/think\u003e",
  "\u003c/redacted_thinking\u003e",
] as const;

type StreamMode = "text" | "reasoning";

function findEarliestTag(
  buffer: string,
  tags: readonly string[],
): { index: number; tag: string } | null {
  let best: { index: number; tag: string } | null = null;

  for (const tag of tags) {
    const index = buffer.indexOf(tag);
    if (index === -1) {
      continue;
    }
    if (!best || index < best.index) {
      best = { index, tag };
    }
  }

  return best;
}

function holdbackLength(buffer: string, tags: readonly string[]): number {
  if (tags.length === 0) {
    return 0;
  }
  const maxTagLength = Math.max(...tags.map((tag) => tag.length));
  return Math.min(buffer.length, Math.max(0, maxTagLength - 1));
}

export class ThinkStreamParser {
  private buffer = "";
  private mode: StreamMode = "text";
  private textOpen = false;
  private reasoningOpen = false;

  constructor(
    private readonly writer: UiStreamWriter,
    private readonly textId: string,
    private readonly reasoningId: string,
  ) {}

  push(delta: string) {
    if (!delta) {
      return;
    }
    this.buffer += delta;
    this.process();
  }

  flush() {
    if (this.buffer) {
      this.emitContent(this.buffer);
      this.buffer = "";
    }
    this.closeOpenParts();
  }

  private process() {
    while (this.buffer.length > 0) {
      if (this.mode === "reasoning") {
        const closeTag = findEarliestTag(this.buffer, THINK_CLOSE_TAGS);
        if (closeTag) {
          const before = this.buffer.slice(0, closeTag.index);
          if (before) {
            this.emitContent(before);
          }
          this.buffer = this.buffer.slice(closeTag.index + closeTag.tag.length);
          this.closeReasoning();
          this.mode = "text";
          continue;
        }

        const emitLength = this.buffer.length - holdbackLength(this.buffer, THINK_CLOSE_TAGS);
        if (emitLength <= 0) {
          break;
        }
        this.emitContent(this.buffer.slice(0, emitLength));
        this.buffer = this.buffer.slice(emitLength);
        continue;
      }

      const openTag = findEarliestTag(this.buffer, THINK_OPEN_TAGS);
      if (openTag) {
        const before = this.buffer.slice(0, openTag.index);
        if (before) {
          this.emitContent(before);
        }
        this.buffer = this.buffer.slice(openTag.index + openTag.tag.length);
        this.openReasoning();
        this.mode = "reasoning";
        continue;
      }

      const emitLength = this.buffer.length - holdbackLength(this.buffer, THINK_OPEN_TAGS);
      if (emitLength <= 0) {
        break;
      }
      this.emitContent(this.buffer.slice(0, emitLength));
      this.buffer = this.buffer.slice(emitLength);
    }
  }

  private emitContent(content: string) {
    if (!content) {
      return;
    }

    if (this.mode === "reasoning") {
      this.openReasoning();
      this.writer.write({
        type: "reasoning-delta",
        id: this.reasoningId,
        delta: content,
      });
      return;
    }

    this.openText();
    this.writer.write({ type: "text-delta", id: this.textId, delta: content });
  }

  private openText() {
    if (this.textOpen) {
      return;
    }
    this.writer.write({ type: "text-start", id: this.textId });
    this.textOpen = true;
  }

  private openReasoning() {
    if (this.reasoningOpen) {
      return;
    }
    this.writer.write({ type: "reasoning-start", id: this.reasoningId });
    this.reasoningOpen = true;
  }

  private closeReasoning() {
    if (!this.reasoningOpen) {
      return;
    }
    this.writer.write({ type: "reasoning-end", id: this.reasoningId });
    this.reasoningOpen = false;
  }

  private closeText() {
    if (!this.textOpen) {
      return;
    }
    this.writer.write({ type: "text-end", id: this.textId });
    this.textOpen = false;
  }

  private closeOpenParts() {
    if (this.mode === "reasoning") {
      this.closeReasoning();
      this.mode = "text";
    }
    this.closeText();
  }
}
