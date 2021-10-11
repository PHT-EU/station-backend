from re import sub
import pandas as pd
from fhirpy import SyncFHIRClient
from datetime import timedelta, datetime
import os
from requests.auth import HTTPBasicAuth
import requests
import asyncio


## Define (input) variables from Docker Container environment variables

fhir_server = str(os.environ['FHIR_SERVER'])
fhir_port = str(os.environ['FHIR_PORT'])
fhir_token = str(os.environ['FHIR_TOKEN'])

#fhir_server = "https://blaze-fhir.personalhealthtrain.de/fhir"
#fhir_port = "443"
#fhir_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ5VmMwcnVQZjdrMDgxN2JWMWF0ZFoycWpJUUFqYnR3RUpiZklvZ3k3aElzIn0.eyJleHAiOjE2MzM0NjQ5NzksImlhdCI6MTYzMzQyODk3OSwianRpIjoiODM3MTExODUtZjljOC00YzVkLTgxNDItMmI3OTY4MTFhOTNiIiwiaXNzIjoiaHR0cHM6Ly9rZXljbG9hay1waHQudGFkYTVoaS5uZXQvYXV0aC9yZWFsbXMvYmxhemUiLCJzdWIiOiI3MmE3ZjM3ZS1iMzNmLTQ5MDgtOWFkOS0zM2JlMGQ0YzE2MjAiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhY2NvdW50IiwiYWNyIjoiMSIsInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50Iiwidmlldy1hcHBsaWNhdGlvbnMiLCJ2aWV3LWNvbnNlbnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsImRlbGV0ZS1hY2NvdW50IiwibWFuYWdlLWNvbnNlbnQiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImVtYWlsIHByb2ZpbGUiLCJjbGllbnRJZCI6ImFjY291bnQiLCJjbGllbnRIb3N0IjoiMTkyLjE2OC4wLjEiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsInByZWZlcnJlZF91c2VybmFtZSI6InNlcnZpY2UtYWNjb3VudC1hY2NvdW50IiwiY2xpZW50QWRkcmVzcyI6IjE5Mi4xNjguMC4xIn0.SgdVj1gdlDrkX7-PYJ3r8351HIVfYOtUsjy_1mX6K6m1vuoZAO4pRS2dEwNI78KxRGB00oD-ClnOICaIrSENwvp4ePavnslqoyy_kbhW2GclfUZgroivln8hCSCjRp9s7Y_mU5entEz-2mnWASN0SrhutvL7iWEj9DVpK5ldAm2c72XAfLF4VqkKkt_poLXnPsEa5C6AoCLharYZLQcthk071qeDLQoJFF2o90jvD1mXK3NAzX6QHbaTNaAZlAxj9VOUqriEcp2EnmXOph1qM_S33cmxi-V33hg9WaC3cRSfy0_4DUWD0w2kruoVD4MVy2tySwD6zb6qQzeFo5MZaw"
print(fhir_server)
print(fhir_port)
print(fhir_token)

## Collect Data Statistic
# Create an instance
client = SyncFHIRClient(url=fhir_server, authorization=f"Bearer {fhir_token}")
# Search for patients
conditions = client.resources('Condition')# Return lazy search set
conditions = conditions.search(code='K85.11').include('Condition', 'subject', 'Patient').fetch_all()

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

df_cfa.to_csv('opt/pht_results/result.csv', mode='a', header=True, index=False)

