/**
 * UCP Service - Handles communication with the UCP server
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

export class UCPService {
    private client: AxiosInstance;
    private connected: boolean = false;

    constructor(private serverUrl: string = 'http://localhost:8765') {
        this.client = axios.create({
            baseURL: serverUrl,
            timeout: 30000,
        });
    }

    setServerUrl(url: string): void {
        this.serverUrl = url;
        this.client = axios.create({
            baseURL: url,
            timeout: 30000,
        });
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

    isConnected(): boolean {
        return this.connected;
    }

    async predictTools(
        context: string,
        recentTools: string[] = [],
        maxTools: number = 5
    ): Promise<ToolPrediction> {
        if (!this.connected) {
            return { tools: [], scores: {}, queryUsed: context };
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
                queryUsed: response.data.query_used || context,
            };
        } catch (error) {
            console.error('Failed to predict tools:', error);
            return { tools: [], scores: {}, queryUsed: context };
        }
    }

    async reportUsage(
        prediction: ToolPrediction,
        actuallyUsed: string[],
        success: boolean = true
    ): Promise<boolean> {
        if (!this.connected) return false;

        try {
            await this.client.post('/feedback', {
                predicted_tools: prediction.tools.map(t => t.name),
                actually_used: actuallyUsed,
                success,
                query_used: prediction.queryUsed,
            });
            return true;
        } catch {
            return false;
        }
    }

    async getAvailableTools(): Promise<Tool[]> {
        if (!this.connected) return [];

        try {
            const response = await this.client.get('/tools');
            return response.data.tools || [];
        } catch {
            return [];
        }
    }

    async searchTools(query: string, topK: number = 10): Promise<Tool[]> {
        if (!this.connected) return [];

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
}
