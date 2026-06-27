> ## Documentation Index
>
> Fetch the complete documentation index at: [/docs/llms.txt](https://platform.minimax.io/docs/llms.txt)
>
> Use this file to discover all available pages before exploring further.

[Skip to main content](https://platform.minimax.io/docs/api-reference/text-chat-openai#content-area)

cURL

Image Understanding

```
curl --request POST \
  --url https://api.minimax.io/v1/chat/completions \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "MiniMax-M3",
  "messages": [\
    {\
      "role": "user",\
      "content": [\
        {\
          "type": "text",\
          "text": "What does this image show?"\
        },\
        {\
          "type": "image_url",\
          "image_url": {\
            "url": "https://filecdn.minimax.chat/public/fe9d04da-f60e-444d-a2e0-18ae743add33.jpeg"\
          }\
        }\
      ]\
    }\
  ],
  "thinking": {
    "type": "adaptive"
  },
  "max_completion_tokens": 500
}
'
```

200

Image Understanding

```
{
  "id": "066a33a7d290378f8a9e57a055812afa",
  "choices": [\
    {\
      "finish_reason": "stop",\
      "index": 0,\
      "message": {\
        "content": "<think>\nThe user is asking me to describe an image. Let me look at it carefully and provide a description.\n\nThe image shows a young girl, likely a child, with curly/wavy brown hair that has bangs. She has large brown/amber eyes and is smiling gently. She's wearing what appears to be a cream or off-white dress with lace/ruffled details. The lighting is soft and warm, suggesting this is a portrait-style photograph with a blurred neutral background.\n</think>\nThis image is a warm, softly-lit portrait photograph of a young girl, likely a child around 4-6 years old. Key features include:\n\n- **Hair**: Wavy/curly brown hair with bangs, with some strands pulled back or styled on top\n- **Eyes**: Large, expressive amber/brown eyes looking directly at the camera\n- **Expression**: A gentle, sweet smile\n- **Clothing**: A cream or off-white dress with delicate lace trim and ruffled cap sleeves\n- **Lighting**: Soft, warm, golden lighting that gives the image a dreamy, classic portrait quality\n- **Background**: A neutral, muted grayish-brown backdrop, blurred to keep focus on the subject\n\nThe overall aesthetic resembles a professional studio portrait or a finely-tuned AI-generated image, with attention to detail in features like the catchlights in her eyes, the texture of her hair, and the soft focus on the background. It has a timeless, painterly quality.",\
        "role": "assistant",\
        "name": "MiniMax AI",\
        "audio_content": ""\
      }\
    }\
  ],
  "created": 1780154535,
  "model": "MiniMax-M3",
  "object": "chat.completion",
  "usage": {
    "total_tokens": 1659,
    "total_characters": 0,
    "prompt_tokens": 1366,
    "completion_tokens": 293,
    "prompt_tokens_details": {
      "cached_tokens": 114
    }
  },
  "input_sensitive": false,
  "output_sensitive": false,
  "input_sensitive_type": 0,
  "output_sensitive_type": 0,
  "output_sensitive_int": 0,
  "base_resp": {
    "status_code": 0,
    "status_msg": ""
  }
}
```

POST

/

v1

/

chat

/

completions

Try it

cURL

Image Understanding

```
curl --request POST \
  --url https://api.minimax.io/v1/chat/completions \
  --header 'Authorization: Bearer <token>' \
  --header 'Content-Type: application/json' \
  --data '
{
  "model": "MiniMax-M3",
  "messages": [\
    {\
      "role": "user",\
      "content": [\
        {\
          "type": "text",\
          "text": "What does this image show?"\
        },\
        {\
          "type": "image_url",\
          "image_url": {\
            "url": "https://filecdn.minimax.chat/public/fe9d04da-f60e-444d-a2e0-18ae743add33.jpeg"\
          }\
        }\
      ]\
    }\
  ],
  "thinking": {
    "type": "adaptive"
  },
  "max_completion_tokens": 500
}
'
```

200

Image Understanding

```
{
  "id": "066a33a7d290378f8a9e57a055812afa",
  "choices": [\
    {\
      "finish_reason": "stop",\
      "index": 0,\
      "message": {\
        "content": "<think>\nThe user is asking me to describe an image. Let me look at it carefully and provide a description.\n\nThe image shows a young girl, likely a child, with curly/wavy brown hair that has bangs. She has large brown/amber eyes and is smiling gently. She's wearing what appears to be a cream or off-white dress with lace/ruffled details. The lighting is soft and warm, suggesting this is a portrait-style photograph with a blurred neutral background.\n</think>\nThis image is a warm, softly-lit portrait photograph of a young girl, likely a child around 4-6 years old. Key features include:\n\n- **Hair**: Wavy/curly brown hair with bangs, with some strands pulled back or styled on top\n- **Eyes**: Large, expressive amber/brown eyes looking directly at the camera\n- **Expression**: A gentle, sweet smile\n- **Clothing**: A cream or off-white dress with delicate lace trim and ruffled cap sleeves\n- **Lighting**: Soft, warm, golden lighting that gives the image a dreamy, classic portrait quality\n- **Background**: A neutral, muted grayish-brown backdrop, blurred to keep focus on the subject\n\nThe overall aesthetic resembles a professional studio portrait or a finely-tuned AI-generated image, with attention to detail in features like the catchlights in her eyes, the texture of her hair, and the soft focus on the background. It has a timeless, painterly quality.",\
        "role": "assistant",\
        "name": "MiniMax AI",\
        "audio_content": ""\
      }\
    }\
  ],
  "created": 1780154535,
  "model": "MiniMax-M3",
  "object": "chat.completion",
  "usage": {
    "total_tokens": 1659,
    "total_characters": 0,
    "prompt_tokens": 1366,
    "completion_tokens": 293,
    "prompt_tokens_details": {
      "cached_tokens": 114
    }
  },
  "input_sensitive": false,
  "output_sensitive": false,
  "input_sensitive_type": 0,
  "output_sensitive_type": 0,
  "output_sensitive_int": 0,
  "base_resp": {
    "status_code": 0,
    "status_msg": ""
  }
}
```

✨ **New model — `MiniMax-M3`****Core capabilities**: **Coding/Agentic SOTA**, **1M long context**, **multimodal**.

**What’s new in `MiniMax-M3`:**

1. Image and video understanding — see the example code on the right
2. Control thinking via the `thinking` parameter

#### Authorizations

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#authorization-authorization)

Authorization

string

header

required

`HTTP: Bearer Auth`

- Security Scheme Type: http
- HTTP Authorization Scheme: Bearer API\_key, used for account verification, can be viewed in [Account Management > API Keys](https://platform.minimax.io/user-center/basic-information/interface-key)

#### Headers

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#parameter-content-type)

Content-Type

enum<string>

default:application/json

required

Media type of the request body, should be set to `application/json` to ensure JSON format

Available options:

`application/json`

#### Body

application/json

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-model)

model

enum<string>

required

Model ID

Available options:

`MiniMax-M3`,

`MiniMax-M2.7`,

`MiniMax-M2.7-highspeed`,

`MiniMax-M2.5`,

`MiniMax-M2.5-highspeed`,

`MiniMax-M2.1`,

`MiniMax-M2.1-highspeed`,

`MiniMax-M2`

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-messages)

messages

object\[\]

required

A list of messages containing the conversation history. Supports text, image, video, and tool call content.

Showchild attributes

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-service-tier)

service\_tier

enum<string>

default:standard

Service tier for request admission. Supported values are `standard` and `priority`. If omitted, the request uses the `standard` tier. The `priority` [price](https://platform.minimax.io/docs/guides/pricing-paygo) is 1.5 times the `standard` price and ensures priority admission so the request is processed ahead of other requests, leading to faster responses and fewer failures.

Available options:

`standard`,

`priority`

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-thinking)

thinking

object

Controls MiniMax-M3 thinking. When omitted, adaptive thinking is enabled by default and responses include thinking content. For M2.x models, thinking cannot be disabled.

Showchild attributes

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-reasoning-split)

reasoning\_split

boolean

Output-format switch. When enabled, separates thinking content into the `reasoning_content` and `reasoning_details` fields. This does not enable or disable thinking.

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-stream)

stream

boolean

default:false

Whether to use streaming output, defaults to `false`. When set to `true`, the response will be returned in chunks.

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-stream-options)

stream\_options

object

Streaming response options.

Showchild attributes

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-max-completion-tokens)

max\_completion\_tokens

integer<int64>

Specifies the upper limit for generated content length, in tokens. For MiniMax-M3 the recommended value is 131072 (128K) and the maximum is 524288 (512K); for other models the recommended value is 65536 (64K) and the maximum is 204800 (200K). If generation stops due to `length`, try increasing this value.

Required range: `x >= 1`

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-temperature)

temperature

number<double>

default:1

Temperature coefficient, affects output randomness. Range \[0, 2\], default 1. Higher values produce more random output; lower values produce more deterministic output.

Required range: `0 <= x <= 2`

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-top-p)

top\_p

number<double>

default:0.95

Nucleus sampling parameter. Range \[0, 1\]. Default is 0.95 for MiniMax-M3 and 0.9 for M2.x models.

Required range: `0 <= x <= 1`

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-tools)

tools

object\[\]

Tool definition list. Function tools are supported.

Showchild attributes

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#body-max-tokens)

max\_tokens

integer<int64>

deprecated

Legacy generation length limit parameter. Deprecated; use `max_completion_tokens` instead.

Required range: `x >= 1`

#### Response

200

application/json

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-id)

id

string

Unique ID of this response

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-choices)

choices

object\[\]

List of response choices

Showchild attributes

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-created)

created

integer<int64>

Unix timestamp (seconds) when the response was created

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-model)

model

string

Model ID used for this request

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-object)

object

enum<string>

Object type. `chat.completion` for non-streaming, `chat.completion.chunk` for streaming

Available options:

`chat.completion`,

`chat.completion.chunk`

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-usage)

usage

object

Token usage statistics for this request

Showchild attributes

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-input-sensitive)

input\_sensitive

boolean

Whether the input content triggered sensitive word detection. If the input content is severely inappropriate, the API will return a content violation error message with empty reply content

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-input-sensitive-type)

input\_sensitive\_type

integer<int64>

Type of sensitive word triggered by input, returned when input\_sensitive is true. Values: 1 Severe violation; 2 Pornography; 3 Advertising; 4 Prohibited; 5 Abuse; 6 Violence/Terrorism; 7 Other

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-output-sensitive)

output\_sensitive

boolean

Whether the output content triggered sensitive word detection. If the output content is severely inappropriate, the API will return a content violation error message with empty reply content

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-output-sensitive-type)

output\_sensitive\_type

integer<int64>

Type of sensitive word triggered by output

[​](https://platform.minimax.io/docs/api-reference/text-chat-openai#response-base-resp)

base\_resp

object

Error status code and details

Showchild attributes

[Messages API](https://platform.minimax.io/docs/api-reference/text-chat-anthropic) [Create Response](https://platform.minimax.io/docs/api-reference/responses-create)

⌘I