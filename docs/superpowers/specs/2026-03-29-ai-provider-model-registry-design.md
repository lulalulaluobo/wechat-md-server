# V3.1 AI Provider / Model Registry Design

English summary: Add a provider registry, model registry, and single current model selection for AI polish, while keeping the current AI connectivity test and existing polish pipeline behavior.

## Goal

Upgrade the current single AI configuration:

- `ai_base_url`
- `ai_api_key`
- `ai_model`

into a registry-based structure that supports:

- multiple providers
- multiple models
- one active model at a time
- unchanged AI connectivity test workflow

This change is scoped only to AI provider/model management. It does not change:

- WeChat article fetching
- image handling
- FNS sync
- Telegram workflow
- Clipper template import behavior
- AI polish output structure

## Product Scope

### In Scope

- built-in read-only providers
- user-defined custom providers
- multiple models bound to providers
- one selected model for runtime use
- AI connectivity testing against the selected model
- settings UI for provider/model management
- migration from legacy single-provider settings

### Out of Scope

- multiple simultaneous active models
- model fallback / retry chains
- automatic provider model list fetching
- per-conversion provider switching
- full Web Clipper provider feature parity
- provider-specific advanced tuning panels

## User-Facing Behavior

### Providers

The system will ship with these built-in read-only providers:

- `openai_compatible`
- `anthropic`
- `gemini`
- `ollama`
- `openrouter`

Users can also add custom providers.

Built-in providers are not editable in their protocol definition, but their connection configuration is editable:

- display name
- base URL when applicable
- API key when applicable
- enabled state

### Models

Users can create multiple models. Each model belongs to one provider and stores:

- `id`
- `provider_id`
- `display_name`
- `model_id`
- `enabled`

Only one model can be selected for runtime AI polish at a time.

### AI Test

The existing “测试 AI 连通性” action remains in place.

Its behavior changes from:

- test current `base_url + api_key + model`

to:

- resolve the currently selected model
- resolve its bound provider
- dispatch the test request through the provider adapter

The response contract stays the same:

- `success`
- `latency_ms`
- `model`
- `preview`
- `message`

## Data Model

### Runtime Settings Structure

Add these new fields under `user_settings.ai`:

```json
{
  "providers": [
    {
      "id": "openai-compatible-default",
      "type": "openai_compatible",
      "display_name": "OpenAI Compatible",
      "built_in": true,
      "enabled": true,
      "base_url": "",
      "api_key": ""
    }
  ],
  "models": [
    {
      "id": "model-1",
      "provider_id": "openai-compatible-default",
      "display_name": "gpt-5.4-mini",
      "model_id": "gpt-5.4-mini",
      "enabled": true
    }
  ],
  "selected_model_id": "model-1"
}
```

Sensitive fields continue to use the existing encrypted-at-rest mechanism:

- provider `api_key`

No model-level secrets are introduced.

## Migration Strategy

Legacy fields:

- `ai_base_url`
- `ai_api_key`
- `ai_model`

will be migrated on read if registry data is absent.

Migration rule:

1. create built-in provider entries
2. populate the `openai_compatible` provider from legacy `ai_base_url` and `ai_api_key`
3. create one model from legacy `ai_model`
4. set it as `selected_model_id`
5. preserve existing non-registry AI settings:
   - `ai_enabled`
   - `ai_prompt_template`
   - `ai_frontmatter_template`
   - `ai_body_template`
   - `ai_context_template`
   - `ai_allow_body_polish`
   - `ai_enable_content_polish`
   - `ai_content_polish_prompt`

Migration must be idempotent.

## Backend Architecture

### Provider Adapter Layer

Introduce a provider adapter abstraction:

- `OpenAICompatibleAdapter`
- `AnthropicAdapter`
- `GeminiAdapter`
- `OllamaAdapter`

`OpenRouter` uses the OpenAI-compatible adapter in V3.1.

`xAI` and `DeepSeek` are intentionally not first-class providers in V3.1; they are expected to work through `openai_compatible`.

Adapter responsibilities:

- validate provider config
- build request payload for connectivity test
- build request payload for AI polish
- normalize response into the existing internal result shape

## Runtime Resolution

All AI operations must resolve runtime config through:

1. selected model
2. model’s provider
3. provider adapter

That applies to:

- `/api/admin/ai-test`
- AI polish execution during `/api/convert`
- AI polish execution during batch jobs

## API Changes

### `/api/admin/settings`

Extend read/write payload with:

- `ai_providers`
- `ai_models`
- `ai_selected_model_id`

Read payload should return masked provider secrets without exposing raw API keys.

### `/api/config`

Continue returning AI summary, but source it from selected model:

- `ai_enabled`
- `ai_configured`
- `ai_model`
- `ai_selected_provider`

### `/api/admin/ai-test`

Keep the route and response format.

Behavior update:

- if a temporary provider/model payload is sent from the form, test that temporary configuration
- otherwise test the saved selected model

This preserves the current “test before save” workflow.

## Frontend Design

### Settings Page

Replace the current single-provider section:

- `OpenAI 兼容 Base URL`
- `API Key`
- `Model`

with three sections:

### 1. Provider Registry

- list built-in providers
- add custom provider
- edit provider connection info
- disable/enable provider

Built-in provider type is read-only.

### 2. Model Registry

- add model
- choose provider for model
- edit `display_name`
- edit `model_id`
- enable/disable model

### 3. Current Model Selection

- select one enabled model as active

### 4. AI Connectivity Test

Keep a visible `测试 AI 连通性` button.

The test result panel remains unchanged in shape and placement.

## UX Constraints

- do not turn AI config into a complex wizard
- keep the current page style and tab structure
- preserve low-friction testing
- keep model selection obvious
- prevent selecting a disabled model

## Validation Rules

### Provider Validation

- `openai_compatible`: requires `base_url`, optionally `api_key`
- `openrouter`: requires `base_url`, `api_key`
- `anthropic`: requires `api_key`, optional `base_url`
- `gemini`: requires `api_key`, optional `base_url`
- `ollama`: requires `base_url`, no API key required by default
- `custom`: validation depends on declared type; V3.1 custom providers are restricted to `openai_compatible` transport

### Model Validation

- `display_name` required
- `model_id` required
- `provider_id` must exist
- only one `selected_model_id`
- selected model must be enabled

## Error Handling

If AI provider/model resolution fails during runtime:

- AI polish degrades gracefully to non-AI output
- article conversion still succeeds
- result summary includes failure reason

If AI connectivity test fails:

- return structured failure
- do not mutate saved settings

If the selected model becomes invalid because its provider is deleted or disabled:

- mark `ai_configured = false`
- block AI test and AI runtime
- keep non-AI conversion working

## Testing Strategy

### Backend

- migration from legacy single-provider config
- provider/model save and reload
- masked secret behavior
- selected model resolution
- AI test against each adapter type
- invalid selected model handling
- AI polish still works with selected model

### Frontend

- settings page renders provider/model registry controls
- single selected model control exists
- AI test still renders correctly
- disabled providers/models behave correctly

### Regression

- existing AI polish flow still works after migration
- Clipper import still works
- FNS/image/Telegram flows are unaffected

## Recommended Implementation Order

1. add runtime config schema + migration
2. add provider/model adapter resolution layer
3. adapt AI test endpoint
4. adapt AI polish runtime to selected model
5. replace settings UI
6. add regression coverage

## Risks

### Configuration Complexity

Adding provider/model registries increases UI and state complexity. This is controlled by:

- keeping built-in providers read-only
- supporting only one active model
- limiting V3.1 custom providers to openai-compatible transport

### Provider Drift

Different vendors evolve their APIs. This is controlled by:

- isolating request logic in adapters
- keeping OpenRouter on the openai-compatible path
- not overfitting V3.1 to every vendor-specific feature

### Migration Errors

If migration is wrong, users may lose AI connectivity. This is controlled by:

- idempotent migration
- preserving legacy non-registry settings
- explicit tests for upgraded configs

## Acceptance Criteria

V3.1 is complete when:

- users can manage multiple providers
- users can manage multiple models
- users can select one active model
- AI connectivity test works with the active model
- AI polish uses the selected model
- legacy single-provider configs upgrade automatically
- no non-AI feature regresses
