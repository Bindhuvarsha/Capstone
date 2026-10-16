"""
MigrateIQ LangGraph Workflow Assembly
Coordinates Planner -> Retriever / Scanner -> Scorer -> Responder flow.
"""

from app.agent.state import AgentState
from app.agent.nodes import (
    planner_node,
    retriever_node,
    scanner_node,
    scorer_node,
    responder_node
)

class MigrateIQWorkflow:
    def __init__(self):
        self._has_langgraph = False
        try:
            from langgraph.graph import StateGraph, END
            self._has_langgraph = True
            self.graph = self._build_langgraph()
        except ImportError:
            self._has_langgraph = False

    def _build_langgraph(self):
        """Constructs LangGraph StateGraph if langgraph library is installed."""
        from langgraph.graph import StateGraph, END

        workflow = StateGraph(AgentState)
        workflow.add_node("planner", planner_node)
        workflow.add_node("retriever", retriever_node)
        workflow.add_node("scanner", scanner_node)
        workflow.add_node("scorer", scorer_node)
        workflow.add_node("responder", responder_node)

        workflow.set_entry_point("planner")

        def route_after_planner(state: AgentState):
            if not state.guardrail_passed:
                return "responder"
            if state.query_type == "CODE_SCAN":
                return "scanner"
            return "retriever"

        workflow.add_conditional_edges(
            "planner",
            route_after_planner,
            {
                "responder": "responder",
                "scanner": "scanner",
                "retriever": "retriever"
            }
        )

        workflow.add_edge("scanner", "scorer")
        workflow.add_edge("scorer", "retriever")
        workflow.add_edge("retriever", "responder")
        workflow.add_edge("responder", END)

        return workflow.compile()

    def run(self, initial_state: AgentState) -> AgentState:
        """Executes the workflow graph."""
        if self._has_langgraph:
            try:
                result = self.graph.invoke(initial_state)
                if isinstance(result, dict):
                    return AgentState(**result)
                return result
            except Exception:
                pass

        # Robust, high-speed native state runner
        state = initial_state
        state = planner_node(state)

        if not state.guardrail_passed:
            return responder_node(state)

        if state.query_type == "CODE_SCAN":
            state = scanner_node(state)
            state = scorer_node(state)
            state = retriever_node(state)
            state = responder_node(state)
        else:
            state = retriever_node(state)
            state = responder_node(state)

        return state

agent_workflow = MigrateIQWorkflow()
