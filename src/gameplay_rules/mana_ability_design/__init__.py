"""Non-executable mana-ability design; no engine conversion or classification."""
from .classification import (
    ManaAbilityClassificationDesign, ActivatedManaClassificationInputDesign,
    TriggeredManaClassificationInputDesign, ClassificationPersistenceDesign,
    build_classification_design, build_activated_classification_input,
    build_triggered_classification_input, build_classification_persistence,
)
from .behavior import ManaAbilityBehaviorDesign, build_behavior_design
from .controller import ManaAbilityControllerDesign, build_controller_design
from .consumers import ManaAbilityConsumerMatrix, build_consumer_matrix
from .frontier import ManaAbilityProjectionFrontier, build_projection_frontier
from .readiness import ManaAbilityReadiness, build_readiness
from .builder import build_design_package
