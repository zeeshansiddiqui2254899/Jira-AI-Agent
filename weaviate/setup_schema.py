import weaviate
import weaviate.classes as wvc
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path('../backend/.env')
load_dotenv(dotenv_path=env_path)

client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    grpc_port=50051
)

# Try to delete existing collection if it exists
try:
    client.collections.delete("JiraIssue")
except Exception:
    pass  # Collection doesn't exist yet, that's fine

try:
    client.collections.create(
        name="JiraIssue",
        generative_config=wvc.config.Configure.Generative.ollama(
            api_endpoint="http://172.17.0.1:11434",
            model="tinyllama"
        ),
        vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(
            inference_url="http://t2v-transformers:8080"
        ),
        properties=[
            wvc.config.Property(name="issueID", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="key", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="project", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="projectName", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="summary", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="status", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="priority", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="labels", data_type=wvc.config.DataType.TEXT_ARRAY),
            wvc.config.Property(name="assignee", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="reporter", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="created", data_type=wvc.config.DataType.DATE),
            wvc.config.Property(name="updated", data_type=wvc.config.DataType.DATE),
            wvc.config.Property(name="resolutionDate", data_type=wvc.config.DataType.DATE),
            wvc.config.Property(name="customFields", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="attachments", data_type=wvc.config.DataType.TEXT_ARRAY),
            wvc.config.Property(
                name="comments",
                data_type=wvc.config.DataType.OBJECT_ARRAY,
                nested_properties=[
                    wvc.config.Property(name="commentID", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="author", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="body", data_type=wvc.config.DataType.TEXT),
                    wvc.config.Property(name="created", data_type=wvc.config.DataType.DATE),
                    wvc.config.Property(name="updated", data_type=wvc.config.DataType.DATE)
                ]
            )
        ]
    )
finally:
    client.close()