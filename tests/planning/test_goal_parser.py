"""
Tests for Goal Parsing and Clarification Engine.
"""

from planning.goal_parser import GoalParser
from planning.models import Goal


def test_goal_parser_extracts_composite_outputs():
    parser = GoalParser()
    query = "Shivani, research the latest AI agent frameworks, compare them, create a report, make a presentation and prepare a LinkedIn post."
    goal = parser.parse(query)

    assert goal.scope == "composite"
    assert "research_findings" in goal.desired_outputs
    assert "report" in goal.desired_outputs
    assert "presentation" in goal.desired_outputs
    assert "social_post" in goal.desired_outputs
    assert goal.needs_clarification is False


def test_goal_parser_clarification_on_missing_recipient():
    parser = GoalParser()
    query = "Send this email."
    goal = parser.parse(query)

    assert goal.needs_clarification is True
    assert goal.clarification_question is not None
    assert "Who should receive" in goal.clarification_question
    assert len(goal.clarification_options) > 0


def test_goal_parser_clarification_on_missing_transfer_file():
    parser = GoalParser()
    query = "Phone mein transfer karo."
    goal = parser.parse(query)

    assert goal.needs_clarification is True
    assert "Which file" in goal.clarification_question


def test_goal_parser_executes_when_recipient_specified():
    parser = GoalParser()
    query = "Send this email to team@company.com with project updates."
    goal = parser.parse(query)

    assert goal.needs_clarification is False


def test_goal_parser_coding_task():
    parser = GoalParser()
    query = "Shivani, inspect my project, find the login bug, fix it and run tests."
    goal = parser.parse(query)

    assert goal.needs_clarification is False
    assert "code" in goal.desired_outputs
    assert "test_results" in goal.desired_outputs
