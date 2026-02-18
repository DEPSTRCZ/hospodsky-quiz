import streamlit as st
import pandas as pd
import base64
from io import StringIO



st.title("Hospodský Quiz")
st.divider()

st.write("TMP storage")
st.write(st.query_params)

#data = pd.DataFrame(index=pd.Index([], name="Název týmu"), columns=["Žolík"]).astype({"Žolík": bool})
EMPTY_DATA = pd.DataFrame(index=pd.Index([], name="Název týmu"), columns=["Žolík"]).astype({"Žolík": bool})

def SaveToQueryParams(data):
    print(data.to_json(orient="index", force_ascii=False))
    st.query_params["data"] = base64.b64encode(data.to_json(orient="index", force_ascii=False).encode('utf-8')).decode()

def GetDataFromQueryParams():
    if "data" in st.query_params:
        decoded = base64.b64decode(st.query_params["data"]).decode()
        loaded = pd.read_json(StringIO(decoded), orient="index")
        if "Žolík" in loaded.columns:
            loaded["Žolík"] = loaded["Žolík"].astype("boolean").fillna(False)
        else:
            loaded["Žolík"] = False
        return loaded
    else:
        return EMPTY_DATA



def SetupPage():
    st.title("Nastavení nové hry")

    edited_data = st.data_editor(EMPTY_DATA, num_rows="dynamic", key="data_editor",hide_index=False,disabled=["Žolík"])

    
    if st.button("Začít hru"):
        SaveToQueryParams(edited_data)
        st.query_params["round"] = "1"
        st.rerun()


def RoundPage(round_number):
    st.title(f"Kolo {round_number}")
    st.write("Tady bude obsah kola")
    new_data = GetDataFromQueryParams()

    # If there is not a column for the current round, add it
    if f"Kolo {round_number}" not in new_data.columns:
        new_data[f"Kolo {round_number}"] = 0
        SaveToQueryParams(new_data)

    round_data_editor = st.data_editor(new_data, num_rows="dynamic", key="round_data_editor",hide_index=False)
    
    # Save the edited data
    if not round_data_editor.equals(new_data):
        SaveToQueryParams(round_data_editor)


    col1, col2 = st.columns(2)
    with col2:
        if st.button("Přejít na další kolo",type="secondary"):
            st.query_params["round"] = str(round_number + 1)
            st.rerun()
    with col1:
        if st.button("Ukončit a zobrazit výsledky",type="primary"):
            st.query_params.pop("round", None)
            st.rerun()
if "round" in st.query_params:
    RoundPage(int(st.query_params["round"]))
elif "data" not in st.query_params:
    SetupPage()


if st.button("Decode data from query params"):
    edited_data2 = st.data_editor(GetDataFromQueryParams(), num_rows="dynamic", key="data_editor",hide_index=False)
    st.write(GetDataFromQueryParams())