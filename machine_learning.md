# Machine Learning in DolphinDB

DolphinDB implements machine learning algorithms including linear regression, random forest, K-means, etc. that allow users to easily complete tasks such as regression, classification, and clustering. This tutorial will introduce the process of using DolphinDB script language for machine learning with specific application examples. 

All code examples in this tutorial are based on DolphinDB server version 1.10.11.

- [1. Small-Sample Classification](#1-small-sample-classification)
  - [1.1 Import Data to DolphinDB](#11-import-data-to-dolphindb)
  - [1.2 Data Preprocessing](#12-data-preprocessing)
  - [1.3 Random Forest Classification](#13-random-forest-classification)
  - [1.4 Model Persistence](#14-model-persistence)
- [2. Distributed Machine Learning](#2-distributed-machine-learning)
  - [2.1 Data Preprocessing](#21-data-preprocessing)
  - [2.2 Model Training](#22-model-training)
- [3. Using PCA for Dimensionality Reduction](#3-using-pca-for-dimensionality-reduction)
- [4. Linear Regression: Ridge, Lasso, and ElasticNet](#4-linear-regression-ridge-lasso-and-elasticnet)
- [5. Machine Learning With DolphinDB Plugins](#5-machine-learning-with-dolphindb-plugins)
  - [5.1 Load XGBoost Plugin](#51-load-xgboost-plugin)
  - [5.2 Train and Predict](#52-train-and-predict)
- [Appendix: Built-in Functions for Machine Learning](#appendix-built-in-functions-for-machine-learning)
  - [A. Training Functions](#a-training-functions)
  - [B. Tools](#b-tools)
  - [C. Plugins](#c-plugins)


## 1. Small-Sample Classification

We use the [Wine](http://archive.ics.uci.edu/ml/machine-learning-databases/wine/) dataset provided by [UCI Machine Learning Repository](http://archive.ics.uci.edu/ml/) to train our first random forest classification model.

### 1.1 Import Data to DolphinDB

Download the dataset, and import it to DolphinDB with function `loadText`.

```
wineSchema = table(
    `Label`Alcohol`MalicAcid`Ash`AlcalinityOfAsh`Magnesium`TotalPhenols`Flavanoids`NonflavanoidPhenols`Proanthocyanins`ColorIntensity`Hue`OD280_OD315`Proline as name,
    `INT`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE as type
)
wine = loadText("D:/dataset/wine.data", schema=wineSchema)
```

### 1.2 Data Preprocessing

The DolphinDB [randomForestClassifier](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/r/randomForestClassifier.html) function requires the class labels to be integers in [0, *numClasses*), while the wine dataset uses class labels 1, 2, 3. So we use the following code to process these labels as 0, 1, 2.

```
update wine set Label = Label - 1
```

Split the data into training and testing sets in a 7:3 ratio. In this example, the function `trainTestSplit` is defined to facilitate the split.

```
def trainTestSplit(x, testRatio) {
    xSize = x.size()
    testSize = xSize * testRatio
    r = (0..(xSize-1)).shuffle()
    return x[r > testSize], x[r <= testSize]
}

wineTrain, wineTest = trainTestSplit(wine, 0.3)
wineTrain.size()    // 124
wineTest.size()     // 54
```

### 1.3 Random Forest Classification

We perform random forest classification on the training set with function `randomForestClassifier`. The function has four required parameters:

- *ds*: The input data source (usually generated using the `sqlDS` function).
- *yColName*: The column name of the dependent variable in the data source.
- *xColNames*: The column names of the dependent variables in the data source.
- *numClasses*: The number of classes.

```
model = randomForestClassifier(
    sqlDS(<select * from wineTrain>),
    yColName=`Label,
    xColNames=`Alcohol`MalicAcid`Ash`AlcalinityOfAsh`Magnesium`TotalPhenols`Flavanoids`NonflavanoidPhenols`Proanthocyanins`ColorIntensity`Hue`OD280_OD315`Proline,
    numClasses=3
)
```

Predict the test set with the trained model:

```
predicted = model.predict(wineTest)
```

Examine the prediction accuracy:

```
sum(predicted == wineTest.Label) \ wineTest.size();

0.925926
```

### 1.4 Model Persistence

Save the trained model to disk using the `saveModel` function:

```
model.saveModel("D:/model/wineModel.bin")
```

You can load the model from disk with `loadModel` for predictions:

```
model = loadModel("D:/model/wineModel.bin")
predicted = model.predict(wineTest)
```

## 2. Distributed Machine Learning

The above example only uses a small dataset for demonstration purposes. DolphinDB offers a machine learning library that differs from the usual ones in that it is specifically designed for distributed processing. It provides reliable support for machine learning algorithms in distributed environments. This chapter will introduce how to use the logistic regression algorithm in the DolphinDB distributed database to complete the training of classification models.

We use a DFS database partitioned by stock ID. It contains daily OHLC data of stocks from 2010 to 2018. 

The following nine variables are used as predictive indicators:

- opening price
- highest price
- lowest price
- closing price
- difference between the opening price of the current day and the closing price of the previous day
- difference between the opening price of the current day and the opening price of the previous day
- 10-day moving average
- correlation coefficient
- relative strength index (RSI). 

We will make predictions on whether the closing price of the second day is greater than that of the current day.

### 2.1 Data Preprocessing

In this example, missing values in the raw data are filled with the `ffill` function. The first 10 rows of the 10-day moving average and RSI calculation result are empty and we remove these records from output. We use the `transDS!` function to apply the preprocessing steps to the original data. In this example, calculating RSI uses the ta module of DolphinDB, and the specific usage can be found in [DolphinDBModules](https://github.com/dolphindb/DolphinDBModules).

```
use ta

def preprocess(t) {
    ohlc = select ffill(Open) as Open, ffill(High) as High, ffill(Low) as Low, ffill(Close) as Close from t
    update ohlc set OpenClose = Open - prev(Close), OpenOpen = Open - prev(Open), S_10 = mavg(Close, 10), RSI = ta::rsi(Close, 10), Target = iif(next(Close) > Close, 1, 0)
    update ohlc set Corr = mcorr(Close, S_10, 10)
    return ohlc[10:]
}
```

After loading the data, generate a data source through function `sqlDS`, and use `transDS!` to convert the data source using the preprocessing function `preprocess defined above`:

```
ohlc = database("dfs://trades").loadTable("ohlc")
ds = sqlDS(<select * from ohlc>).transDS!(preprocess)
```

### 2.2 Model Training

We use function [logisticRegression](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/l/logisticRegression.html) which has three required parameters:

- *ds*: The input data source (usually generated using the `sqlDS` function).
- *yColName*: The column name of the dependent variable in the data source.
- *xColNames*: The column names of the dependent variables in the data source.

The data source generated in [section 2.1](#21-data-preprocessing) can be passed to *ds*:

```
model = logisticRegression(ds, `Target, `Open`High`Low`Close`OpenClose`OpenOpen`S_10`RSI`Corr)
```

Then use the trained model for prediction and check the classification accuracy:

```
aapl = preprocess(select * from ohlc where Ticker = `AAPL)
predicted = model.predict(aapl)
score = sum(predicted == aapl.Target) \ aapl.size()    // 0.756522
```

## 3. Using PCA for Dimensionality Reduction

Principal component analysis (PCA) is a popular technique in machine learning for analyzing large datasets containing a high number of dimensions/features per observation. It is often used to reduce the dimensionality of large datasets by transforming a large set of variables into a smaller one that still contains most of the information in the large set. PCA can also be used to transform a high dimensional data to low dimensional data (2 or 3 dimension) so that it can be visualized easily.

Taking the example conducted in [Chapter 1](#1-small-sample-classification), the input dataset has 13 dependent variables. By calling the [pca](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/p/pca.html) function on the data source, the variance weights of each principal component are observed. Set the normalize parameter to true to normalize the data.

```
xColNames = `Alcohol`MalicAcid`Ash`AlcalinityOfAsh`Magnesium`TotalPhenols`Flavanoids`NonflavanoidPhenols`Proanthocyanins`ColorIntensity`Hue`OD280_OD315`Proline
pcaRes = pca(
    sqlDS(<select * from wineTrain>),
    colNames=xColNames,
    normalize=true
)
```

The return value is a dictionary. Based on the *explainedVarianceRatio*, we can observe that the variance weights of the initial three compressed dimensions are already substantial. Therefore, compressing the data into three dimensions already satisfies training purposes.

```
pcaRes.explainedVarianceRatio;
[0.209316,0.201225,0.121788,0.088709,0.077805,0.075314,0.058028,0.045604,0.038463,0.031485,0.021256,0.018073,0.012934]
```

Keep only the first three principal components:

```
components = pcaRes.components.transpose()[:3]
```

Apply the principal component analysis matrix to the input data set and call `randomForestClassifier` for training.

```
def principalComponents(t, components, yColName, xColNames) {
    res = matrix(t[xColNames]).dot(components).table()
    res[yColName] = t[yColName]
    return res
}

ds = sqlDS(<select * from wineTrain>)
ds.transDS!(principalComponents{, components, `Class, xColNames})

model = randomForestClassifier(ds, yColName=`Class, xColNames=`col0`col1`col2, numClasses=3)
```

The principal components of the test set also need to be extracted for prediction of the test set. 

```
model.predict(wineTest.principalComponents(components, `Class, xColNames))
```

## 4. Linear Regression: Ridge, Lasso, and ElasticNet

DolphinDB offers functions [ols](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/o/ols.html) and [olsEx](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/o/olsEx.html) for ordinary least squares regression. These functions typically deal with low-dimensional data, but can lead to overfitting when working with high-dimensional data. To address this issue, the Ridge, Lasso, and ElasticNet regression methods were introduced by enhancing the algorithm and tackling the problem from different aspects:

- Lasso performs the L1 regularization which adds penalty equivalent to the square of the magnitude of coefficients to the objective function for sparse feature selection.
- Ridge performs the L2 regularization which adds penalty equivalent to the absolute value of the magnitude of coefficients.
- ElasticNet employs both L1 and L2 penalties during training.

DolphinDB provides functions [lasso](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/l/lasso.html), [ridge](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/r/ridge.html), [elasticNet ](https://www.dolphindb.com/help/FunctionsandCommands/FunctionReferences/e/elasticNet.html)accordingly. They all have three required parameters:

- *ds*: An in-memory table or the input data source (usually generated using the `sqlDS` function).
- *yColName*: The column name of the dependent variable in the data source.
- *xColNames*: The column names of the dependent variables in the data source.

The function `lasso` is a special case of `elasticNet` when *l1Ratio* = 1. They use the same implementation method that employs coordinate descent to compute the parameters. The function `ridge` uses an analytical solution, and the *solver* can be 'svd' or 'cholesky'.

To train a model:

```
model = lasso(sqlDS(<select * from t>), `y, `x0`x1, alpha=0.5)
```

To predict on a test set:

```
model.predict(t)
```

## 5. Machine Learning With DolphinDB Plugins

In addition to the built-in functions that implement classical machine learning algorithms, DolphinDB also provides plugins for calling third-party libraries for machine learning. This chapter uses the DolphinDB XGBoost plugin as an example.

### 5.1 Load XGBoost Plugin

Download the pre-compiled XGBoost plugin from xxxx to your local machine. Then, run `loadPlugin(pathToXgboost)` in DolphinDB, where *pathToXgboost* is the path to the downloaded *PluginXgboost.txt* file:

```
pathToXgboost = "C:/DolphinDB/plugin/xgboost/PluginXgboost.txt"
loadPlugin(pathToXgboost)
```

### 5.2 Train and Predict

We also use the wine dataset for model training in this example. The training method `xgboost::train(Y, X, [params], [numBoostRound=10], [xgbModel])` is used. The Label column of the wineTrain set is taken as the input Y, and the other columns are kept as X.

```
Y = exec Label from wineTrain
X = select Alcohol, MalicAcid, Ash, AlcalinityOfAsh, Magnesium, TotalPhenols, Flavanoids, NonflavanoidPhenols, Proanthocyanins, ColorIntensity, Hue, OD280_OD315, Proline from wineTrain
```

Before training the model, we need to specify a dictionary for *params*. We will train a multi-classification model so the *objective* is set to “multi-softmax” and the number of classification *num_class* is set to 3. You can refer to [XGBoost doc](https://xgboost.readthedocs.io/en/latest/parameter.html#general-parameters) for the parameter descriptions.

Parameters in this example are set as below:

```
params = {
    objective: "multi:softmax",
    num_class: 3,
    max_depth: 5,
    eta: 0.1,
    subsample: 0.9
}
```

Train the model, predict and calculate the classification accuracy:

```
model = xgboost::train(Y, X, params)

testX = select Alcohol, MalicAcid, Ash, AlcalinityOfAsh, Magnesium, TotalPhenols, Flavanoids, NonflavanoidPhenols, Proanthocyanins, ColorIntensity, Hue, OD280_OD315, Proline from wineTest
predicted = xgboost::predict(model, testX)

sum(predicted == wineTest.Label) \ wineTest.size()    // 0.962963
```

Similarly, the model can be persisted to or loaded from disk:

```
xgboost::saveModel(model, "xgboost001.mdl")

model = xgboost::loadModel("xgboost001.mdl")
```

By specifying the *xgbModel* parameter of `xgboost::train`, incremental training can be performed on an existing model:

```
model = xgboost::train(Y, X, params, , model)
```

## Appendix: Built-in Functions for Machine Learning

### A. Training Functions 

| **Function**           | **Usage**                 | **Description**                           | **Distributed Processing** |
| :--------------------- | :------------------------ | :---------------------------------------- | :------------------------- |
| adaBoostClassifier     | classification            | AdaBoost classification                   | √                          |
| adaBoostRegressor      | regression                | AdaBoost regression                       | √                          |
| elasticNet             | regression                | Elastic net regression                    | ×                          |
| gaussianNB             | classification            | Naive Bayesian classification             | ×                          |
| glm                    | classification/regression | generalized linear model (GLM)            | √                          |
| kmeans                 | clustering                | k-means clustering                        | ×                          |
| knn                    | classification            | k-nearest neighbors (KNN)                 | ×                          |
| lasso                  | regression                | Lasso regression                          | ×                          |
| logisticRegression     | classification            | logistic regression                       | √                          |
| multinomialNB          | classification            | multinomial Naive Bayesian classification | ×                          |
| ols                    | regression                | ordinary-least-squares (OLS) regression   | ×                          |
| olsEx                  | regression                | ordinary-least-squares (OLS) regression   | √                          |
| pca                    | downsampling              | principal component analysis (PCA)        | √                          |
| randomForestClassifier | classification            | random forest classification              | √                          |
| randomForestRegressor  | regression                | random forest regression                  | √                          |
| ridge                  | regression                | ridge regression                          | √                          |

 

### B. Tools

| **Function** | **Description** |
| :----------- | :-------------- |
| loadModel    | load model      |
| saveModel    | save model      |
| predict      | prediction      |

 

### C. Plugins 

| **Plugin** | **Usage**                 | **Description**                         |
| :--------- | :------------------------ | :-------------------------------------- |
| XGBoost    | classification/regression | gradient boosting based on XGBOOST      |
| svm        | classification/regression | support vector machines based on LIBSVM |