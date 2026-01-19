"""
Decision Maker
Analyzes annotations and decides which specialist models to invoke
"""
from typing import List, Dict, Any
from dataclasses import dataclass

from src.models.annotation_model import Annotation


@dataclass
class SpecialistDecision:
    """Decision for which specialist to use"""
    specialist_name: str
    priority: int
    annotations: List[Annotation]
    reason: str


class DecisionMaker:
    """
    Analyzes annotations and routes to appropriate specialist models
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.decision_rules = self._load_decision_rules()
    
    def _load_decision_rules(self) -> Dict[str, Any]:
        """Load decision rules from configuration"""
        return {
            'high_priority_objects': self.config.get('high_priority_objects', [
                'person', 'vehicle', 'object_0', 'object_1'
            ]),
            'confidence_threshold_specialist': self.config.get('confidence_threshold_specialist', 0.7),
            'min_annotations_for_specialist': self.config.get('min_annotations_for_specialist', 1),
        }
    
    def decide(self, annotations: List[Annotation]) -> List[SpecialistDecision]:
        """
        Analyze annotations and decide which specialists to invoke
        
        Args:
            annotations: List of annotations from annotation model
            
        Returns:
            List of specialist decisions
        """
        decisions = []
        
        if not annotations:
            return decisions
        
        # Filter high-confidence annotations
        high_conf_annotations = [
            a for a in annotations 
            if a.confidence >= self.decision_rules['confidence_threshold_specialist']
        ]
        
        # Check for high-priority objects
        high_priority_annotations = [
            a for a in high_conf_annotations
            if any(priority_obj in a.object_type 
                   for priority_obj in self.decision_rules['high_priority_objects'])
        ]
        
        # Decide on CPU specialist for detailed analysis
        if high_priority_annotations:
            decisions.append(SpecialistDecision(
                specialist_name='cpu_detector',
                priority=1,
                annotations=high_priority_annotations,
                reason='High-priority objects detected'
            ))
        elif len(high_conf_annotations) >= self.decision_rules['min_annotations_for_specialist']:
            decisions.append(SpecialistDecision(
                specialist_name='cpu_detector',
                priority=2,
                annotations=high_conf_annotations,
                reason='Multiple objects detected'
            ))
        
        return decisions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get decision maker statistics"""
        return {
            'decision_rules': self.decision_rules
        }
