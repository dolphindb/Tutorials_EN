# Function Mappings: From Python to DolphinDB <!-- omit in toc -->

This page shows the corresponding DolphinDB functions for selected Python functions. 

The DolphinDB functions listed below are supported in version 2.00 (refer to [user guide](https://www.dolphindb.com/help200/Introduction/index.html) for more information).

The following python libraries are covered:

- [1. Python built-in function](#1-python-built-in-function)
- [2. NumPy](#2-numpy)
- [3. Pandas](#3-pandas)
- [4. SciPy](#4-scipy)
- [5. Statsmodels](#5-statsmodels)
- [6. sklearn](#6-sklearn)
- [7. TA-lib](#7-ta-lib)


##  1. Python built-in function 

| Python      | DolphinDB      |
| ----------- | -------------- |
| all         | all            |
| any         | any            |
| in          | in             |


##  2. NumPy

| NumPy                                                    | DolphinDB                   |
| -------------------------------------------------------- | --------------------------- |
| numpy.median                                             | med                         |
| numpy.var(ddof=1)                                        | var                         |
| numpy.var                                                | varp                        |
| numpy.cov                                                | covarMatrix                 |
| numpy.cov(fweights)                                      | wcovar                      |
| numpy.std(ddof=1)                                        | std                         |
| numpy.std                                                | stdp                        |
| numpy.percentile / pandas.Series.percentile              | percentile                  |
| numpy.quantile / pandas.Series.quantile                  | quantile                    |
| numpy.quantile                                           | quantileSeries              |
| numpy.corrcoef                                           | corrMatrix                  |
| numpy.random.beta                                        | randBeta                    |
| numpy.random.binomial                                    | randBinomial                |
| numpy.random.chisquare                                   | randChiSquare               |
| numpy.random.exponential                                 | randExp                     |
| numpy.random.f                                           | randF                       |
| numpy.random.gamma                                       | randGamma                   |
| numpy.random.logistic                                    | randLogistic                |
| numpy.random.normal                                      | randNormal                  |
| numpy.random.multivariate_normal                         | randMultivariateNormal      |
| numpy.random.poisson                                     | randPoisson                 |
| numpy.random.standard_t                                  | randStudent                 |
| numpy.random.rand                                        | rand                        |
| numpy.argsort                                            | isort/isort!                |
| numpy.averge(weight)                                     | wavg                        |
| numpy.random.uniform                                     | randUniform                 |
| numpy.random.weibull                                     | randWeibull                 |
| numpy.max                                                | max                         |
| numpy.min                                                | min                         |
| numpy.mean                                               | mean/avg                    |
| numpy.sum                                                | sum                         |
| nump.random.normal                                       | norm                        |

##  3. Pandas

| Pandas                                                       | DolphinDB               |
| ------------------------------------------------------------ | ----------------------- |
| pandas.Series.loc / pandas.DataFrame.loc                     | loc                     |
| pandas.Series.align / pandas.DataFrame.align                 | align                   |
| pandas.DataFrame.ewm.var                                     | ewmVar                  |
| pandas.Series.cov                                            | covar                   |
| pandas.DataFrame.ewm.cov                                     | ewmCov                  |
| pandas.ewmstd                                                | ewmStd                  |
| pandas.Series.corr                                           | corr                    |
| pandas.DataFrame.ewm.corr                                    | ewmCorr                 |
| pandas.DataFrame.max / pandas.Series.max                     | max                     |
| pandas.DataFrame.min / pandas.Series.min                     | min                     |
| pandas.DataFrame.mean / pandas.Series.mean                   | mean/avg                |
| pandas.DataFrame.ewm.mean                                    | ewmMean                 |
| pandas.DataFrame.sum / pandas.Series.sum                     | sum                     |
| pandas.DataFrame.sem / pandas.Series.sem                     | sem                     |
| pandas.DataFrame.mad / pandas.Series.mad                     | mad (useMedian=false)   |
| pandas.DataFrame.kurt(kurtosis) / pandas.Series.kurt(kurtosis)  | kurtosis                |
| pandas.DataFrame.skew / pandas.Series.kurt(skew)        | skew                    |
| pandas.Series.resample / pandas.DataFrame.resample       | resample               |
| pandas.Series.copy / pandas.DataFrame.copy               | copy                   |
| pandas.Series.describe / pandas.DataFrame.describe  (similar) | stat                   |
| pandas.DataFrame.isnull/pandas.DataFrame.isna         | isNull                |
| pandas.DataFrame.notnull/pandas.DataFrame.notna       | isValid               |
| pandas.Series.between                                 | between               |
| pandas.Series.str.startswith                          | startsWith            |
| pandas.Series.str.endswith                            | endsWith              |
| pandas.Series.str.find                                | regexFind             |
| pandas.Series.duplicated /pandas.DataFrame.duplicated | isDuplicated          |
| pandas.Series.is_monotonic_decreasing                 | isMonotonicIncreasing |
| pandas.Series.is_monotonic_increasing                 | isMonotonicDecreasing |
| pandas.DataFrame.mask / pandas.Series.mask            | mask                  |
| pandas.DataFrame.bfill                 | bfill/bfill!       |
| pandas.DataFrame.ffill                        | ffill/ffill!       |
| pandas.DataFrame.interpolate                  | interpolate        |
| pandas.DataFrame.interpolate(method='linear') | lfill/lfill!       |
| pandas.DataFrame.fillna                       | nullFill/nullFill! |
| pandas.Series.sort_values                                    | sort/sort!     |
| pandas.Series.str.isspace                                    | isSpace               |
| pandas.Series.str.isalnum                                    | isAlNum               |
| pandas.Series.str.isalpha                                    | isAlpha               |
| pandas.Series.str.isnumeric                                  | isNumeric             |
| pandas.Series.str.isdecimal                                  | isDecimal             |
| pandas.Series.str.isdigit                                    | isDigit               |
| pandas.Series.str.islower                                    | isLower               |
| pandas.Series.str.isupper                                    | isUpper               |
| pandas.Series.str.istitle                                    | isTitle               |
| pandas.Series.rank/pandas.DataFrame.rank                     | rank           |
| pandas.Series.rank(method='dense')/pandas.DataFrame.rank(method='dense') | denseRank      |


##  4. SciPy

| SciPy                                                    | DolphinDB                   |
| -------------------------------------------------------- | --------------------------- |
| scipy.stats.percentileofscore                            | percentileRank              |
| scipy.stats.spearmanr(X, Y)[0]                           | spearmanr(X, Y)             |
| scipy.spatial.distance.euclidean                         | euclidean                   |
| scipy.stats.beta.cdf(X, a, b)                            | cdfBeta(a, b, X)            |
| scipy.stats.binom.cdf(X, trials, p)                      | cdfBinomial(trials, p, X)   |
| scipy.stats.chi2.cdf(x, df)                              | cdfChiSquare(df, X)         |
| scipy.stats.expon.cdf(x, scale=mean)                     | cdfExp(mean, X)             |
| scipy.stats.f.cdf(X, dfn, dfd)                           | cdfF(dfn, dfd, X)           |
| scipy.stats.gamma.cdf(X, shape, scale=scale)             | cdfGamma(shape, scale, X)   |
| scipy.stats.logistic.cdf(X, loc=mean,scale=scale)        | cdfLogistic(mean, scale, X) |
| scipy.stats.norm.cdf(X, loc=mean, scale=stdev)           | cdfNormal(mean,stdev,X)     |
| scipy.stats.poisson.cdf(X, mu=mean)                      | cdfPoisson(mean, X)         |
| scipy.stats.t.cdf(X, df)                                 | cdfStudent(df, X)           |
| scipy.stats.uniform.cdf(X, loc=lower, scale=upper-lower) | cdfUniform(lower, upper, X) |
| scipy.stats.weibull_min.cdf(X, alpha, scale=beta)        | cdfWeibull(alpha, beta, X)  |
| scipy.stats.zipfian.cdf(X, exponent, num)                | cdfZipf(num, exponent, X)   |
| scipy.stats.beta.ppf(X, a, b)                            | invBeta                     |
| scipy.stats.binom.ppf(X, trials, p)                      | invBinomial                 |
| scipy.stats.chi2.ppf(x, df)                              | invChiSquare                |
| scipy.stats.expon.ppf(x, scale=mean)                     | invExp                      |
| scipy.stats.f.ppf(X, dfn, dfd)                           | invF                        |
| scipy.stats.gamma.ppf(X, shape, scale=scale)             | invGamma                    |
| scipy.stats.logistic.ppf(X, loc=mean,scale=scale)        | invLogistic                 |
| scipy.stats.norm.ppf(X, loc=mean, scale=stdev)           | invNormal                   |
| scipy.stats.poisson.ppf(X, mu=mean)                      | invPoisson                  |
| scipy.stats.t.ppf(X, df)                                 | invStudent                  |
| scipy.stats.uniform.ppf(X, loc=lower, scale=upper-lower) | invUniform                  |
| scipy.stats.weibull_min.ppf(X, alpha, scale=beta)        | invWeibull                  |
| scipy.stats.chisquare                                    | chiSquareTest               |
| scipy.stats.f_oneway                                     | fTest                       |
| scipy.stats.ttest_ind                                    | tTest                       |
| scipy.stats.ks_2samp                                     | ksTest                      |
| scipy.stats.shapiro                                      | shapiroTest                 |
| scipy.stats.mannwhitneyu                                 | mannWhitneyUTest            |
| scipy.stats.mstats.winsorize                             | winsorize                   |
| scipy. stats.kurtosis                                    | kurtosis                    |
| scipy.stats.skew                                         | skew                        |
| scipy.stats.sem                                          | sem                         |
| scipy.stats.zscore(ddof=1)                               | zscore                      |



##  5. Statsmodels

| Statsmodels                            | DolphinDB      |
| -------------------------------------- | -------------- |
| statsmodels.api.tsa.acf                | acf            |
| statsmodels.tsa.seasonal.STL           | stl            |
| statsmodels.stats.weightstats.ztest    | zTest          |
| statsmodels.multivariate.manova.MANOVA | manova         |
| statsmodels.api.stats.anova_lm         | anova          |
| statsmodels.regression.linear_model.OLS                 | olsolsEx               |
| statsmodels.regression.linear_model.WLS                 | wls                    |

##  6. sklearn

| sklearn                                                 | DolphinDB              |
| ------------------------------------------------------- | ---------------------- |
| sklearn.linear_model.LinearRegression().fit(Y, X).coef_ | beta(X, Y)             |
| sklearn.metrics.mutual_info_score                       | mutualInfo             |
| sklearn.ensemble.AdaBoostClassifier                     | adaBoostClassifier     |
| sklearn.ensemble.AdaBoostRegressor                      | adaBoostRegressor      |
| sklearn.ensemble.RandomForestClassifier                 | randomForestClassifier |
| sklearn.ensemble.RandomForestRegressor                  | randomForestRegressor  |
| sklearn.naive_bayes.GaussianNB                          | gaussianNB             |
| sklearn.naive_bayes.MultinomialNB                       | multinomialNB          |
| sklearn.linear_model.LogisticRegression                 | logisticRegression     |
| sklearn.mixture.GaussianMixture                         | gmm                    |
| sklearn.cluster.k_means                                 | kmeans                 |
| sklearn.neighbors.KNeighborsClassifier                  | knn                    |
| sklearn.linear_model.ElasticNet                         | elasticNet             |
| sklearn.linear_model.Lasso                              | lasso                  |
| sklearn.linear_model.Ridge                              | ridge                  |
| sklearn.decomposition.PCA                               | pca                    |



##  7. TA-lib

| TA-lib                                            | DolphinDB       |
| ------------------------------------------------- | --------------- |
| talib.MA                                          | ma              |
| talib.EMA                                         | ema             |
| talib.WMA                                         | wma             |
| talib.SMA                                         | sma             |
| talib.TRIMA                                       | trima           |
| talib.TEMA                                        | tema            |
| talib.DEMA                                        | dema            |
| talib.KAMA                                        | kama            |
| talib.T3                                          | t3              |
| talib.LINEARREG_SLOPE / talib.LINEARREG_INTERCEPT | linearTimeTrend |
| talib.TRANGE                                      | trueRange       |

> The functions listed above are DolphinDB built-in functions. More TA-lib functions are provided in DolphinDB ta module. Refer to [DolphinDB tutorial: Technical Analysis Indicator Library](https://github.com/dolphindb/Tutorials_EN/blob/master/ta.md) for more information.

**Note:**
Contact us or comment below to send us feedback or report any problems you find. 
