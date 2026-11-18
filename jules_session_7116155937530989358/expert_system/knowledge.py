"""
OrbitForge Knowledge Representation Module.
Provides dataclasses and containers for Facts, Conditions, Rules, and KnowledgeBase.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import json
from pathlib import Path


@dataclass
class Fact:
    """Represents an individual domain assertion / fact in the knowledge base."""
    id: str
    category: str  # e.g., 'orbit', 'power', 'comm', 'payload', 'adcs', 'thermal', 'structure', 'regulations', 'launch'
    name: str
    value: Any
    unit: Optional[str] = None
    description: str = ""
    source: str = "knowledge_base"  # 'knowledge_base', 'user', 'deduced', 'default'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fact":
        return cls(
            id=data["id"],
            category=data["category"],
            name=data["name"],
            value=data["value"],
            unit=data.get("unit"),
            description=data.get("description", ""),
            source=data.get("source", "knowledge_base"),
        )


@dataclass
class Condition:
    """Represents a condition clause in a production rule IF statement."""
    fact_name: str
    operator: str  # '==', '!=', '>', '>=', '<', '<=', 'in', 'not_in', 'contains'
    value: Any

    def evaluate(self, current_value: Any) -> bool:
        """Evaluates condition against a provided value."""
        if current_value is None:
            return False
            
        try:
            if self.operator == "==":
                return current_value == self.value
            elif self.operator == "!=":
                return current_value != self.value
            elif self.operator == ">":
                return float(current_value) > float(self.value)
            elif self.operator == ">=":
                return float(current_value) >= float(self.value)
            elif self.operator == "<":
                return float(current_value) < float(self.value)
            elif self.operator == "<=":
                return float(current_value) <= float(self.value)
            elif self.operator == "in":
                return current_value in self.value
            elif self.operator == "not_in":
                return current_value not in self.value
            elif self.operator == "contains":
                return self.value in current_value
            else:
                return False
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_name": self.fact_name,
            "operator": self.operator,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condition":
        return cls(
            fact_name=data["fact_name"],
            operator=data["operator"],
            value=data["value"],
        )


@dataclass
class Action:
    """Represents an action / deduction in a production rule THEN statement."""
    fact_name: str
    value: Any
    category: str
    unit: Optional[str] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_name": self.fact_name,
            "value": self.value,
            "category": self.category,
            "unit": self.unit,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        return cls(
            fact_name=data["fact_name"],
            value=data["value"],
            category=data.get("category", "deduced"),
            unit=data.get("unit"),
            description=data.get("description", ""),
        )


@dataclass
class Rule:
    """Represents an explicit IF-THEN production rule."""
    id: str
    name: str
    category: str  # e.g., 'power', 'comm', 'payload', 'adcs', 'thermal', 'orbit', 'structure', 'propulsion', 'launch'
    salience: int  # Priority for conflict resolution (higher fires first)
    conditions: List[Condition]
    actions: List[Action]
    rationale: str
    reference: Optional[str] = None

    @property
    def specificity(self) -> int:
        """Specificity metric: number of antecedent conditions."""
        return len(self.conditions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "salience": self.salience,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "rationale": self.rationale,
            "reference": self.reference,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            salience=data.get("salience", 50),
            conditions=[Condition.from_dict(c) for c in data["conditions"]],
            actions=[Action.from_dict(a) for a in data["actions"]],
            rationale=data.get("rationale", ""),
            reference=data.get("reference"),
        )


class KnowledgeBase:
    """Container and manager for domain facts and production rules."""

    def __init__(self, facts_path: Optional[str] = None, rules_path: Optional[str] = None):
        self.facts: Dict[str, Fact] = {}
        self.rules: Dict[str, Rule] = {}
        
        if facts_path:
            self.load_facts(facts_path)
        if rules_path:
            self.load_rules(rules_path)

    def load_facts(self, filepath: str) -> None:
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                fact = Fact.from_dict(item)
                self.facts[fact.id] = fact

    def load_rules(self, filepath: str) -> None:
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                rule = Rule.from_dict(item)
                self.rules[rule.id] = rule

    def get_fact(self, fact_id: str) -> Optional[Fact]:
        return self.facts.get(fact_id)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self.rules.get(rule_id)

    def get_facts_by_category(self, category: str) -> List[Fact]:
        return [f for f in self.facts.values() if f.category == category]

    def get_rules_by_category(self, category: str) -> List[Rule]:
        return [r for r in self.rules.values() if r.category == category]

    @property
    def fact_count(self) -> int:
        return len(self.facts)

    @property
    def rule_count(self) -> int:
        return len(self.rules)
