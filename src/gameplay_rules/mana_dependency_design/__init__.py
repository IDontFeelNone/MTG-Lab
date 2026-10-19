"""Design-only mana dependency grouping, with no gameplay execution path."""
from .classification import ManaClassificationDependencyDesign, build_classification_design
from .activated import ActivatedAbilityDependencyDesign, build_activated_design
from .triggered import TriggeredAbilityDependencyDesign, build_triggered_design
from .stack import StackExceptionDependencyDesign, build_stack_design
from .consumers import ManaDependencyConsumerMatrix, build_consumer_matrix
from .grouping import ManaDependencyGrouping, build_dependency_grouping
from .readiness import ManaDependencyReadiness, build_readiness
from .builder import build_design_package
