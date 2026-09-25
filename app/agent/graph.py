"""LangGraph workflow definition for TechNova Enterprise Policy Assistant."""

import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.nodes import (
    classify_intent_node,
    policy_question_node,
    leave_balance_node,
    employee_info_node,
    leave_status_node,
    leave_request_node,
    general_node
)

logger = logging.getLogger(__name__)


def route_intent(state: AgentState) -> str:
    """Routing function that determines the next node based on classified intent."""
    intent = state.get("intent", "general_question")
    logger.info(f"LangGraph routing on intent: {intent}")

    if intent == "policy_question":
        return "policy_handler"
    elif intent == "leave_balance":
        return "balance_handler"
    elif intent == "leave_request":
        return "leave_request_handler"
    elif intent == "leave_status":
        return "status_handler"
    elif intent == "employee_info":
        return "employee_handler"
    else:
        return "general_handler"


def build_agent_graph():
    """Build and compile the unified single-agent LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Register workflow nodes
    workflow.add_node("classifier", classify_intent_node)
    workflow.add_node("policy_handler", policy_question_node)
    workflow.add_node("balance_handler", leave_balance_node)
    workflow.add_node("employee_handler", employee_info_node)
    workflow.add_node("status_handler", leave_status_node)
    workflow.add_node("leave_request_handler", leave_request_node)
    workflow.add_node("general_handler", general_node)

    # Edge from START to classifier
    workflow.add_edge(START, "classifier")

    # Conditional branching from classifier
    workflow.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "policy_handler": "policy_handler",
            "balance_handler": "balance_handler",
            "leave_request_handler": "leave_request_handler",
            "status_handler": "status_handler",
            "employee_handler": "employee_handler",
            "general_handler": "general_handler",
        }
    )

    # End transitions from leaf nodes
    workflow.add_edge("policy_handler", END)
    workflow.add_edge("balance_handler", END)
    workflow.add_edge("leave_request_handler", END)
    workflow.add_edge("status_handler", END)
    workflow.add_edge("employee_handler", END)
    workflow.add_edge("general_handler", END)

    return workflow.compile()


# Compile reusable graph instance
agent_graph = build_agent_graph()


def run_agent_workflow(
    query: str,
    employee_id: str = "EMP001",
    confirmed: bool = False,
    extra_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute the LangGraph agent workflow for a given query and employee session.
    
    Args:
        query: User message or question.
        employee_id: Logged in employee ID.
        confirmed: Boolean confirmation flag for pending requests.
        extra_state: Optional prior state (e.g. pending leave details).
        
    Returns:
        Final resulting state dictionary.
    """
    initial_state: AgentState = {
        "user_query": query,
        "employee_id": employee_id,
        "confirmed": confirmed,
        "confirmation_required": False,
        "retrieved_context": [],
        "sources": [],
        "actions": [],
        "final_response": ""
    }

    if extra_state:
        for k, v in extra_state.items():
            if v is not None:
                initial_state[k] = v

    result = agent_graph.invoke(initial_state)
    return result
