from nassbot_app.utils.utils import pretty_log
from nassbot_app.utils.log_utils import log_event

from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.llms import OpenAI

from nassbot_app.utils import vecstore


def qanda_langchain(query: str, request_id=None, with_logging=False) -> str:
    """Runs sourced Q&A for a query using LangChain.

    Arguments:
        query: The query to run Q&A on.
        request_id: A unique identifier for the request.
        with_logging: If True, logs the interaction to Gantry.
    """

    embedding_engine = vecstore.get_embedding_engine(allowed_special="all")

    pretty_log("connecting to vector storage")
    vector_index = vecstore.connect_to_vector_index(
        vecstore.INDEX_NAME, embedding_engine
    )
    pretty_log("connected to vector storage")

    pretty_log(f"running on query: {query}")
    pretty_log("selecting sources by similarity to query")
    sources = vector_index.similarity_search(query, k=5)

    if with_logging:
        pretty_log("SOURCES")
        print(*[source.page_content for source in sources], sep="\n\n---\n\n")

    pretty_log("running query against Q&A chain")

    llm = OpenAI(model_name="text-davinci-003", temperature=0)
    chain = load_qa_with_sources_chain(llm, chain_type="stuff")

    result = chain(
        {"input_documents": sources, "question": query}, return_only_outputs=True
    )
    answer = result["output_text"]

    if with_logging:
        print(answer)
        pretty_log("logging results to gantry")
        record_key = log_event(query, sources, answer, request_id=request_id)
        pretty_log(f"logged to gantry with key {record_key}")

    return answer
