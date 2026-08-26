"""Accurate local MCQ bank used when AI question generation is unavailable."""

from __future__ import annotations

from copy import deepcopy


FALLBACK_QUESTIONS: dict[str, list[dict[str, object]]] = {
    "programming": [
        {
            "question_type": "multiple_choice",
            "question_text": "What is the output of print(type([])) in Python?",
            "options": ["A) <class 'tuple'>", "B) <class 'list'>", "C) <class 'array'>", "D) <class 'dict'>"],
            "correct_answer": "B) <class 'list'>",
            "explanation": "Square brackets create a Python list, and type() reports its class.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which Python collection stores unique values and has no guaranteed positional indexing?",
            "options": ["A) list", "B) tuple", "C) set", "D) string"],
            "correct_answer": "C) set",
            "explanation": "A set stores unique hashable values and is not accessed by numeric position.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What does the expression [x * 2 for x in range(3)] produce?",
            "options": ["A) [0, 1, 2]", "B) [0, 2, 4]", "C) [2, 4, 6]", "D) range(0, 3)"],
            "correct_answer": "B) [0, 2, 4]",
            "explanation": "range(3) yields 0, 1, and 2; each value is multiplied by two.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which Git command creates a new commit from changes already placed in the staging area?",
            "options": ["A) git add", "B) git push", "C) git commit", "D) git fetch"],
            "correct_answer": "C) git commit",
            "explanation": "git commit records the staged snapshot in the local repository history.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Why is a Python dictionary lookup usually faster than searching a list item by item?",
            "options": ["A) Dictionaries use hashing", "B) Dictionaries are always sorted", "C) Lists cannot contain strings", "D) Dictionaries use recursion"],
            "correct_answer": "A) Dictionaries use hashing",
            "explanation": "Hash tables provide average constant-time key lookup, while a linear list search is typically O(n).",
            "difficulty": 3,
        },
    ],
    "mathematics": [
        {
            "question_type": "multiple_choice",
            "question_text": "What is the mean of 2, 4, 6, and 8?",
            "options": ["A) 4", "B) 5", "C) 6", "D) 20"],
            "correct_answer": "B) 5",
            "explanation": "The sum is 20 and 20 divided by 4 observations is 5.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "A fair coin is flipped twice. What is the probability of exactly one head?",
            "options": ["A) 1/4", "B) 1/3", "C) 1/2", "D) 3/4"],
            "correct_answer": "C) 1/2",
            "explanation": "The equally likely outcomes are HH, HT, TH, and TT; two of four have exactly one head.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What is the dot product of vectors [1, 2] and [3, 4]?",
            "options": ["A) 7", "B) 10", "C) 11", "D) [3, 8]"],
            "correct_answer": "C) 11",
            "explanation": "The dot product is 1×3 + 2×4 = 11.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "If f(x) = x², what is f'(3)?",
            "options": ["A) 3", "B) 6", "C) 9", "D) 12"],
            "correct_answer": "B) 6",
            "explanation": "The derivative is 2x, which equals 6 when x is 3.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which statistic is least affected by a single extreme outlier?",
            "options": ["A) Mean", "B) Range", "C) Median", "D) Variance"],
            "correct_answer": "C) Median",
            "explanation": "The median depends on order rather than the magnitude of an extreme value.",
            "difficulty": 2,
        },
    ],
    "data-science": [
        {
            "question_type": "multiple_choice",
            "question_text": "Which pandas method displays the first five rows of a DataFrame by default?",
            "options": ["A) df.top()", "B) df.head()", "C) df.first()", "D) df.sample()"],
            "correct_answer": "B) df.head()",
            "explanation": "DataFrame.head() returns the first five rows unless another count is supplied.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which SQL clause filters rows before grouping?",
            "options": ["A) ORDER BY", "B) HAVING", "C) WHERE", "D) SELECT"],
            "correct_answer": "C) WHERE",
            "explanation": "WHERE filters input rows; HAVING filters groups after aggregation.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which chart is usually best for inspecting the relationship between two continuous variables?",
            "options": ["A) Pie chart", "B) Scatter plot", "C) Stacked bar chart", "D) Treemap"],
            "correct_answer": "B) Scatter plot",
            "explanation": "A scatter plot places paired numeric observations on two axes to reveal association and outliers.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What is the main purpose of a train/test split?",
            "options": ["A) Increase row count", "B) Evaluate generalization on unseen data", "C) Remove all missing values", "D) Sort the target"],
            "correct_answer": "B) Evaluate generalization on unseen data",
            "explanation": "The held-out test set estimates performance on data not used to fit the model.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "A column contains values in meters and centimeters without conversion. This is primarily what kind of data-quality issue?",
            "options": ["A) Duplicate keys", "B) Inconsistent units", "C) Class imbalance", "D) Data leakage"],
            "correct_answer": "B) Inconsistent units",
            "explanation": "Values representing the same measurement must be normalized to a consistent unit before analysis.",
            "difficulty": 2,
        },
    ],
    "ml": [
        {
            "question_type": "multiple_choice",
            "question_text": "Which learning setting uses labeled input-output examples?",
            "options": ["A) Supervised learning", "B) Unsupervised learning", "C) Random search", "D) Clustering only"],
            "correct_answer": "A) Supervised learning",
            "explanation": "Supervised learning fits a mapping from inputs to known target labels or values.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What does overfitting usually look like?",
            "options": ["A) Poor training and test performance", "B) Strong training but poor test performance", "C) Identical predictions for every model", "D) No training data"],
            "correct_answer": "B) Strong training but poor test performance",
            "explanation": "An overfit model memorizes training-specific patterns that do not generalize well.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Precision is calculated using which formula?",
            "options": ["A) TP / (TP + FP)", "B) TP / (TP + FN)", "C) TN / (TN + FP)", "D) (TP + TN) / FP"],
            "correct_answer": "A) TP / (TP + FP)",
            "explanation": "Precision is the fraction of predicted positives that are truly positive.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which technique can reduce overfitting by penalizing large model weights?",
            "options": ["A) Regularization", "B) Data leakage", "C) Label duplication", "D) Removing validation data"],
            "correct_answer": "A) Regularization",
            "explanation": "L1 and L2 regularization add penalties that discourage overly complex parameter values.",
            "difficulty": 2,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "In gradient descent, what does the learning rate control?",
            "options": ["A) Number of features", "B) Step size of parameter updates", "C) Number of labels", "D) Test-set size"],
            "correct_answer": "B) Step size of parameter updates",
            "explanation": "The learning rate scales how far parameters move in the negative-gradient direction each update.",
            "difficulty": 2,
        },
    ],
    "devops": [
        {
            "question_type": "multiple_choice",
            "question_text": "What does a Docker image represent?",
            "options": ["A) A running process only", "B) An immutable template used to create containers", "C) A DNS record", "D) A virtual machine hypervisor"],
            "correct_answer": "B) An immutable template used to create containers",
            "explanation": "Images package filesystem layers and metadata from which containers are started.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which HTTP method is conventionally used to retrieve a resource without changing it?",
            "options": ["A) POST", "B) DELETE", "C) GET", "D) PATCH"],
            "correct_answer": "C) GET",
            "explanation": "GET requests retrieve representations and are defined as safe and idempotent.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "What is the main purpose of a CI pipeline?",
            "options": ["A) Manually rename files", "B) Automatically build and test changes", "C) Replace source control", "D) Store production passwords in code"],
            "correct_answer": "B) Automatically build and test changes",
            "explanation": "Continuous integration validates changes automatically and provides fast feedback.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Why should application secrets be supplied through a secret manager or environment rather than committed to Git?",
            "options": ["A) To make files larger", "B) To prevent credential exposure", "C) To disable encryption", "D) To avoid testing"],
            "correct_answer": "B) To prevent credential exposure",
            "explanation": "Committed credentials persist in repository history and can grant unauthorized access.",
            "difficulty": 1,
        },
        {
            "question_type": "multiple_choice",
            "question_text": "Which signal most directly indicates an API availability problem?",
            "options": ["A) Increased successful response count", "B) Rising 5xx error rate", "C) Smaller source files", "D) More unit tests"],
            "correct_answer": "B) Rising 5xx error rate",
            "explanation": "Server-side 5xx responses indicate the service failed to fulfill requests.",
            "difficulty": 2,
        },
    ],
}


def fallback_questions_for(category: str, count: int, offset: int = 0) -> list[dict[str, object]]:
    """Return copied fallback questions, cycling when more are requested."""

    bank = FALLBACK_QUESTIONS.get(category, FALLBACK_QUESTIONS["programming"])
    return [deepcopy(bank[(offset + index) % len(bank)]) for index in range(max(0, count))]
