/**
 * UCP Client - Communicates with the UCP server
 */

import axios, { AxiosInstance } from 'axios';

export interface Tool {
    name: string;
    description?: string;
    tags?: string[];
    inputSchema?: Record<string, unknown>;
}

export interface ToolPrediction {
    tools: Tool[];
    reasoning?: string;
    scores: Record<string, number>;
    queryUsed: string;
}

export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    toolCalls?: Array<{
        name: string;
        arguments: Record<string, unknown>;
    }>;
}

export interface ChatResponse {
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

export class UCPClient {
    private client: AxiosInstance;
    private connected: boolean = false;
    private serverUrl: string;

    constructor(serverUrl: string = 'http://localhost:8765') {
        this.serverUrl = serverUrl;
        this.client = axios.create({
            baseURL: serverUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }

    setServerUrl(url: string): void {
        this.serverUrl = url;
        this.client = axios.create({
            baseURL: url,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });
        this.connected = false;
    }

    async connect(): Promise<boolean> {
        try {
            const response = await this.client.get('/health');
            this.connected = response.status === 200;
            return this.connected;
        } catch {
            this.connected = false;
            return false;
        }
    }

    disconnect(): void {
        this.connected = false;
    }

    async toggle(): Promise<boolean> {
        if (this.connected) {
            this.disconnect();
            return false;
        } else {
            return await this.connect();
        }
    }

    isConnected(): boolean {
        return this.connected;
    }

    async predictTools(
        context: string,
        recentTools: string[] = [],
        maxTools: number = 5
    ): Promise<ToolPrediction> {
        if (!this.connected) {
            return {
                tools: [],
                reasoning: 'Not connected to UCP server',
                scores: {},
                queryUsed: context,
            };
        }

        try {
            const response = await this.client.post('/predict', {
                context,
                recent_tools: recentTools,
                max_tools: maxTools,
            });

            return {
                tools: response.data.tools || [],
                reasoning: response.data.reasoning,
                scores: response.data.scores || {},
                queryUsed: response.data.query_used || context.substring(0, 100),
            };
        } catch (error) {
            console.error('Failed to predict tools:', error);
            return {
                tools: [],
                reasoning: `Error: ${error}`,
                scores: {},
                queryUsed: context,
            };
        }
    }

    async reportUsage(
        prediction: ToolPrediction,
        actuallyUsed: string[],
        success: boolean = true
    ): Promise<boolean> {
        if (!this.connected) {
            return false;
        }

        try {
            const response = await this.client.post('/feedback', {
                predicted_tools: prediction.tools.map(t => t.name),
                actually_used: actuallyUsed,
                success,
                query_used: prediction.queryUsed,
            });
            return response.status === 200;
        } catch {
            return false;
        }
    }

    async getAvailableTools(): Promise<Tool[]> {
        if (!this.connected) {
            return [];
        }

        try {
            const response = await this.client.get('/tools');
            return response.data.tools || [];
        } catch {
            return [];
        }
    }

    async searchTools(query: string, topK: number = 10): Promise<Tool[]> {
        if (!this.connected) {
            return [];
        }

        try {
            const response = await this.client.get('/tools/search', {
                params: { query, top_k: topK },
            });
            return response.data.results || [];
        } catch {
            return [];
        }
    }

    async getStatus(): Promise<Record<string, unknown>> {
        try {
            const response = await this.client.get('/status');
            return response.data;
        } catch {
            return { status: 'unavailable' };
        }
    }

    async chat(
        messages: Message[],
        tools?: Tool[]
    ): Promise<ChatResponse> {
        if (!this.connected) {
            throw new Error('Not connected to UCP server');
        }

        try {
            const response = await this.client.post('/chat', {
                messages: messages.map(m => ({
                    role: m.role,
                    content: m.content,
                    tool_calls: m.toolCalls,
                })),
                tools: tools?.map(t => ({
                    type: 'function',
                    function: {
                        name: t.name,
                        description: t.description,
                        parameters: t.inputSchema,
                    },
                })),
            });

            return {
                content: response.data.content || '',
                toolCalls: response.data.tool_calls,
                usage: response.data.usage,
            };
        } catch (error) {
            throw new Error(`Chat request failed: ${error}`);
        }
    }
}
