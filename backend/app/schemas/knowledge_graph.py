from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    document_count: int


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    document_id: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ExtractEntitiesResponse(BaseModel):
    document_id: str
    entities_found: int
    relations_found: int
