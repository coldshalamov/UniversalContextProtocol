"""
Client API endpoints for UCP.

Provides additional REST endpoints specifically for the client applications
(CLI, VS Code Extension, Desktop App) to interact with UCP.

These endpoints are designed to be used alongside the core MCP endpoints
in http_server.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger(__name__)


class PredictRequest(BaseModel):
    """Request for tool prediction."""
    context: str = Field(description="Conversation context for prediction")
    recent_tools: list[str] = Field(default_factory=list, description="Recently used tools")
    max_tools: int = Field(default=5, description="Maximum tools to return")


class PredictResponse(BaseModel):
    """Response from tool prediction."""
    tools: list[dict] = Field(description="Predicted tool schemas")
    reasoning: str | None = Field(default=None, description="Explanation of prediction")
    scores: dict[str, float] = Field(default_factory=dict, description="Confidence scores")
    query_used: str = Field(description="Query used for retrieval")


class FeedbackRequest(BaseModel):
    """Request to report tool usage feedback."""
    predicted_tools: list[str] = Field(description="Tools that were predicted")
    actually_used: list[str] = Field(description="Tools that were actually used")
    success: bool = Field(default=True, description="Whether the tools succeeded")
    query_used: str = Field(description="Original query")
    timestamp: str | None = Field(default=None, description="When prediction was made")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: list[dict] = Field(description="Chat messages")
    tools: list[dict] | None = Field(default=None, description="Tools to include")
    provider: str | None = Field(default=None, description="LLM provider (if not using UCP's)")
    model: str | None = Field(default=None, description="Model to use")


class ChatResponse(BaseModel):
    """Response from chat completion."""
    content: str = Field(description="Assistant response")
    tool_calls: list[dict] | None = Field(default=None, description="Tool calls made")
    usage: dict | None = Field(default=None, description="Token usage")


def create_client_router(ucp_server) -> APIRouter:
    """
    Create a router with client-specific endpoints.
    
    Args:
        ucp_server: The UCPServer instance to use for predictions
    
    Returns:
        FastAPI APIRouter with client endpoints
    """
    router = APIRouter(tags=["Client API"])
    
    # Store feedback for learning
    feedback_store: list[dict] = []
    
    @router.post("/predict", response_model=PredictResponse)
    async def predict_tools(request: PredictRequest) -> PredictResponse:
        """
        Predict which tools will be needed for the given context.
        
        This is the core UCP functionality - given conversation context,
        predict and return the most relevant tools.
        """
        logger.info(
            "predict_tools_request",
            context_length=len(request.context),
            recent_tools=request.recent_tools,
        )
        
        try:
            # Use UCP's router to get predictions
            if ucp_server._router and ucp_server._session:
                # Update session context
                await ucp_server.update_context(request.context, role="user")
                
                # Get routing decision
                decision = ucp_server._router.route(
                    ucp_server._session,
                    current_message=request.context,
                )
                
                # Convert to tool schemas
                tools = []
                if ucp_server._tool_zoo:
                    for tool_name in decision.selected_tools[:request.max_tools]:
                        tool_schemas = ucp_server._tool_zoo.search(tool_name, top_k=1)
                        if tool_schemas:
                            tool, _ = tool_schemas[0]
                            tools.append({
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.input_schema,
                                }
                            })
                
                return PredictResponse(
                    tools=tools,
                    reasoning=decision.reasoning,
                    scores=decision.scores,
                    query_used=decision.query_used,
                )
            else:
                # No router available, return empty prediction
                return PredictResponse(
                    tools=[],
                    reasoning="Router not initialized",
                    scores={},
                    query_used=request.context[:100],
                )
                
        except Exception as e:
            logger.error("predict_tools_error", error=str(e))
            return PredictResponse(
                tools=[],
                reasoning=f"Error: {e}",
                scores={},
                query_used=request.context[:100],
            )
    
    @router.post("/feedback")
    async def report_feedback(request: FeedbackRequest) -> dict:
        """
        Report which tools were actually used after a prediction.
        
        This feedback is used to improve future predictions via
        the adaptive router and RAFT fine-tuning.
        """
        logger.info(
            "feedback_received",
            predicted_count=len(request.predicted_tools),
            used_count=len(request.actually_used),
            success=request.success,
        )
        
        # Store feedback for learning
        feedback_entry = {
            "timestamp": request.timestamp or datetime.utcnow().isoformat(),
            "predicted": request.predicted_tools,
            "used": request.actually_used,
            "success": request.success,
            "query": request.query_used,
        }
        feedback_store.append(feedback_entry)
        
        # If we have an adaptive router, record the usage
        if hasattr(ucp_server, '_router') and hasattr(ucp_server._router, 'record_usage'):
            try:
                # Create a mock prediction for the router
                from ucp.models import RoutingDecision
                prediction = RoutingDecision(
                    selected_tools=request.predicted_tools,
                    scores={t: 1.0 for t in request.predicted_tools},
                    query_used=request.query_used,
                )
                ucp_server._router.record_usage(prediction, request.actually_used)
            except Exception as e:
                logger.warning("feedback_record_error", error=str(e))
        
        return {"status": "accepted", "feedback_id": len(feedback_store)}
    
    @router.get("/feedback/export")
    async def export_feedback() -> dict:
        """Export all collected feedback for training."""
        return {
            "count": len(feedback_store),
            "feedback": feedback_store,
        }
    
    @router.post("/chat", response_model=ChatResponse)
    async def chat_completion(request: ChatRequest) -> ChatResponse:
        """
        Send a chat request through UCP with automatic tool injection.
        
        Note: This requires the UCP server to be configured with a
        downstream LLM provider. If not configured, returns an error.
        """
        # This would integrate with an LLM provider
        # For now, return a placeholder
        return ChatResponse(
            content="Chat completion not yet implemented. Use the clients directly with your LLM provider.",
            tool_calls=None,
            usage=None,
        )
    
    @router.get("/stats")
    async def get_stats() -> dict:
        """Get UCP statistics including prediction accuracy."""
        # Calculate accuracy from feedback
        correct = 0
        total = len(feedback_store)
        
        for fb in feedback_store:
            predicted_set = set(fb["predicted"])
            used_set = set(fb["used"])
            if used_set.issubset(predicted_set):
                correct += 1
        
        accuracy = correct / total if total > 0 else 0.0
        
        # Get router stats if available
        router_stats = {}
        if hasattr(ucp_server, '_router') and hasattr(ucp_server._router, 'get_learning_stats'):
            router_stats = ucp_server._router.get_learning_stats()
        
        return {
            "predictions_made": total,
            "accuracy": accuracy,
            "router_stats": router_stats,
            "tools_indexed": len(ucp_server._connection_pool.all_tools) if ucp_server._connection_pool else 0,
        }
    
    return router


def register_client_endpoints(app, ucp_server) -> None:
    """
    Register client API endpoints on an existing FastAPI app.
    
    Args:
        app: FastAPI application
        ucp_server: UCPServer instance
    """
    router = create_client_router(ucp_server)
    app.include_router(router)
    logger.info("client_endpoints_registered")
