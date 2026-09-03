import { OpenRouter } from "@openrouter/sdk";
import type { ChatStreamChunk } from "@openrouter/sdk";
import type { ReasoningDetailUnion } from "@openrouter/sdk";
import fs from "fs";

const TERM_COLORS = {
  red: "\x1b[31m",
  grey: "\x1b[90m",
  blue: "\x1b[34m",
  teal: "\x1b[36m",
  orange: "\x1b[38;5;208m",
  yellow: "\x1b[33m",
  white: "\x1b[37m",
};

function termColor(s: string, color: keyof typeof TERM_COLORS) {
  return TERM_COLORS[color] + s + "\x1b[0m";
}
const apiKey = fs.readFileSync("../../../keys/openrouter.txt", "utf8");

const openrouter = new OpenRouter({
  apiKey,
});

// Stream the response to get reasoning tokens in usage
const stream = await openrouter.chat.send({
  chatRequest: {
    model: "z-ai/glm-5.3-flash",
    messages: [
      {
        role: "user",
        content: "Design a node-based shader editor",
      },
    ],
    stream: true,
    reasoning: {
      effort: "high",
      summary: "detailed",
    },
  },
});

let response = "";
let lastType = "";
let handleChunk = async (type: string, detail: string, color?: keyof typeof TERM_COLORS) => {
  if (lastType !== type) {
    lastType = type;
    await process.stdout.write(`\n\n== ${type} == \n`);
  }
  await process.stdout.write(color ? termColor(detail, color) : detail);
};

const formatReasoning = (details: ReasoningDetailUnion[]) => {
  let s = ''
  for (const detail of details) {
    switch (detail.type) {
    case 'reasoning.text':
      s += detail.text;
      break;
    case 'reasoning.summary':
      s += detail.summary;
      break;

    }
  }
  return s
}

for await (const chunk of stream as unknown as AsyncIterable<ChatStreamChunk>) {
  for (const chunkChoice of chunk.choices) {
    if (chunkChoice?.delta?.content) {
      await handleChunk("content", chunkChoice.delta.content, "teal");
    }
    if (chunkChoice?.delta?.reasoningDetails) {
      await handleChunk("reasoningDetails", formatReasoning(chunkChoice.delta.reasoningDetails), "white");
    }
    /*
    if (chunkChoice?.delta?.reasoning) {
      await handleChunk("reasoning", chunkChoice.delta.reasoning);
    }*/
    if (chunkChoice?.delta?.refusal) {
      await handleChunk("refusal", chunkChoice.delta.refusal, "red");
    }
    if (chunkChoice?.delta?.toolCalls) {
      await handleChunk("tool", 'tool request: ' + chunkChoice.delta.toolCalls.map(t => t.function?.name).join(", "), "red");
    }
  }

  // Usage information comes in the final chunk
  if (chunk.usage) {
    console.log(
      "\nReasoning tokens:",
      chunk.usage.completionTokensDetails?.reasoningTokens,
    );
  }
}
