gcloud projects list
gcloud config set project


gcloud ml vision
gcloud ml vision detect-logos Logo-Vodafone.png


gcloud ml vision detect-objects rose.jpg
gcloud ml vision detect-text cloud-computing.png

# for the response > save the file
#
jsoneditoronline.org

# install the api for the vision API
pip3 install --upgrade google-cloud-vision

# create service account for ml
#manage keys create a new key
#upload the keys
# export GOOGLE_APPLICATION_CREDENTIALS=''
python3 logo_detect.py

gcloud ml lenguage

gcloud ml language classify-text --content='House Intelligence Committee Chairman Adam Schiff, who also sits on the House committee investigating the Jan. 6, 2021, insurrection, said Sunday that he doesnt believe the committees upcoming report would focus almost entirely on Donald Trump.
Schiff, a California Democrat, told CNNs Dana Bash on State of the Union that he doesn’t believe a recent Washington Post story about how the contents of the report could potentially leave out investigations in other areas.'


# look for a news related to politics , then look for a news related to technology
gcloud ml language classify-text --content='Facebooks parent company, Meta, has released an AI model called Galactica that is designed to write essays or scientific papers summarising the state of the art on a given topic, complete with citations, as well as detailed Wikipedia articles. It can also carry out mathematical calculations and answer questions about specific molecules.'

# look lfor a review in amazon
gcloud ml language analyze-sentiment --content='In description it says newest model, not true. BUT, for the price and quality itll do the job. The first thing that popped up is that there is no more updates for this laptop, so if you buy this keep in mind if you use certain sites with bugs and advertisements, youll have to take it in to get wiped sooner rather than later due to it being out dated to updates. Other than that, I can use it for school and YouTube, 
thats all I care about'
gcloud ml language analyze-sentiment --content='I hate apple'

#look for google wiki 
gcloud ml language analyze-entities --content='Google was founded on September 4, 1998, by Larry Page and Sergey Brin while they were PhD students at Stanford University in California. ' 

pip3 install google-cloud-language



# text classification
#create dataset
# single classification
#happiness.csv

gcloud cloud-shell scp cloudshell:~/employees.csv localhost:~/

gs://cloud-samples-data/ai-platform/flowers/flowers.csv
gs://cloud-ml-data/NL-classification/happiness.csv


from  sklearn import  datasets
iris=datasets.load_iris()
x=iris.data
y=iris.targetD
from sklearn.model_selection import train_test_split
x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=.8)
from sklearn import tree
classifier=tree.DecisionTreeClassifier()
classifier.fit(x_train,y_train)
predictions=classifier.predict(x_test)
from sklearn.metrics import accuracy_score
print(accuracy_score(y_test,predictions))


import pickle
pkl_filename = "model.pkl"
with open(pkl_filename, 'wb') as file:
    pickle.dump(classifier, file)
	
import sklearn
sklearn.__version__

 gsutil cp model.pkl gs://data-flow-demo-ulises
 
 
 
{
  "instances": [[5.1, 7.1, 3, 2.5],[4.9,3,1.4, 0.2] ]
         
}
 
SELECT  *
FROM  `bigquery-public-data.ml_datasets.iris`



CREATE OR REPLACE MODEL
  `ds_bqml_tutorial.irisdata_model`
OPTIONS
  ( model_type='LOGISTIC_REG',
    auto_class_weights=TRUE,
    data_split_method='NO_SPLIT',
    input_label_cols=['species'],
    max_iterations=10) AS
SELECT  *
FROM  `bigquery-public-data.ml_datasets.iris`

SELECT * FROM ML.EVALUATE(MODEL ds_bqml_tutorial.irisdata_model,
   ( SELECT * FROM `bigquery-public-data.ml_datasets.iris`))

select * from ML.PREDICT(MODEL ds_bqml_tutorial.irisdata_model, 
(SELECT
5.1 as sepal_length,
2.5 as petal_length,
3.0 as petal_width,
1.1 as sepal_width))



