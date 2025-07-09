# Kinesthetic Mind Project Pipeline
# Jupyter Notebook Structure

# --- Step 1: Deep Research Chat ---
# Markdown:
"""
### Step 1: Deep Research Chat

Upload your deep research chat logs and associated preliminary documents here. Ensure the files are clearly labeled for easy identification.
"""

# Code:
from ipywidgets import FileUpload

upload = FileUpload(accept='.pdf,.docx,.txt', multiple=True)
display(upload)

# --- Step 2: Document Prepper Agent ---
# Markdown:
"""
### Step 2: Document Prepper Agent

The Document Prepper Agent standardizes uploaded documents into a structured Deep Document. It will create a comprehensive scientific dictionary, annotate entities and connections, and standardize citations.

Implement the Document Prepper logic below.
"""
# --- requirements (once per environment) ---
# pip install pypdf python-docx beautifulsoup4 rake-nltk scispacy ipywidgets neo4j openai pydantic

from pathlib import Path
import re, json, uuid, tempfile
from typing import List, Dict
from pydantic import BaseModel
from rake_nltk import Rake
import openai, os
import docx2txt
from PyPDF2 import PdfReader

class Section(BaseModel):
    id: str
    title: str
    level: int
    content: str

class DeepDocument(BaseModel):
    title: str
    sections: List[Section]
    dictionary: Dict[str,str]
    bibliography: List[str]

class DocumentPrepperAgent:
    def __init__(self, files, model="gpt-4o-mini"):
        self.files = files
        self.model = model
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def _file_to_text(self, fileobj):
        name = fileobj['metadata']['name']
        data = fileobj['content']
        if name.endswith(".pdf"):
            reader = PdfReader(Path(tempfile.mktemp()))
            with open(reader.stream.name, "wb") as f:
                f.write(data)
            return "\n".join(p.extract_text() for p in reader.pages)
        elif name.endswith(".docx"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(data)
                tmp.flush()
                return docx2txt.process(tmp.name)
        else:                       # txt
            return data.decode('utf-8', errors='ignore')

    def clean_text(self):
        texts = [self._file_to_text(f) for f in self.files]
        return "\n".join(texts)

    def detect_headers(self, blob):
        sections, current, lvl = [], [], 1
        for line in blob.splitlines():
            if re.match(r"^[A-Z][A-Za-z0-9 ,\-]{3,}$", line.strip()):
                if current:
                    sections.append(Section(id=str(uuid.uuid4()), title=header, level=lvl, content="\n".join(current)))
                header, current = line.strip(), []
                lvl = header.count(".")+1
            else:
                current.append(line)
        if current:
            sections.append(Section(id=str(uuid.uuid4()), title=header, level=lvl, content="\n".join(current)))
        return sections

    def build_dictionary(self, text, top_k=30):
        rake = Rake()
        rake.extract_keywords_from_text(text)
        keywords = [k for k,_ in rake.get_ranked_phrases_with_scores()[:top_k]]
        prompt = f"Provide concise scientific definitions (max 25 words) for:\n{keywords}"
        resp = openai.ChatCompletion.create(model=self.model, messages=[{"role":"user","content":prompt}])
        definitions = resp.choices[0].message.content.strip().split("\n")
        return {k.strip(): d.strip() for k,d in (l.split("–") if "–" in l else l.split(":") for l in definitions)}

    def standardize_citations(self, text):
        # naive numeric mapping
        apa_cites = re.findall(r"\(([^)]+, \d{4})\)", text)
        mapping = {c:i+1 for i,c in enumerate(dict.fromkeys(apa_cites))}
        def repl(m): return f"[{mapping[m.group(1)]}]"
        return re.sub(r"\(([^)]+, \d{4})\)", repl, text), [c for c in mapping]

    def run(self):
        blob = self.clean_text()
        sections = self.detect_headers(blob)
        cleaned, bibliography = self.standardize_citations(blob)
        dictionary = self.build_dictionary(cleaned)
        doc = DeepDocument(title="Deep Document", sections=sections,
                           dictionary=dictionary, bibliography=bibliography)
        Path("deep_document.json").write_text(doc.json(indent=2))
        Path("deep_document.md").write_text(cleaned)
        return doc

# --- Execute (if you want automatic run when cell executed) ---
# prepper = DocumentPrepperAgent(upload.value)
# deep_doc = prepper.run()
# print("✅ Deep Document created -> deep_document.*")


# --- Step 3: Document Parser Agent ---
# Markdown:
"""
### Step 3: Document Parser Agent

The Document Parser Agent extracts entities, connections, aliases, and indices from the Deep Document. Outputs will be provided as JSON and CSV files.

Implement the Document Parser logic below.
"""

import scispacy, spacy, csv, json
import networkx as nx
from collections import defaultdict

nlp = spacy.load("en_core_sci_md")  # scispaCy model

class DocumentParserAgent:
    def __init__(self, deep_doc_path="deep_document.json"):
        self.doc = DeepDocument.parse_file(deep_doc_path)

    def extract_entities(self):
        entities = []
        alias_map = {}
        for sec in self.doc.sections:
            doc = nlp(sec.content)
            for ent in doc.ents:
                ent_id = f"{ent.text.lower()}_{ent.label_}"
                entities.append({"id": ent_id, "name": ent.text,
                                 "label": ent.label_, "section_id": sec.id})
                # alias rule of thumb
                if ent.text.lower() not in alias_map:
                    alias_map[ent.text.lower()] = set()
                alias_map[ent.text.lower()].add(ent.text)
        return entities, {k:list(v) for k,v in alias_map.items()}

    def extract_edges(self, entities):
        G = nx.Graph()
        for e in entities:
            G.add_node(e["id"], label=e["label"])
        # simple co-occurrence per sentence
        for sec in self.doc.sections:
            for sent in nlp(sec.content).sents:
                ents = [e for e in sent.ents if e.text.lower()+"_"+e.label_ in G]
                for i,src in enumerate(ents):
                    for tgt in ents[i+1:]:
                        G.add_edge(src.text.lower()+"_"+src.label_,
                                   tgt.text.lower()+"_"+tgt.label_, section=sec.id)
        edges = [{"source":u, "target":v, "section_id":d["section"]}
                 for u,v,d in G.edges(data=True)]
        return edges

    def export(self, entities, edges, aliases):
        with open("entities.csv","w",newline='') as f:
            writer = csv.DictWriter(f, fieldnames=entities[0].keys())
            writer.writeheader(); writer.writerows(entities)
        with open("edges.csv","w",newline='') as f:
            writer = csv.DictWriter(f, fieldnames=edges[0].keys())
            writer.writeheader(); writer.writerows(edges)
        json.dump(aliases, open("aliases.json","w"), indent=2)

    def run(self):
        entities, aliases = self.extract_entities()
        edges = self.extract_edges(entities)
        self.export(entities, edges, aliases)
        return entities, edges, aliases

# --- Execute ---
# parser = DocumentParserAgent()
# ents, eds, aliases = parser.run()
# print("✅ Parsed outputs saved (entities.csv, edges.csv, aliases.json)")


# --- Step 4: Neo4j Graph Builder ---
# Markdown:
"""
### Step 4: Neo4j Graph Builder

Here, use the output from the Document Parser Agent to build an interactive RAG graph with Neo4j.

Implement graph-building logic or output handling below.
"""

from neo4j import GraphDatabase, RoutingControl
import pandas as pd, os, itertools, json

class Neo4jGraphBuilder:
    def __init__(self, uri=os.getenv("NEO4J_URI"), user=os.getenv("NEO4J_USER"),
                 password=os.getenv("NEO4J_PASS")):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def _load_csv(self, path):
        return list(csv.DictReader(open(path)))

    def ingest(self, node_file="entities.csv", edge_file="edges.csv"):
        nodes = self._load_csv(node_file)
        edges = self._load_csv(edge_file)
        with self.driver.session(database="neo4j") as sess:
            # index
            sess.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
            # nodes
            for chunk in [nodes[i:i+100] for i in range(0,len(nodes),100)]:
                sess.run("""
                UNWIND $batch AS row
                MERGE (e:Entity {id: row.id})
                SET e.name = row.name, e.label = row.label
                """, batch=chunk, routing_=RoutingControl.READ)
            # edges
            for chunk in [edges[i:i+100] for i in range(0,len(edges),100)]:
                sess.run("""
                UNWIND $batch AS row
                MATCH (a:Entity {id: row.source})
                MATCH (b:Entity {id: row.target})
                MERGE (a)-[:CO_OCCURS {section_id: row.section_id}]->(b)
                """, batch=chunk, routing_=RoutingControl.READ)
        print("🚀 Graph imported to Neo4j!")

# --- Execute ---
# builder = Neo4jGraphBuilder()
# builder.ingest()

