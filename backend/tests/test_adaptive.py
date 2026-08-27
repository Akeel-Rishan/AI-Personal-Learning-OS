from app.services.knowledge_gap_classifier import KnowledgeGapClassifier

def classify(**values):
    base={"consecutive_incorrect":0,"overall_accuracy":.6,"recent_accuracy":.6,"total_attempts":10,"mastery_trend":"stagnant"}; base.update(values); return KnowledgeGapClassifier().classify_gap(base)

def test_five_consecutive_wrong_is_critical(): assert classify(consecutive_incorrect=5)["gap_severity"]=="critical"
def test_three_consecutive_wrong_is_high(): assert classify(consecutive_incorrect=3)["gap_severity"]=="high"
def test_low_accuracy_is_conceptual(): assert classify(recent_accuracy=.28,overall_accuracy=.28,consecutive_incorrect=3)["gap_type"]=="conceptual"
def test_few_attempts_is_practice_deficit(): assert classify(total_attempts=2)["gap_type"]=="practice_deficit"
def test_inactive_mastered_skill_is_retention_decay(): assert classify(days_inactive=20,current_mastery=.7)["gap_type"]=="retention_decay"
