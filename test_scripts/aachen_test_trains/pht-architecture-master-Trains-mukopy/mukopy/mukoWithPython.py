from re import sub
import pandas as pd
from fhirpy import SyncFHIRClient
from datetime import timedelta, datetime
import os



## Define (input) variables from Docker Container environment variables
fhir_server = str(os.environ['FHIR_SERVER'])
fhir_port = str(os.environ['FHIR_PORT'])
# fhir_server = "137.226.232.119"
# fhir_port = "8080"



## Collect Data Statistic
# Create an instance
client = SyncFHIRClient('http://{}:{}/fhir'.format(fhir_server, fhir_port))
# Search for patients
conditions = client.resources('Condition')# Return lazy search set
conditions = conditions.search(code='O80,O80 Z37.0!').include('Condition', 'subject', 'Patient').fetch_all()

condition_data = []
patientIDs = []
for condition in conditions:
    category = None
    try:
        diagnose = condition.code.text
        category = condition.category
    except:
        pass

    if diagnose == "CF-Geburt":
        condition_data.append(
            [condition.id, condition.subject.reference.replace("Patient/", ""), condition.code.coding[0].code, category,
             condition.code.text])
        patientIDs.append(condition.subject.reference.replace("Patient/", ""))

#print(condition_data)
condition_df = pd.DataFrame(condition_data, columns=["condition_id", "patient_id", "secode", "diagtext1", "diagtext2"])



patients = client.resources('Patient')  # Return lazy search set
patientIDString = ','.join(patientIDs)
patients = patients.search(_id=patientIDString)
patients_data = []

for patient in patients:
    PID = patient.id
    PID = PID.replace("Patient/", "")
    patients_data.append([PID, patient.meta.source, patient.gender, patient.birthDate, patient.address[0].postalCode])



#print(patients_data)
patients_df = pd.DataFrame(patients_data, columns=["patient_id", "source", "geschlecht", "gebd", "plz"])

data_df = pd.merge(patients_df, condition_df, on='patient_id', how='outer')

data_df = data_df.drop(columns=["patient_id","plz","condition_id", "diagtext1"])

data_df['secode'] = data_df['secode'].apply(lambda x: x.replace("/","//"))

data_df['secode'] = data_df['secode'].apply(lambda x: sub("([/]/.*)", "", x))

data_df['secode'] = data_df['secode'].apply(lambda x: sub("\\..*",",-",x))


data_df.loc[(data_df['geschlecht'] == "female"),'geschlecht'] = "f"
data_df.loc[(data_df['geschlecht'] == "male"),'geschlecht'] = "m"
data_df.loc[(data_df['geschlecht'] == ""),'geschlecht'] = "NA"
data_df['source'] = data_df['source'].apply(lambda x: sub("#.*","",x))



data_df['age'] = data_df['gebd'].apply(lambda x: (datetime.today() - datetime.strptime(x, "%Y-%m-%d")) // timedelta(days=365.2425))
data_df = data_df.drop(columns=["gebd"])


bins= [1,10,20,30,40,50,60,70,80,90,999]
labels = ["(1,10]","(11,20]", "(21,30]", "(31,40]", "(41,50]", "(51,60]","(61,70]","(71,80]","(81,90]", "(91,999]"]
data_df['age'] = pd.cut(data_df['age'], bins=bins, labels=labels, right=False)


data_df = data_df.groupby(['source','secode','diagtext2', 'geschlecht', 'age']).size().reset_index(name='count')
data_df = data_df[data_df["count"] > 0]


data_df.loc[(data_df['secode'] == "O80 Z37,-"),'secode'] = "O80"

df_cfa = data_df.rename(columns={'source': 'Einrichtungsidentifikator', 'secode': 'AngabeDiagn2', 'geschlecht': 'AngabeGeschlecht', 'age': 'AngabeAlter', 'diagtext2': 'TextDiagnose2', 'count': 'Anzahl'})
df_cfa = df_cfa.drop(columns=["TextDiagnose2"])





df_cfa["AngabeDiagn1"] = "E84,-"
df_cfa = df_cfa[['Einrichtungsidentifikator', 'AngabeDiagn1', 'AngabeDiagn2', 'AngabeGeschlecht', 'AngabeAlter', 'Anzahl']]

#print(df_cfa.to_string())

df_cfa.to_csv('result.csv', mode='a', header=True, index=False)


