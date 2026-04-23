import pytest
from validation.gate import validate_researcher, validate_questions
from models.session import ResearcherOutput, HistoricalQuestionsOutput, GeneratedQuestionsOutput
from models.question import Question

def test_validate_researcher_success():
    out = ResearcherOutput(culture=["a"], recentNews=["b"], roleExpectations=[])
    assert validate_researcher(out) == True

def test_validate_researcher_failure():
    out = ResearcherOutput(culture=["a"], recentNews=[], roleExpectations=[])
    assert validate_researcher(out) == False

def test_validate_questions_success():
    hist = HistoricalQuestionsOutput(
        behavioural=[Question(text="Q1"), Question(text="Q2")],
        technical=[],
        coding=[]
    )
    gen = GeneratedQuestionsOutput(
        generated=[Question(text="Q3"), Question(text="Q4"), Question(text="Q5")],
        rationale=[]
    )
    is_valid, final_qs, err = validate_questions(hist, gen)
    assert is_valid == True
    assert len(final_qs) == 5

def test_validate_questions_duplicate():
    hist = HistoricalQuestionsOutput(
        behavioural=[Question(text="Tell me about yourself"), Question(text="Q2")],
        technical=[],
        coding=[]
    )
    gen = GeneratedQuestionsOutput(
        generated=[Question(text="Tell me a bit about yourself."), Question(text="Q4"), Question(text="Q5")],
        rationale=[]
    )
    is_valid, final_qs, err = validate_questions(hist, gen)
    # The duplicate should be dropped, leaving 4 total questions
    assert is_valid == False
    assert len(final_qs) == 0 # returns empty list on failure
