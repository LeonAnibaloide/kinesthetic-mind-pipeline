+"""Pipeline utilities for the Kinesthetic Mind project."""
+
+import csv
+import json
+import uuid
+from pathlib import Path
+from typing import List, Dict
+
+# Basic text extraction utilities
+try:
+    from PyPDF2 import PdfReader
+except ImportError:  # Fallback if PyPDF2 missing during tests
+    PdfReader = None
+try:
+    import docx2txt
+except ImportError:
+    docx2txt = None
+
+class DeepDocument:
+    """Simple representation of a parsed document."""
+    def __init__(self, title: str, sections: List[Dict]):
+        self.title = title
+        self.sections = sections
+
+    def to_json(self) -> str:
+        return json.dumps({"title": self.title, "sections": self.sections}, indent=2)
+
+
+class DocumentPrepperAgent:
+    """Convert uploaded files into a Deep Document."""
+    def __init__(self, files: List[Dict]):
+        self.files = files
+
+    def _pdf_to_text(self, data: bytes) -> str:
+        if not PdfReader:
+            return ""
+        with open("tmp.pdf", "wb") as f:
+            f.write(data)
+        reader = PdfReader("tmp.pdf")
+        return "\n".join(page.extract_text() or "" for page in reader.pages)
+
+    def _docx_to_text(self, data: bytes) -> str:
+        if not docx2txt:
+            return ""
+        with open("tmp.docx", "wb") as f:
+            f.write(data)
+        return docx2txt.process("tmp.docx")
+
+    def _file_to_text(self, fileobj: Dict) -> str:
+        name = fileobj.get("name")
+        data = fileobj.get("data")
+        if name.endswith(".pdf"):
+            return self._pdf_to_text(data)
+        elif name.endswith(".docx"):
+            return self._docx_to_text(data)
+        else:
+            return data.decode("utf-8", errors="ignore")
+
+    def run(self) -> DeepDocument:
+        text = "\n".join(self._file_to_text(f) for f in self.files)
+        sections = [{"id": str(uuid.uuid4()), "title": "Document", "content": text}]
+        deep = DeepDocument(title="Deep Document", sections=sections)
+        Path("deep_document.json").write_text(deep.to_json())
+        return deep
+
+
+class DocumentParserAgent:
+    """Very lightweight entity and relation extractor."""
+
+    def __init__(self, deep_document: DeepDocument):
+        self.doc = deep_document
+
+    def extract_entities(self):
+        entities = []
+        for sec in self.doc.sections:
+            words = set(sec["content"].split())
+            for w in words:
+                if w.isalpha() and len(w) > 4:
+                    entities.append({"id": w.lower(), "name": w, "section_id": sec["id"]})
+        return entities
+
+    def extract_edges(self, entities):
+        # dummy edges between sequential entities
+        edges = []
+        for i in range(len(entities)-1):
+            src = entities[i]
+            tgt = entities[i+1]
+            edges.append({"source": src["id"], "target": tgt["id"], "section_id": src["section_id"]})
+        return edges
+
+    def run(self):
+        entities = self.extract_entities()
+        edges = self.extract_edges(entities)
+        with open("entities.csv", "w", newline="") as f:
+            writer = csv.DictWriter(f, fieldnames=entities[0].keys())
+            writer.writeheader(); writer.writerows(entities)
+        with open("edges.csv", "w", newline="") as f:
+            writer = csv.DictWriter(f, fieldnames=edges[0].keys())
+            writer.writeheader(); writer.writerows(edges)
+        return entities, edges
+
+
+__all__ = ["DeepDocument", "DocumentPrepperAgent", "DocumentParserAgent"]
