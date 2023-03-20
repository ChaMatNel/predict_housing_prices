# -*- coding: utf-8 -*-
"""Kaggle_Chad_Nelson.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1InTzc0Gvc3XpSe51B4O-k3oRD8Of2sso

**Importing Raw Data**
"""

#importing basic packages and datasets
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import seaborn as sns
train = pd.read_csv(r'https://www.dropbox.com/s/qsb53om0lp6wz3d/train.csv?dl=1')
test = pd.read_csv(r'https://www.dropbox.com/s/dffohyddys3tp24/test.csv?dl=1')
sample = pd.read_csv(r'https://www.dropbox.com/s/l0a2mzzqq560xre/sample_submission.csv?dl=1')

print(train.columns)
print(test.columns)

"""**Data Exploration**"""

print(train.columns)
print(train.columns.nunique())
train.describe()
#there are a lot of columns with qualitative data instead of numbers.

#lets visualize some of the key components
sns.scatterplot(data=train,x='LotArea',y='SalePrice', hue='MSZoning')

train.corr().style.background_gradient(cmap="coolwarm")

#it looks like the SalePrice is most correlated with the variables OverallQual, YearBuilt, TotalBsmtSF, 1stFlrSF, GrLivArea, FullBath, GarageCars,	GarageArea

#I wonder what the distribution of MSSubClass is like
sns.countplot(data=train, x=train.MSSubClass)
#20 is 1-STORY 1946 & NEWER ALL STYLES
#60 is 2-STORY 1946 & NEWER

#what is the distribution of years in the data set
sns.histplot(train,x='YearBuilt', bins=10)

#lets see if we have any missing values
import missingno as msno
msno.matrix(train)

"""**Data Clearning/Pre-Processing**

For this next section I will be replacing all the null values with the appropriate value or dropping the value if I don't know what the true value should be
"""

#Making index values the house ID
train = train.set_index('Id')
test = test.set_index('Id')

#we have 1460 total observations. So I want to identiy columns where more than 5% of the data is missing. So less than 1168
for column in train:
  if train[column].count() < 1387:
    print(f'{column}:{train[column].count()}')

sns.countplot(data=train, x=train.Alley)

#delete columns with hardley any observations
train = train.drop(['PoolQC','MiscFeature'],axis=1)
test = test.drop(['PoolQC','MiscFeature'],axis=1)

#replace null values with NA for categorical variables
for column in train[['Alley','FireplaceQu','GarageType','GarageYrBlt','GarageFinish','GarageQual','GarageCond','Fence']]:
    train[column].fillna('NA',inplace=True)
for column in test[['Alley','FireplaceQu','GarageType','GarageYrBlt','GarageFinish','GarageQual','GarageCond','Fence']]:
    test[column].fillna('NA',inplace=True)   
#replace nulls in lot frontage with 0 assuming the property has no lot frontage
train['LotFrontage'].fillna(0,inplace=True)
test['LotFrontage'].fillna(0,inplace=True)

#now im looking for more missing values
for column in train:
  if train[column].count() < 1459:
    print(f'{column}:{train[column].count()}')

train.MasVnrArea.describe()

from numpy.lib.twodim_base import triu_indices_from
#Im replacing all of the nulls with NA for the basement variables with the assumption that these houses have no basement.
for column in train[['BsmtQual','BsmtCond','BsmtExposure','BsmtFinType1','BsmtFinType2']]:
    train[column].fillna('NA',inplace=True)
for column in test[['BsmtQual','BsmtCond','BsmtExposure','BsmtFinType1','BsmtFinType2']]:
    test[column].fillna('NA',inplace=True)

#Here I am replacing thre nulls with "None" because that is the most common classification and probably the best guess
train['MasVnrType'].fillna("None",inplace=True)
train['MasVnrArea'].fillna(0,inplace=True)
test['MasVnrType'].fillna("None",inplace=True)
test['MasVnrArea'].fillna(0,inplace=True)

#Here I fixing the garage year built column to remove the NA to make it a numerical column. I will replace all unknown values with the year the house was built
for i in train['GarageYrBlt']:
  if i =='NA':
    train['GarageYrBlt'] = train['GarageYrBlt'].replace("NA",train.YearBuilt.mean())
train['GarageYrBlt'] = train['GarageYrBlt'].astype(float)

for i in test['GarageYrBlt']:
  if i =='NA':
    test['GarageYrBlt'] = test['GarageYrBlt'].replace("NA",test.YearBuilt.mean())
test['GarageYrBlt'] = test['GarageYrBlt'].astype(float)

#There are still just a few null values in our test set that I will just drop for simplicity (only 12 of 1459 observations were dropped)
test.dropna(axis=0,inplace=True)

#There are no longer any missing values
msno.matrix(train)

"""Now that I have removed all the null values and replaced them with the appropriate value. I am going to create dummy variables for all the categorical columns. We need all values to be numerical to run a model."""

#creating dummy variables for all categorical columns
for column in train:
  if train[column].dtypes == 'object':
    train = pd.get_dummies(train, columns = [f'{column}'])
    test = pd.get_dummies(test, columns = [f'{column}'])

#holding out saleprices so we can add it back in after we make the columns in our train and test set match
sale_prices = train[['SalePrice']]

#eliminating columns that dont show up in test set so we can run our model to predict new values later on
train = train[[i for i in test]]
#adding back our sale prices column so we can train the model
train = train.join(sale_prices)

#Splitting my training data into an X matrix and Y vector
X = train.drop('SalePrice', axis=1)
y = train['SalePrice']

"""Split data into training and test set"""

#split training data into training and test sets for cross validation
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test= train_test_split(X,y,random_state=0,test_size=.25)

"""*Note, I am not standardizing my data in this case becasue I don't plan on using a model that relies on euclidean distance to generate predicitons. Standardization isn't required for random forests.*

**Choosing a Model**

Because I am trying to predict the house selling price, a regression model will be appropriate. My options in that case would be OLS, Logit, LASSO, SVM, Random Forests, Gradient Boosted Random Forests. All methods would be appropriate. In this case because I only care about prediction, I will choose to use Random Forests regression.

**Choosing the Tuning Parameters (Cross Validation) & Training**
"""

#importing packages
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV

#creating model and showing best estimators
rf_regressor = RandomForestRegressor(random_state=1)
search_grid = {'n_estimators':[i for i in range(0,150,10)],'max_depth':[i for i in range(0,12,2)], 'max_features':['sqrt', 'log2', None]}
grid_search = GridSearchCV(rf_regressor,search_grid,cv=5,return_train_score=True)
best_model = grid_search.fit(X_train,y_train)
print("Best n_estimators: ",best_model.best_estimator_.get_params()['n_estimators'])
print("Best max_depth: ",best_model.best_estimator_.get_params()['max_depth'])
print("Best max_features ", best_model.best_estimator_.get_params()['max_features'])

"""**Evaluating Model Performance**"""

#scores on test and training set
print(f'Score on training set:{best_model.score(X_train,y_train)}')
print(f'Score on test set:{best_model.score(X_test,y_test)}')

from sklearn.metrics import mean_squared_error

#mean squared error on test and training sets
y_pred_train = best_model.predict(X_train).round(1)
y_pred_test = best_model.predict(X_test).round(1)
print(f'Train MSE:{mean_squared_error(y_train,y_pred_train)}')
print(f'Test MSE:{mean_squared_error(y_test,y_pred_test)}')

#create a data frame that displays predicted values with true values from test set
y_pred_test = pd.DataFrame(y_pred_test)
y_test_2 = pd.DataFrame(y_test).reset_index()
performance_test_set = y_test_2.join(y_pred_test)
performance_test_set.rename(columns={0:'PredSalePrice'},inplace=True)
performance_test_set['Error'] = np.abs(performance_test_set['PredSalePrice'] - performance_test_set['SalePrice'])
print(f'On average, the model was off by {performance_test_set.Error.mean().round(0)}$')

"""**Predicting New Observations**"""

#constructing data frame for final predictions on new data
new_predictions = pd.DataFrame(best_model.predict(test).round(0))
test_id = pd.DataFrame(test.reset_index()['Id'])
final_submission = test_id.join(new_predictions)
final_submission.rename(columns={0:'Prediction'},inplace=True)
final_submission