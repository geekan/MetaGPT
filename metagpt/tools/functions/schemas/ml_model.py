import pandas as pd

from metagpt.tools.functions.schemas.base import tool_field, ToolSchema


class LogisticRegressionClassification(ToolSchema):
    """Logistic Regression (aka logit, MaxEnt) classifier"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    label: str = tool_field(description="target name")
    test_size: float = tool_field(description="The proportion of the test set to all the data", default=0.2)
    penalty: str = tool_field(description="Specify the norm of the penalty", default="l2")
    dual: bool = tool_field(description="Dual (constrained) or primal (regularized) formulation", default="l2")


class RandomForestClassification(ToolSchema):
    """random forest is a meta estimator that fits a number of decision tree classifiers on various sub-samples of the dataset and uses averaging to improve the predictive accuracy and control over-fitting"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    label: str = tool_field(description="target name")
    test_size: float = tool_field(description="The proportion of the test set to all the data", default=0.2)
    n_estimators: int = tool_field(description="The number of trees in the forest", default=100)
    criterion: str = tool_field(description="The function to measure the quality of a split", default="gini")


class GradientBoostingClassification(ToolSchema):
    """Gradient Boosting for classification.This algorithm builds an additive model in a forward stage-wise fashion"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    label: str = tool_field(description="target name")
    test_size: float = tool_field(description="The proportion of the test set to all the data", default=0.2)
    n_estimators: int = tool_field(description="The number of boosting stages to perform", default=100)
    learning_rate: float = tool_field(description="Learning rate shrinks the contribution of each tree by learning_rate", default=0.1)


class LinearRegressionRegression(ToolSchema):
    """Ordinary least squares Linear Regression."""
    df: pd.DataFrame = tool_field(description="input dataframe")
    label: str = tool_field(description="target name")
    test_size: float = tool_field(description="The proportion of the test set to all the data", default=0.2)


class RandomForestRegression(ToolSchema):
    """random forest is a meta estimator that fits a number of decision tree on various sub-samples of the dataset and uses averaging to improve the predictive accuracy and control over-fitting"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    label: str = tool_field(description="target name")
    test_size: float = tool_field(description="The proportion of the test set to all the data", default=0.2)
    n_estimators: int = tool_field(description="The number of trees in the forest", default=100)
    criterion: str = tool_field(description="The function to measure the quality of a split", default="squared_error")


class GradientBoostingRegression(ToolSchema):
    """Gradient Boosting for regression.This estimator builds an additive model in a forward stage-wise fashion"""
    df: pd.DataFrame = tool_field(description="input dataframe")
    label: str = tool_field(description="target name")
    test_size: float = tool_field(description="The proportion of the test set to all the data", default=0.2)
    n_estimators: int = tool_field(description="The number of boosting stages to perform", default=100)
    learning_rate: float = tool_field(description="Learning rate shrinks the contribution of each tree by learning_rate", default=0.1)
