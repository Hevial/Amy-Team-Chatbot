from src.models import QueryRequest, QueryResponse, SourceNode


def test_query_request_validation():
    """Test validation of the QueryRequest payload."""
    req = QueryRequest(question="What is the rule?", top_k=3)
    assert req.question == "What is the rule?"
    assert req.top_k == 3
    assert req.enable_google_search is None

    req_with_search = QueryRequest(question="What is the rule?", top_k=3, enable_google_search=True)
    assert req_with_search.enable_google_search is True


def test_source_node_document():
    """Test SourceNode schema for internal document citations."""
    node = SourceNode(source_type="document", text="content snippet", file_name="rules.pdf")
    assert node.source_type == "document"
    assert node.file_name == "rules.pdf"
    assert node.url is None


def test_source_node_web():
    """Test SourceNode schema for web citations."""
    node = SourceNode(
        source_type="web", text="web snippet", title="Official Rules", url="https://example.com"
    )
    assert node.source_type == "web"
    assert node.title == "Official Rules"
    assert node.url == "https://example.com"
    assert node.file_name is None


def test_query_response():
    """Test construction of the QueryResponse payload."""
    resp = QueryResponse(answer="Yes", sources=[], query_time_ms=10.5, llm_model="gemini-2.0-flash")
    assert resp.answer == "Yes"
    assert resp.query_time_ms == 10.5
    assert resp.llm_model == "gemini-2.0-flash"
