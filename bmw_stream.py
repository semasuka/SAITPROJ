import streamlit as st
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from itertools import permutations

#======================  DATA EXTRACTION & PREPROCESSING  =====================
   
file1 = "Ready_data.csv"
file2 = "Aggregated Data.csv"

df_original = pd.read_csv(file1)
df = pd.read_csv(file2,index_col="CUST_KEY")
df1 = df.copy()

scaler = MinMaxScaler() #MinMax Normalize Numeric Values
df[['JOBPARTCHARGE', 'JOBLABOURCHARGE', 'AVG_MILE']] = scaler.fit_transform(df[['JOBPARTCHARGE', 'JOBLABOURCHARGE', 'AVG_MILE']])

le = LabelEncoder() #convert categorical values to numeric
df[['YEAR', 'MODEL_NEW']] = df[['YEAR', 'MODEL_NEW']].apply(le.fit_transform)

#=============================   FUNCTIONS   ==================================

scaler = MinMaxScaler()
le= LabelEncoder()

def encoder(inp):
    df1["YEAR"] = df1["YEAR"].astype(str)
    names= ['JOBPARTCHARGE', 'JOBLABOURCHARGE', 'MODEL_NEW', 'YEAR', 'AVG_MILE']
    i=0
    arr = []
    for x in inp:
        if isinstance(x,str):
            le.fit(df1[names[i]])
            arr.append(le.transform(np.array([x])))
        else:
            scaler.fit(np.array([df1[names[i]]]).reshape(-1,1))
            arr.append(scaler.transform(np.array([x]).reshape(-1,1)))
        i = i+1
    result = [x.tolist() for x in arr]
    result = [x for list in result for x in list]

    res = []
    for i in result:
        if isinstance(i,list):
            for y in i:
                res.append(y)
        else:
            res.append(i)
    
    return np.array(res)

def top_input(a,b,c,d,e,f):
    result = [a,b,c,d,e]
    df_dist_new = pairwise_distances(encoder(result).reshape(1,-1),df, metric='minkowski')
    df_new1 = pd.DataFrame(df_dist_new.reshape(-1,1), index=df.index, columns=["Similarity_Strength"])
    top = df_new1.sort_values(by="Similarity_Strength")
    top_df = top[1:(int(f)+1)]
    df1.reset_index(inplace=True)
    top_df = pd.merge(top_df,df1, on="CUST_KEY")
    return top_df

#return arbitrary number of top similar customers
def top_cust(cust, top_number):
    df_dist = pairwise_distances(df, metric='minkowski') #find mikowski distances between all customers
    df_new = pd.DataFrame(df_dist, index=df.index, columns=df.index) #convert to dataframe
    _var = df_new[[cust]].sort_values(cust)
    df1.reset_index(inplace=True)
    _var = df1[df1["CUST_KEY"].isin(_var[[cust]][1:(int(top_number)+1)].index)]
    return _var



#========================   STREAMLIT CODING SECTION 1 ========================

col1, col2, col3 = st.columns([1, 1, 1])
col3.image("Logo.png",use_column_width=True)

st.title("M-Power Customer Management")

st.sidebar.header("**User Inputs for New Customer**")

a = st.sidebar.slider("Average Part Charge:", min_value=0,max_value=1000,step=10)
b = st.sidebar.slider("Average Labor Charge:", min_value=0,max_value=1000,step=10)
e = st.sidebar.slider("Average Yearly Mileage:", min_value=0,max_value=30000,step=1000)
c = st.sidebar.selectbox("Car Model:",np.sort(df1["MODEL_NEW"].unique()),index=80)
d = st.sidebar.selectbox("Year of Manufacture:",np.sort(df1["YEAR"].unique()),index=30)
f = st.sidebar.number_input("Number of Top Customers to Return:", value=10)

if st.sidebar.button("Run Top Customers"):
    st.header("New Customer Retrieval")
    st.dataframe(top_input(a,b,c,str(d),e,f))
    
st.sidebar.header("**User Inputs for Existing Customer**")

g = st.sidebar.text_input("Customer Number:", value="")
h = st.sidebar.number_input("Number of Top Customers to Return:", value=10, key="new")

if len(g) != 0: 
    if g not in list(df1.index):
        st.error("Customer Not Found, Please enter correct number")
    
if st.sidebar.button("Run Top Customers",key="new2"):
    st.header("Existing Customer Retrieval")
    st.dataframe(top_cust(g,h))

#====================== SERVICE RECOMMENDATION CODE =========================== 

st.sidebar.header("**User Inputs for Service Recommendation**")

df_original["CUST_KEY"] = df_original["CUST"].astype(str) + "-" + df_original["VIN"] #concatenate customer # and vin #

df2 = df_original.copy()

df2 = df2[(df2["JOBLABOURCHARGE"] !=0) | (df2["JOBPARTCHARGE"]!=0)] #remove zero value services

radio = st.sidebar.radio("Select Customer Type for Service Recommendation", ("New Customer","Existing Customer","None"))

#create all possible permutations of 3 services for each RO
def perms(x):
    variations = pd.DataFrame(list(permutations(x.values, 2)),columns=["Service 1","Service 2"])
    
    return variations

if  radio =="New Customer":
    df2 = df2[df2["CUST_KEY"].isin(list(top_input(a,b,c,str(d),e,f)["CUST_KEY"]))]#return data for only the target customer from original dataset
    df2 = df2[["RO","OP_DESC"]] #retrieve only RO and OP_DESC 
    df2 = df2.groupby("RO")["OP_DESC"].apply(perms) #group all permutations per RO
    df2 = df2.reset_index(drop=True) 
elif radio =="Existing Customer":
    df2 = df2[df2["CUST_KEY"].isin(list(top_cust(g,h)["CUST_KEY"]))]
    df2 = df2[["RO","OP_DESC"]] #retrieve only RO and OP_DESC 
    df2 = df2.groupby("RO")["OP_DESC"].apply(perms) #group all permutations per RO
    df2 = df2.reset_index(drop=True) 
elif radio=="None":
    st.write("No Customer Type Selected")


count = df2.groupby(["Service 1","Service 2"]).size() #construct frequency table of each permutation
count = count.to_frame(name = "frequency").reset_index() #convert to dataframe

st.sidebar.subheader("Top service packages")

h = st.sidebar.number_input("Number of Top Services to Return:")

if st.sidebar.button("Run Top Services",key="new3"):
    st.header("Recommended Service Packages")
    st.dataframe(count.sort_values(by="frequency",ascending=False)[1:(int(h)+1)])

st.sidebar.subheader("Top Packages by Service")
i = st.sidebar.number_input("Number of Top Services to Return:",key="Input1")
j = st.sidebar.selectbox("Service Description:",np.sort(df2["Service 1"].unique()))

if st.sidebar.button("Run Packages by Service",key="New4"):
    st.header("Recommended Service Packages")
    st.dataframe(count[count["Service 1"] == j].sort_values(by="frequency",ascending =False)[1:(int(i)+1)])
