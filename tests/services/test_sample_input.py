from backend.rag.chunker import chunk_text


def test_sample_clinical_text_is_split_into_expected_chunks() -> None:
    sample_text = (
        "Study objective: evaluate safety and efficacy of a diabetes therapy. "
        "Patient population: adults with type 2 diabetes. "
        "Primary endpoint: change in HbA1c at 24 weeks. "
        "Risk factors: hypoglycemia and injection-site reactions were monitored."
    )

    chunks = chunk_text(sample_text, doc_id="sample", chunk_size=120, chunk_overlap=20)

    assert len(chunks) == 2
    assert chunks[0].doc_id == "sample"
    assert "Study objective" in chunks[0].text
    assert chunks[1].start_char == 100
