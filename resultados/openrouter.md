# What each model supports: openrouter

Checked on 2026-10-13 21:33 UTC with `scripts/check_gateway.py`.

| Check | `google/gemma-4-26b-a4b-it` | `openai/gpt-oss-120b` | `mistralai/devstral-2512` |
|---|---|---|---|
| plain answer | yes | yes | yes |
| logprobs | yes | **no** | **no** |
| n = 3 | **no** | **no** | **no** |
| tools | yes | yes | yes |
| json_schema | yes | yes | yes |
| reasoning none | yes | **no** | yes |
| reasoning low | yes | yes | yes |

## `google/gemma-4-26b-a4b-it`

- plain answer: yes, 'OK', 0.4 s, 20+2 tokens
- logprobs: yes, first token '3'; alternatives: '3' 1.00, '2' 0.00, '1' 0.00, '6' 0.00, '5' 0.00
- n = 3: NO, 1 answers: Blue
- tools: yes, called get_requirement({'id': 'SRS-0004'}); the answer uses the result: yes
- json_schema: yes, {"id":"SRS-0004","seconds":2}
- reasoning none: yes, '12', 0 reasoning tokens, 0.6 s
- reasoning low: yes, '12', 267 reasoning tokens, 8.8 s

## `openai/gpt-oss-120b`

- plain answer: yes, 'OK', 4.1 s, 61+66 tokens, reasons by default (59 reasoning tokens)
- logprobs: NO, no logprobs in the answer ''
- n = 3: NO, 1 answers: Blue
- tools: yes, called get_requirement({'id': 'SRS-0004'}); the answer uses the result: yes
- json_schema: yes, { "id": "SRS-0004", "seconds": 2 }
- reasoning none: NO, HTTP 400: Error code: 400 - {'error': {'message': 'Reasoning is mandatory for this endpoint and cannot be disabled.', 'code': 400, 'metadata': {'provider_name': None}}}
- reasoning low: yes, '12', 40 reasoning tokens, 14.7 s

## `mistralai/devstral-2512`

- plain answer: yes, 'OK', 0.4 s, 22+2 tokens
- logprobs: NO, no logprobs in the answer '5'
- n = 3: NO, 1 answers: Blue
- tools: yes, called get_requirement({'id': 'SRS-0004'}); the answer uses the result: yes
- json_schema: yes, {"id": "SRS-0004", "seconds": 2}
- reasoning none: yes, "Alright, let's tackl", 0 reasoning tokens, 4.9 s
- reasoning low: yes, "Alright, let's tackl", 0 reasoning tokens, 5.0 s

## Embeddings: `baai/bge-m3`

- yes, 1024 dimensions; the Spanish question is closer to the stale track sentence: yes; 'SRS-0004' alone is closest to SRS-0004 0.528, SRS-0005 0.528, SRS-0011 0.520
- cosine with '¿Cuánto tarda en borrarse una traza?': stale track (en) 0.564, alarm (en) 0.456, recipe (es) 0.311
