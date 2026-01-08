"""
LangGraph Integration - State Machine Orchestration.

Implements the cyclic graph architecture from the design docs:
1. Analyze Context -> Predict Tools -> Inject Context -> Model Inference -> Tool Execution -> (cycle)

This module wraps UCP's components in a LangGraph StateGraph for
proper state management, checkpointing, and human-in-the-loop support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, Annotated
from uuid import UUID

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages

from ucp.models import Message, RoutingDecision, SessionState, ToolCallResult
from ucp.router import Router
from ucp.session import SessionManager
from ucp.tool_zoo import ToolZoo
from ucp.connection_pool import ConnectionPool


class UCPGraphState(TypedDict):
    """
    State schema for the UCP LangGraph.

    This is the "RAM" that flows through the graph nodes.
    """

    # Conversation messages (LangGraph's add_messages reducer)
    messages: Annotated[list[dict], add_messages]

    # Currently active tools (injected into context)
    active_tools: list[str]

    # Last routing decision
    routing_decision: dict | None

    # Pending tool call (if any)
    pending_tool_call: dict | None

    # Tool execution result
    tool_result: dict | None

    # Session ID for persistence
    session_id: str

    # Control flow
    next_action: Literal["route", "respond", "execute", "end"]


class UCPGraph:
    """
    LangGraph-based orchestration for UCP.

    Provides proper state machine semantics with checkpointing.
    """

    def __init__(
        self,
        tool_zoo: ToolZoo,
        router: Router,
        connection_pool: ConnectionPool,
        session_manager: SessionManager,
        checkpoint_path: str = "./data/checkpoints.db",
    ) -> None:
        self.tool_zoo = tool_zoo
        self.router = router
        self.connection_pool = connection_pool
        self.session_manager = session_manager

        # Set up checkpointer for persistence
        self.checkpointer = SqliteSaver.from_conn_string(checkpoint_path)

        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=self.checkpointer)

    def _build_graph(self) -> StateGraph:
        """Construct the UCP state graph."""
        graph = StateGraph(UCPGraphState)

        # Add nodes
        graph.add_node("analyze", self._node_analyze)
        graph.add_node("route", self._node_route)
        graph.add_node("execute", self._node_execute)
        graph.add_node("respond", self._node_respond)

        # Add edges
        graph.set_entry_point("analyze")

        graph.add_conditional_edges(
            "analyze",
            self._should_route,
            {
                "route": "route",
                "respond": "respond",
            }
        )

        graph.add_edge("route", "respond")

        graph.add_conditional_edges(
            "respond",
            self._check_tool_call,
            {
                "execute": "execute",
                "end": END,
            }
        )

        graph.add_edge("execute", "analyze")  # Cycle back

        return graph

    async def _node_analyze(self, state: UCPGraphState) -> UCPGraphState:
        """
        Analyze the current context to determine next action.

        This node looks at the conversation and decides if we need
        to re-route (update active tools) or just respond.
        """
        messages = state.get("messages", [])

        if not messages:
            return {**state, "next_action": "respond"}

        # Get the last message
        last_msg = messages[-1] if messages else None

        # Check if this is a tool result
        if last_msg and last_msg.get("role") == "tool":
            # Tool executed - cycle back to check for more
            return {**state, "next_action": "route", "tool_result": None}

        # Check if context has shifted
        current_tools = set(state.get("active_tools", []))

        # Build session state for routing
        session = SessionState(session_id=UUID(state["session_id"]))
        for msg in messages[-10:]:  # Last 10 messages
            session.add_message(msg.get("role", "user"), msg.get("content", ""))

        # Quick check: do we need new tools?
        context = session.get_context_for_routing()
        domains = self.router.detect_domain(context)

        # If domain changed significantly, re-route
        if domains and not current_tools:
            return {**state, "next_action": "route"}

        return {**state, "next_action": "respond"}

    async def _node_route(self, state: UCPGraphState) -> UCPGraphState:
        """
        Route to select relevant tools for the current context.

        This is the core UCP operation - predicting which tools to inject.
        """
        messages = state.get("messages", [])

        # Build session state
        session = SessionState(session_id=UUID(state["session_id"]))
        for msg in messages[-10:]:
            session.add_message(msg.get("role", "user"), msg.get("content", ""))

        # Get current message for routing
        current_msg = messages[-1].get("content") if messages else None

        # Perform routing
        decision = await self.router.route(session, current_msg)

        return {
            **state,
            "active_tools": decision.selected_tools,
            "routing_decision": {
                "selected_tools": decision.selected_tools,
                "scores": decision.scores,
                "reasoning": decision.reasoning,
            },
        }

    async def _node_execute(self, state: UCPGraphState) -> UCPGraphState:
        """
        Execute a pending tool call.

        Routes the call to the appropriate downstream server.
        """
        pending = state.get("pending_tool_call")

        if not pending:
            return {**state, "tool_result": None}

        tool_name = pending.get("name", "")
        arguments = pending.get("arguments", {})

        try:
            result = await self.connection_pool.call_tool(tool_name, arguments)

            tool_result = {
                "tool_name": tool_name,
                "success": True,
                "result": result,
            }

            # Add tool result as a message
            new_messages = state.get("messages", []) + [
                {"role": "tool", "content": str(result), "tool_call_id": pending.get("id")}
            ]

            return {
                **state,
                "messages": new_messages,
                "tool_result": tool_result,
                "pending_tool_call": None,
            }

        except Exception as e:
            tool_result = {
                "tool_name": tool_name,
                "success": False,
                "error": str(e),
            }

            new_messages = state.get("messages", []) + [
                {"role": "tool", "content": f"Error: {e}", "tool_call_id": pending.get("id")}
            ]

            return {
                **state,
                "messages": new_messages,
                "tool_result": tool_result,
                "pending_tool_call": None,
            }

    async def _node_respond(self, state: UCPGraphState) -> UCPGraphState:
        """
        Prepare response state.

        This node doesn't generate the response (that's the LLM's job),
        but it prepares the state with the active tools.
        """
        # The actual LLM response happens outside the graph
        # This node just ensures state is ready
        return state

    def _should_route(self, state: UCPGraphState) -> str:
        """Conditional edge: should we route to update tools?"""
        return state.get("next_action", "respond")

    def _check_tool_call(self, state: UCPGraphState) -> str:
        """Conditional edge: is there a tool call to execute?"""
        if state.get("pending_tool_call"):
            return "execute"
        return "end"

    async def process_message(
        self,
        message: str,
        session_id: str,
        thread_id: str | None = None,
    ) -> dict:
        """
        Process a user message through the graph.

        Args:
            message: The user's message
            session_id: UCP session ID
            thread_id: Optional thread ID for checkpointing

        Returns:
            The final state including active tools
        """
        thread_id = thread_id or session_id

        initial_state: UCPGraphState = {
            "messages": [{"role": "user", "content": message}],
            "active_tools": [],
            "routing_decision": None,
            "pending_tool_call": None,
            "tool_result": None,
            "session_id": session_id,
            "next_action": "route",
        }

        config = {"configurable": {"thread_id": thread_id}}

        # Run the graph
        final_state = await self.app.ainvoke(initial_state, config)

        return final_state

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        session_id: str,
        thread_id: str | None = None,
    ) -> dict:
        """
        Execute a tool call within the graph.

        This is called when the LLM decides to use a tool.
        """
        thread_id = thread_id or session_id

        # Get current state from checkpoint
        config = {"configurable": {"thread_id": thread_id}}

        # Create state with pending tool call
        state: UCPGraphState = {
            "messages": [],
            "active_tools": [],
            "routing_decision": None,
            "pending_tool_call": {
                "name": tool_name,
                "arguments": arguments,
                "id": f"call_{tool_name}",
            },
            "tool_result": None,
            "session_id": session_id,
            "next_action": "execute",
        }

        # Run from execute node
        final_state = await self.app.ainvoke(state, config)

        return final_state

    def get_active_tools(self, thread_id: str) -> list[str]:
        """Get the currently active tools for a thread."""
        config = {"configurable": {"thread_id": thread_id}}

        try:
            state = self.app.get_state(config)
            if state and state.values:
                return state.values.get("active_tools", [])
        except Exception:
            pass

        return []


def create_ucp_graph(
    tool_zoo: ToolZoo,
    router: Router,
    connection_pool: ConnectionPool,
    session_manager: SessionManager,
    checkpoint_path: str = "./data/checkpoints.db",
) -> UCPGraph:
    """
    Factory function to create a UCP graph.

    This is the recommended way to instantiate the graph.
    """
    return UCPGraph(
        tool_zoo=tool_zoo,
        router=router,
        connection_pool=connection_pool,
        session_manager=session_manager,
        checkpoint_path=checkpoint_path,
    )
