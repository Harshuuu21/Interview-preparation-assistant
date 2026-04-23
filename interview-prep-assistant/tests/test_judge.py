import pytest
from unittest.mock import patch
from agents import judge
from models.feedback import Feedback

@patch('agents.judge.get_model')
def test_judge_execute_error(mock_get_model):
    # Mock the LLM to throw an exception
    mock_model = mock_get_model.return_value
    mock_model.generate_content.side_effect = Exception("API Error")
    
    # Should fall back to generic error feedback
    result = judge.execute("Q", "A", "Role", "Company", 1)
    assert isinstance(result, Feedback)
    assert result.score == 0
    assert result.gaps == ["Error evaluating answer"]
