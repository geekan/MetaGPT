from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier


from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor

from metagpt.tools.functions import registry
from metagpt.tools.functions.schemas.ml_model import *


#########
## 分类 ##
#########


@registry.register("classification_model", LogisticRegressionClassification)
def logistic_regression_classification(df, label, test_size=0.2, penalty='l2', dual=False):
    nonnumeric_columns = [col for col in df if df[col].dtype == 'object']
    for col in nonnumeric_columns:
        df[col] = LabelEncoder().fit_transform(df[col])
    df = df.fillna(0)

    features = [col for col in df if col != label]
    x, y = df[features], df[label]
    tr_x, te_x, tr_y, te_y = train_test_split(x, y, test_size=test_size, random_state=1)

    model = LogisticRegression(penalty=penalty, dual=dual)
    model.fit(tr_x, tr_y, )
    te_pred_prob = model.predict_proba(te_x)

    res = {
        'te_pred_prob': te_pred_prob
    }
    return res


@registry.register("classification_model", RandomForestClassification)
def random_forest_classification(df, label, test_size=0.2, n_estimators=100, criterion='gini'):
    nonnumeric_columns = [col for col in df if df[col].dtype == 'object']
    for col in nonnumeric_columns:
        df[col] = LabelEncoder().fit_transform(df[col])
    df = df.fillna(0)

    features = [col for col in df if col != label]
    x, y = df[features], df[label]
    tr_x, te_x, tr_y, te_y = train_test_split(x, y, test_size=test_size, random_state=1)
    model = RandomForestClassifier(n_estimators=n_estimators, criterion=criterion)
    model.fit(tr_x, tr_y, )
    te_pred_prob = model.predict_proba(te_x)

    res = {
        'te_pred_prob': te_pred_prob
    }
    return res


@registry.register("classification_model", GradientBoostingClassification)
def gradient_boosting_classification(df, label, test_size=0.2, n_estimators=100, learning_rate=0.1):
    nonnumeric_columns = [col for col in df if df[col].dtype == 'object']
    for col in nonnumeric_columns:
        df[col] = LabelEncoder().fit_transform(df[col])
    df = df.fillna(0)

    features = [col for col in df if col != label]
    x, y = df[features], df[label]
    tr_x, te_x, tr_y, te_y = train_test_split(x, y, test_size=test_size, random_state=1)
    model = GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate)
    model.fit(tr_x, tr_y, )
    te_pred_prob = model.predict_proba(te_x)

    res = {
        'te_pred_prob': te_pred_prob
    }
    return res



#########
## 回归 ##
#########


@registry.register("regression_model", LinearRegressionRegression)
def linear_regression(df, label, test_size=0.2, ):
    nonnumeric_columns = [col for col in df if df[col].dtype == 'object']
    for col in nonnumeric_columns:
        df[col] = LabelEncoder().fit_transform(df[col])
    df = df.fillna(0)

    features = [col for col in df if col != label]
    x, y = df[features], df[label]
    tr_x, te_x, tr_y, te_y = train_test_split(x, y, test_size=test_size, random_state=1)

    model = LinearRegression()
    model.fit(tr_x, tr_y, )
    te_pred_prob = model.predict(te_x)

    res = {
        'te_pred_prob': te_pred_prob
    }
    return res


@registry.register("regression_model", RandomForestRegression)
def random_forest_regression(df, label, test_size=0.2, n_estimators=100, criterion='squared_error'):
    nonnumeric_columns = [col for col in df if df[col].dtype == 'object']
    for col in nonnumeric_columns:
        df[col] = LabelEncoder().fit_transform(df[col])
    df = df.fillna(0)

    features = [col for col in df if col != label]
    x, y = df[features], df[label]
    tr_x, te_x, tr_y, te_y = train_test_split(x, y, test_size=test_size, random_state=1)
    model = RandomForestRegressor(n_estimators=n_estimators, criterion=criterion)
    model.fit(tr_x, tr_y, )
    te_pred_prob = model.predict(te_x)

    res = {
        'te_pred_prob': te_pred_prob
    }
    return res


@registry.register("regression_model", GradientBoostingRegression)
def gradient_boosting_regression(df, label, test_size=0.2, n_estimators=100, learning_rate=0.1):
    nonnumeric_columns = [col for col in df if df[col].dtype == 'object']
    for col in nonnumeric_columns:
        df[col] = LabelEncoder().fit_transform(df[col])
    df = df.fillna(0)

    features = [col for col in df if col != label]
    x, y = df[features], df[label]
    tr_x, te_x, tr_y, te_y = train_test_split(x, y, test_size=test_size, random_state=1)
    model = GradientBoostingRegressor(n_estimators=n_estimators, learning_rate=learning_rate)
    model.fit(tr_x, tr_y, )
    te_pred_prob = model.predict(te_x)

    res = {
        'te_pred_prob': te_pred_prob
    }
    return res


if __name__ == '__main__':
    def run():
        from sklearn.datasets import load_iris
        loader = load_iris(as_frame=True)
        df = loader['data']
        df['target'] = loader['target']

        df[df.columns[0]] = df[df.columns[0]].astype(str)
        df[df.columns[1]] = df[df.columns[1]].astype(int)
        df['target'] = df['target'].astype(str)

        print(df)
        print('####'*5)
        res = logistic_regression_classification(df, 'target', test_size=0.25, penalty='l2', dual=False)
        print(res['te_pred_prob'])

        print('####'*5)
        res = random_forest_classification(df, 'target', test_size=0.25, n_estimators=100, criterion='gini')
        print(res['te_pred_prob'])

        print('####'*5)
        res = gradient_boosting_classification(df, 'target', test_size=0.25, n_estimators=100, learning_rate=0.1)
        print(res['te_pred_prob'])

        from sklearn.datasets import make_regression
        import pandas as pd
        loader = make_regression()
        df = pd.DataFrame(loader[0])
        df['target'] = loader[1]

        df[df.columns[0]] = df[df.columns[0]].astype(str)
        df[df.columns[1]] = df[df.columns[1]].astype(int)
        # df['target'] = df['target'].astype(str)

        print(df)
        print('####' * 5)
        res = linear_regression(df, 'target', test_size=0.25, )
        print(res['te_pred_prob'])

        print('####' * 5)
        res = random_forest_regression(df, 'target', test_size=0.25, n_estimators=100, criterion='squared_error')
        print(res['te_pred_prob'])

        print('####' * 5)
        res = gradient_boosting_regression(df, 'target', test_size=0.25, n_estimators=100, learning_rate=0.1)
        print(res['te_pred_prob'])
    run()