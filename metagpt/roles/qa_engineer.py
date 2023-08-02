#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : qa_engineer.py
"""
from metagpt.actions import WriteTest
from metagpt.roles import Role


class QaEngineer(Role):
    """
    Represents a Quality Assurance (QA) Engineer role responsible for writing tests to ensure software quality.
    
    Attributes:
        name (str): Name of the QA engineer.
        profile (str): Role profile.
        goal (str): Goal of the QA engineer.
        constraints (str): Constraints or limitations for the QA engineer.
    """
    
    def __init__(self, 
                 name: str, 
                 profile: str, 
                 goal: str, 
                 constraints: str) -> None:
        """
        Initializes the QaEngineer role with given attributes.
        
        Args:
            name (str): Name of the QA engineer.
            profile (str): Role profile.
            goal (str): Goal of the QA engineer.
            constraints (str): Constraints or limitations for the QA engineer.
        """
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteTest])