"""Simple Streamlit app for the Kinesthetic Mind pipeline."""

import io
import streamlit as st
from typing import Dict
from pipeline import DocumentPrepperAgent, DocumentParserAgent

st.title("Kinesthetic Mind Pipeline")

st.sidebar.header("Upload Files")
uploaded = st.sidebar.file_uploader("Add research PDFs or docs", accept_multiple_files=True)

if uploaded:
    files = []
    for f in uploaded:
        files.append({"name": f.name, "data": f.read()})
    if st.sidebar.button("Process"):
        st.info("Running Document Prepper...")
        prepper = DocumentPrepperAgent(files)
        deep_doc = prepper.run()
        st.success("Deep Document created")

        st.info("Parsing Document...")
        parser = DocumentParserAgent(deep_doc)
        entities, edges = parser.run()
        st.success(f"Found {len(entities)} entities and {len(edges)} edges")

        with open("entities.csv") as f:
            st.download_button("Download entities.csv", f.read(), file_name="entities.csv")
        with open("edges.csv") as f:
            st.download_button("Download edges.csv", f.read(), file_name="edges.csv")

        st.header("Quick Graph Preview")
        st.json({"entities": entities[:5], "edges": edges[:5]})
else:
    st.write("Upload files to begin.")
