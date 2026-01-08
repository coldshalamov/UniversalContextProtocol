/**
 * Provider Service - Handles LLM provider communication
 */

import axios from 'axios';

interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
}

interface Tool {
    name: string;
    description?: string;
    inputSchema?: Record<string, unknown>;
}

interface ChatResponse {
    content: string;
    toolCalls?: Array<{
        name: string;
        arguments: Record<string, unknown>;
    }>;
    usage?: {
        promptTokens: number;
        completionTokens: number;
    };
}

interface StreamChunk {
    content: string;
    done: boolean;
}

interface ProviderConfig {
    name: string;
    displayName: string;
    apiBase: string;
    models: string[];
    supportsTools: boolean;
}

const PROVIDERS: Record<string, ProviderConfig> = {
    openai: {
        name: 'openai',
        displayName: 'OpenAI',
        apiBase: 'https://api.openai.com/v1',
        models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'o1', 'o1-mini'],
        supportsTools: true,
    },
    anthropic: {
        name: 'anthropic',
        displayName: 'Anthropic',
        apiBase: 'https://api.anthropic.com',
        models: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
        supportsTools: true,
    },
    google: {
        name: 'google',
        displayName: 'Google',
        apiBase: 'https://generativelanguage.googleapis.com/v1beta',
        models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
        supportsTools: true,
    },
    groq: {
        name: 'groq',
        displayName: 'Groq',
        apiBase: 'https://api.groq.com/openai/v1',
        models: ['llama-3.3-70b-versatile', 'llama-3.2-90b-text-preview', 'mixtral-8x7b-32768'],
        supportsTools: true,
    },
    together: {
        name: 'together',
        displayName: 'Together AI',
        apiBase: 'https://api.together.xyz/v1',
        models: ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'mistralai/Mixtral-8x22B-Instruct-v0.1'],
        supportsTools: true,
    },
    deepseek: {
        name: 'deepseek',
        displayName: 'DeepSeek',
        apiBase: 'https://api.deepseek.com/v1',
        models: ['deepseek-chat', 'deepseek-reasoner'],
        supportsTools: true,
    },
    mistral: {
        name: 'mistral',
        displayName: 'Mistral',
        apiBase: 'https://api.mistral.ai/v1',
        models: ['mistral-large-latest', 'mistral-medium-latest', 'mistral-small-latest'],
        supportsTools: true,
    },
    xai: {
        name: 'xai',
        displayName: 'xAI',
        apiBase: 'https://api.x.ai/v1',
        models: ['grok-beta', 'grok-2'],
        supportsTools: true,
    },
    perplexity: {
        name: 'perplexity',
        displayName: 'Perplexity',
        apiBase: 'https://api.perplexity.ai',
        models: ['sonar-pro', 'sonar'],
        supportsTools: false,
    },
    openrouter: {
        name: 'openrouter',
        displayName: 'OpenRouter',
        apiBase: 'https://openrouter.ai/api/v1',
        models: ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'google/gemini-pro'],
        supportsTools: true,
    },
    ollama: {
        name: 'ollama',
        displayName: 'Ollama (Local)',
        apiBase: 'http://localhost:11434/v1',
        models: ['llama3.2', 'llama3.1', 'codellama', 'mistral'],
        supportsTools: false,
    },
};

export class ProviderService {
    private apiKeys: Record<string, string>;

    constructor(apiKeys: Record<string, string> = {}) {
        this.apiKeys = apiKeys;
    }

    updateApiKey(provider: string, key: string): void {
        this.apiKeys[provider] = key;
    }

    listProviders(): ProviderConfig[] {
        return Object.values(PROVIDERS);
    }

    getModels(provider: string): string[] {
        return PROVIDERS[provider]?.models || [];
    }

    async chat(
        messages: Message[],
        provider: string = 'anthropic',
        model?: string,
        tools?: Tool[]
    ): Promise<ChatResponse> {
        const config = PROVIDERS[provider];
        if (!config) throw new Error(`Unknown provider: ${provider}`);

        const apiKey = this.apiKeys[provider];
        if (!apiKey && provider !== 'ollama') {
            throw new Error(`No API key for ${provider}`);
        }

        model = model || config.models[0];

        // Route to appropriate handler
        if (provider === 'anthropic') {
            return this.chatAnthropic(messages, model, tools, apiKey);
        } else if (provider === 'google') {
            return this.chatGoogle(messages, model, tools, apiKey);
        } else {
            // OpenAI-compatible
            return this.chatOpenAI(messages, model, tools, config.apiBase, apiKey);
        }
    }

    async *streamChat(
        messages: Message[],
        provider: string = 'anthropic',
        model?: string,
        tools?: Tool[]
    ): AsyncGenerator<StreamChunk> {
        // For now, yield the full response
        // TODO: Implement proper streaming
        const response = await this.chat(messages, provider, model, tools);
        yield { content: response.content, done: true };
    }

    private async chatOpenAI(
        messages: Message[],
        model: string,
        tools: Tool[] | undefined,
        apiBase: string,
        apiKey: string
    ): Promise<ChatResponse> {
        const payload: Record<string, unknown> = {
            model,
            messages: messages.map(m => ({ role: m.role, content: m.content })),
        };

        if (tools && tools.length > 0) {
            payload.tools = tools.map(t => ({
                type: 'function',
                function: {
                    name: t.name,
                    description: t.description,
                    parameters: t.inputSchema,
                },
            }));
        }

        const response = await axios.post(`${apiBase}/chat/completions`, payload, {
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
            },
            timeout: 60000,
        });

        const choice = response.data.choices[0];
        return {
            content: choice.message.content || '',
            toolCalls: choice.message.tool_calls?.map((tc: any) => ({
                name: tc.function.name,
                arguments: JSON.parse(tc.function.arguments),
            })),
            usage: {
                promptTokens: response.data.usage?.prompt_tokens,
                completionTokens: response.data.usage?.completion_tokens,
            },
        };
    }

    private async chatAnthropic(
        messages: Message[],
        model: string,
        tools: Tool[] | undefined,
        apiKey: string
    ): Promise<ChatResponse> {
        // Extract system message
        let system: string | undefined;
        const filteredMessages = messages.filter(m => {
            if (m.role === 'system') {
                system = m.content;
                return false;
            }
            return true;
        });

        const payload: Record<string, unknown> = {
            model,
            max_tokens: 8192,
            messages: filteredMessages.map(m => ({
                role: m.role === 'user' ? 'user' : 'assistant',
                content: m.content,
            })),
        };

        if (system) {
            payload.system = system;
        }

        if (tools && tools.length > 0) {
            payload.tools = tools.map(t => ({
                name: t.name,
                description: t.description,
                input_schema: t.inputSchema,
            }));
        }

        const response = await axios.post('https://api.anthropic.com/v1/messages', payload, {
            headers: {
                'x-api-key': apiKey,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01',
            },
            timeout: 60000,
        });

        const content = response.data.content
            .filter((b: any) => b.type === 'text')
            .map((b: any) => b.text)
            .join('');

        const toolCalls = response.data.content
            .filter((b: any) => b.type === 'tool_use')
            .map((b: any) => ({
                name: b.name,
                arguments: b.input,
            }));

        return {
            content,
            toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
            usage: {
                promptTokens: response.data.usage?.input_tokens,
                completionTokens: response.data.usage?.output_tokens,
            },
        };
    }

    private async chatGoogle(
        messages: Message[],
        model: string,
        tools: Tool[] | undefined,
        apiKey: string
    ): Promise<ChatResponse> {
        // Extract system message
        let system: string | undefined;
        const contents = messages
            .filter(m => {
                if (m.role === 'system') {
                    system = m.content;
                    return false;
                }
                return true;
            })
            .map(m => ({
                role: m.role === 'user' ? 'user' : 'model',
                parts: [{ text: m.content }],
            }));

        const payload: Record<string, unknown> = { contents };

        if (system) {
            payload.systemInstruction = { parts: [{ text: system }] };
        }

        if (tools && tools.length > 0) {
            payload.tools = [{
                functionDeclarations: tools.map(t => ({
                    name: t.name,
                    description: t.description,
                    parameters: t.inputSchema,
                })),
            }];
        }

        const response = await axios.post(
            `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`,
            payload,
            {
                params: { key: apiKey },
                timeout: 60000,
            }
        );

        const candidate = response.data.candidates[0];
        const parts = candidate.content.parts;

        const textContent = parts
            .filter((p: any) => p.text)
            .map((p: any) => p.text)
            .join('');

        const toolCalls = parts
            .filter((p: any) => p.functionCall)
            .map((p: any) => ({
                name: p.functionCall.name,
                arguments: p.functionCall.args,
            }));

        return {
            content: textContent,
            toolCalls: toolCalls.length > 0 ? toolCalls : undefined,
        };
    }
}
