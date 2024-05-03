import typing as typ

import weaviate
import weaviate.classes as wvc


class WeaviateCollection:
    """Adapter for a Weaviate collection."""

    def __init__(self, collection_name: str, *, host: str, port: str, grpc_port: int):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.client = None
        self.collection = None

    def connect(self):
        """Connect to Weaviate."""
        self.client = weaviate.connect_to_local(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
        )

    def create_collection(self):
        """Create a Weaviate collection."""
        self.collection = self.client.collections.create(
            name=self.collection_name,
            vectorizer_config=wvc.config.Configure.Vectorizer.none(),
            vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                distance_metric=wvc.config.VectorDistances.COSINE  # select prefered distance metric
            ),
        )

    def query_near_vector(
        self, query_vector: typ.Sequence[float], *, filters=None, limit=10
    ):
        """Search by query vector."""
        resp = self.collection.query.near_vector(
            near_vector=query_vector,
            limit=limit,
            return_metadata=wvc.query.MetadataQuery(certainty=True),
            filters=filters,
        )
        return resp
