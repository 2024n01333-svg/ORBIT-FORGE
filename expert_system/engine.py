"""
OrbitForge Rule-Based Inference Engine.

Provides:
- WorkingMemory: Fact store with provenance (user, deduced, kb, default), confidence, and accessors.
- InferenceEngine:
    * Forward Chaining: Match-Resolve-Act cycle until quiescence or max iterations.
    * Conflict Resolution Strategy:
        1. Salience (Priority) - higher salience fires first
        2. Specificity - rules with more condition clauses fire first
        3. Recency / Definition Order - earlier defined rules break remaining ties
    * Backward Chaining: Goal-directed recursive reasoning to verify hypotheses and detect missing facts.
    * Execution Tracer: Full audit trail of evaluation, activations, firings, deductions, and explanations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import copy

from expert_system.knowledge import KnowledgeBase, Rule, Fact, Condition, Action


@dataclass
class TraceStep:
    """Represents a discrete step in the inference reasoning trace."""
    step_number: int
    rule_id: str
    rule_name: str
    category: str
    salience: int
    matched_conditions: List[Dict[str, Any]]
    deduced_actions: List[Dict[str, Any]]
    rationale: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3])


@dataclass
class WorkingMemory:
    """Fact base holding active assertions with provenance and audit metadata."""
    facts: Dict[str, Fact] = field(default_factory=dict)

    def set(self, name: str, value: Any, category: str = "general", unit: Optional[str] = None,
            description: str = "", source: str = "user") -> Fact:
        fact_id = f"wm_{name}"
        fact = Fact(
            id=fact_id,
            category=category,
            name=name,
            value=value,
            unit=unit,
            description=description,
            source=source
        )
        self.facts[name] = fact
        return fact

    def get_value(self, name: str, default: Any = None) -> Any:
        fact = self.facts.get(name)
        return fact.value if fact is not None else default

    def get_fact(self, name: str) -> Optional[Fact]:
        return self.facts.get(name)

    def has(self, name: str) -> bool:
        return name in self.facts

    def to_dict(self) -> Dict[str, Any]:
        return {name: f.value for name, f in self.facts.items()}

    def clear(self) -> None:
        self.facts.clear()

    def clone(self) -> "WorkingMemory":
        new_wm = WorkingMemory()
        for k, v in self.facts.items():
            new_wm.facts[k] = Fact.from_dict(v.to_dict())
        return new_wm


class InferenceEngine:
    """Genuine Rule-Based Expert System Inference Engine supporting Forward and Backward Chaining."""

    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
        self.working_memory = WorkingMemory()
        self.trace: List[TraceStep] = []
        self.fired_rules: List[str] = []

    def reset(self) -> None:
        """Resets working memory and execution trace."""
        self.working_memory.clear()
        self.trace.clear()
        self.fired_rules.clear()

    # =========================================================================
    # CONFLICT RESOLUTION
    # =========================================================================
    def resolve_conflicts(self, conflict_set: List[Rule]) -> List[Rule]:
        """
        Sorts the conflict set according to the documented multi-tier strategy:
        1. Salience (Priority) - Descending (higher first)
        2. Specificity (Condition Count) - Descending (more specific first)
        3. Rule ID / Stable Definition Order - Ascending
        """
        return sorted(
            conflict_set,
            key=lambda r: (-r.salience, -r.specificity, r.id)
        )

    # =========================================================================
    # FORWARD CHAINING
    # =========================================================================
    def evaluate_rule(self, rule: Rule, wm: WorkingMemory) -> Tuple[bool, List[Dict[str, Any]]]:
        """Evaluates whether all conditions of a rule are satisfied in working memory."""
        matched_details = []
        for cond in rule.conditions:
            current_val = wm.get_value(cond.fact_name)
            is_satisfied = cond.evaluate(current_val)
            matched_details.append({
                "fact_name": cond.fact_name,
                "required_op": cond.operator,
                "required_val": cond.value,
                "current_val": current_val,
                "satisfied": is_satisfied
            })
            if not is_satisfied:
                return False, matched_details
        return True, matched_details

    def forward_chain(self, max_iterations: int = 100) -> Dict[str, Any]:
        """
        Executes Forward Chaining Match-Resolve-Act cycle until quiescence.
        Returns a summary report of the reasoning process.
        """
        iteration = 0
        rules_fired_this_run: Set[str] = set()

        while iteration < max_iterations:
            iteration += 1
            conflict_set: List[Rule] = []

            # 1. Match Phase: Find all eligible rules whose conditions match WM and have not fired
            for rule in self.kb.rules.values():
                if rule.id in rules_fired_this_run:
                    continue
                satisfied, _ = self.evaluate_rule(rule, self.working_memory)
                if satisfied:
                    conflict_set.append(rule)

            # Quiescence check
            if not conflict_set:
                break

            # 2. Resolve Phase: Apply conflict resolution strategy
            resolved_set = self.resolve_conflicts(conflict_set)
            rule_to_fire = resolved_set[0]  # Take top priority rule

            # 3. Act Phase: Execute actions of the selected rule
            satisfied, matched_details = self.evaluate_rule(rule_to_fire, self.working_memory)
            deduced_details = []
            
            for action in rule_to_fire.actions:
                self.working_memory.set(
                    name=action.fact_name,
                    value=action.value,
                    category=action.category,
                    unit=action.unit,
                    description=action.description,
                    source=f"rule:{rule_to_fire.id}"
                )
                deduced_details.append(action.to_dict())

            rules_fired_this_run.add(rule_to_fire.id)
            self.fired_rules.append(rule_to_fire.id)

            # Record Trace Step
            step = TraceStep(
                step_number=len(self.trace) + 1,
                rule_id=rule_to_fire.id,
                rule_name=rule_to_fire.name,
                category=rule_to_fire.category,
                salience=rule_to_fire.salience,
                matched_conditions=matched_details,
                deduced_actions=deduced_details,
                rationale=rule_to_fire.rationale
            )
            self.trace.append(step)

        return {
            "iterations": iteration,
            "fired_count": len(rules_fired_this_run),
            "fired_rules": list(rules_fired_this_run),
            "trace_length": len(self.trace),
            "quiescence_reached": len(conflict_set) == 0
        }

    # =========================================================================
    # BACKWARD CHAINING
    # =========================================================================
    def backward_chain(self, target_fact: str, target_value: Any = None,
                       visited_goals: Optional[Set[str]] = None,
                       depth: int = 0, max_depth: int = 15) -> Dict[str, Any]:
        """
        Goal-directed Backward Chaining.
        Evaluates whether a target hypothesis is true or can be proven from the rules.
        Identifies missing facts needed to prove the goal.
        """
        if visited_goals is None:
            visited_goals = set()

        goal_key = f"{target_fact}=={target_value}" if target_value is not None else target_fact
        if goal_key in visited_goals or depth > max_depth:
            return {
                "success": False,
                "reason": "Circular dependency or maximum search depth exceeded",
                "target_fact": target_fact,
                "target_value": target_value,
                "subproofs": [],
                "missing_facts": []
            }
        visited_goals.add(goal_key)

        # 1. Check if goal is already asserted in working memory
        if self.working_memory.has(target_fact):
            curr_val = self.working_memory.get_value(target_fact)
            if target_value is None or curr_val == target_value:
                return {
                    "success": True,
                    "target_fact": target_fact,
                    "target_value": target_value,
                    "source": "working_memory",
                    "proven_value": curr_val,
                    "subproofs": [],
                    "missing_facts": []
                }
            else:
                return {
                    "success": False,
                    "target_fact": target_fact,
                    "target_value": target_value,
                    "source": "working_memory_contradiction",
                    "proven_value": curr_val,
                    "reason": f"Working memory has value '{curr_val}', contradictory to target '{target_value}'",
                    "subproofs": [],
                    "missing_facts": []
                }

        # 2. Search for rules that conclude this target fact
        candidate_rules = []
        for rule in self.kb.rules.values():
            for action in rule.actions:
                if action.fact_name == target_fact:
                    if target_value is None or action.value == target_value:
                        candidate_rules.append(rule)
                        break

        if not candidate_rules:
            # Target is an atomic fact or unsupported deduction
            return {
                "success": False,
                "target_fact": target_fact,
                "target_value": target_value,
                "source": "unsupported_hypothesis",
                "reason": "No rule derives this fact; must be provided by user",
                "missing_facts": [target_fact],
                "subproofs": []
            }

        # Resolve candidates by salience and specificity
        candidate_rules = self.resolve_conflicts(candidate_rules)
        missing_facts_accumulator = set()
        subproofs = []

        for rule in candidate_rules:
            all_subgoals_proven = True
            rule_subproofs = []

            for cond in rule.conditions:
                # Recursively evaluate condition as a subgoal
                cond_result = self.backward_chain(
                    target_fact=cond.fact_name,
                    target_value=cond.value if cond.operator == "==" else None,
                    visited_goals=visited_goals.copy(),
                    depth=depth + 1,
                    max_depth=max_depth
                )
                rule_subproofs.append({"condition": cond.to_dict(), "proof": cond_result})

                if not cond_result["success"]:
                    all_subgoals_proven = False
                    missing_facts_accumulator.add(cond.fact_name)
                    for mf in cond_result.get("missing_facts", []):
                        missing_facts_accumulator.add(mf)
                    break

            if all_subgoals_proven:
                # Successfully proved goal via this rule!
                return {
                    "success": True,
                    "target_fact": target_fact,
                    "target_value": target_value,
                    "source": f"rule:{rule.id}",
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "rationale": rule.rationale,
                    "subproofs": rule_subproofs,
                    "missing_facts": []
                }

            subproofs.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "subgoals": rule_subproofs
            })

        return {
            "success": False,
            "target_fact": target_fact,
            "target_value": target_value,
            "reason": "Could not satisfy antecedent conditions for any candidate rule",
            "candidate_rules_evaluated": [r.id for r in candidate_rules],
            "missing_facts": sorted(list(missing_facts_accumulator)),
            "subproofs": subproofs
        }

    # =========================================================================
    # EXPLANATION FACILITY
    # =========================================================================
    def explain_fact(self, fact_name: str) -> Dict[str, Any]:
        """Provides 'Why / How' explanation for a given fact in working memory."""
        fact = self.working_memory.get_fact(fact_name)
        if not fact:
            return {"exists": False, "message": f"Fact '{fact_name}' is not currently asserted in working memory."}

        if fact.source.startswith("rule:"):
            rule_id = fact.source.split("rule:")[1]
            rule = self.kb.get_rule(rule_id)
            trace_entry = next((t for t in self.trace if t.rule_id == rule_id), None)

            return {
                "exists": True,
                "name": fact.name,
                "value": fact.value,
                "unit": fact.unit,
                "source_type": "deduced_by_rule",
                "rule_id": rule_id,
                "rule_name": rule.name if rule else "Unknown",
                "salience": rule.salience if rule else None,
                "rationale": rule.rationale if rule else "",
                "matched_conditions": trace_entry.matched_conditions if trace_entry else [],
                "explanation_text": f"Deduction was made because Rule '{rule.name if rule else rule_id}' fired based on antecedent parameters: {rule.rationale if rule else ''}"
            }
        else:
            return {
                "exists": True,
                "name": fact.name,
                "value": fact.value,
                "unit": fact.unit,
                "source_type": fact.source,
                "explanation_text": f"This parameter was provided directly by the user or default configuration specification."
            }
