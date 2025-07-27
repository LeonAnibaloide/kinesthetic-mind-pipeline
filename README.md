 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index d3e07adb974ede1ab60cddc259599d3e0fa5f7b6..1fe167be6ec52224ff6d0756f4dc061a1e144558 100644
--- a/README.md
+++ b/README.md
@@ -9,26 +9,28 @@ Develop a pipeline for transforming complex deep research documents into intuiti
 ## Pipeline Steps
 
 1. **Deep Research Chat**: Upload your research notes and documents to `data/`.
 2. **Document Prepper Agent**: Standardizes documents into a structured Deep Document.
 3. **Document Parser Agent**: Extracts entities, connections, aliases, and indices; outputs JSON/CSV.
 4. **Neo4j Graph Builder**: Visualizes outputs as interactive graphs.
 
 ## How to Use
 
 1. Clone this repo.
 2. Add your research files to `data/`.
 3. Open `kinesthetic_pipeline_nb.ipynb` in Jupyter Lab/Notebook.
 4. Follow instructions in each step.
 
 ## Requirements
 
 Install dependencies with:
 
 ```bash
 pip install -r requirements.txt
 ```
 
 ## Notes
 
 - Do **not** upload private or copyrighted research files.
-- The `data/` and `output/` folders are gitignored for privacy and size.
+- The `data/` and `output/` folders are gitignored for privacy and size.
+## Web App
+Run `streamlit run webapp.py` to launch a simple interface for uploading documents and generating CSV outputs.
 
EOF
)
