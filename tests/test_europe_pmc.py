from europe_pmc import duplicate_papers, process_metadata, fetch_papers
from unittest.mock import patch, Mock

import requests


def test_process_metadata():
    paper = {
        "title": "Drug Solubility",
        "authorString": "Author A",
        "journalTitle": "Pharma Journal",
        "pubYear": "2026",
        "doi": " 10.1000/ABC ",
        "pmid": 101
    }

    result = process_metadata([paper])

    assert result[0]["title"] == "Drug Solubility"
    assert result[0]["authors"] == "Author A"
    assert result[0]["journal"] == "Pharma Journal"
    assert result[0]["year"] == "2026"
    assert result[0]["doi"] == "10.1000/abc"
    assert result[0]["pmid"] == "101"
    assert isinstance(result[0]["pmid"], str)

def test_process_metadata_missing_fields():
    paper = {
        "title": "Drug Solubility"
    }

    result = process_metadata([paper])

    assert result[0]["title"] == "Drug Solubility"
    assert result[0]["authors"] is None
    assert result[0]["journal"] is None
    assert result[0]["year"] is None
    assert result[0]["doi"] is None
    assert result[0]["pmid"] is None

def test_duplicate_papers_same_doi():
    papers = [
        {
            "title": "Drug Solubility Research",
            "doi": "10.1000/abc",
            "pmid": "101"
        },
        {
            "title": "Solubility of Pharmaceutical Compounds",
            "doi": "10.1000/abc",
            "pmid": "101"
        }
    ]

    unique, confirmed, possible, conflicts = duplicate_papers(papers)

    assert len(unique) == 1
    assert len(confirmed) == 1
    assert len(possible) == 0
    assert len(conflicts) == 0

def test_duplicate_papers_possible_duplicate():
    papers = [
        {
            "title": "Drug Solubility Research",
            "doi": None,
            "pmid": None
        },
        {
            "title": "Drug Solubility Research",
            "doi": None,
            "pmid": None
        }
    ]

    unique, confirmed, possible, conflicts = duplicate_papers(papers)

    assert len(unique) == 1
    assert len(confirmed) == 0
    assert len(possible) == 1
    assert len(conflicts) == 0

def test_duplicate_papers_different_dois():
    papers = [
        {
            "title": "Drug Solubility Research",
            "doi": "10.1000/abc",
            "pmid": "101"
        },
        {
            "title": "Drug Solubility Research",
            "doi": "10.2000/xyz",
            "pmid": "202"
        }
    ]

    unique, confirmed, possible, conflicts = duplicate_papers(papers)

    assert len(unique) == 2
    assert len(confirmed) == 0
    assert len(possible) == 0
    assert len(conflicts) == 0


def test_fetch_papers_success():
    mock_data = {
        "resultList": {
            "result": [
                {
                    "title": "Paper One",
                    "doi": "10.1000/abc"
                },
                {
                    "title": "Paper Two",
                    "doi": "10.2000/xyz"
                }
            ]
        }
    }

    mock_response = Mock()
    mock_response.json.return_value = mock_data
    mock_response.raise_for_status.return_value = None

    with patch("europe_pmc.requests.get") as mock_get:
        mock_get.return_value = mock_response

        results = fetch_papers(
            "drug solubility",
            page_size=2
        )
    assert results == mock_data["resultList"]["result"]
    assert results is not None
    assert len(results) == 2

    mock_get.assert_called_once()
    mock_get.assert_called_once_with(
    "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
    params={
        "query": "drug solubility",
        "format": "json",
        "pageSize": 2
    },
    timeout=15
)

def test_fetch_papers_request_failure():
    with patch("europe_pmc.requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        results = fetch_papers("drug solubility")

    assert results is None


def test_fetch_papers_unexpected_response_structure():
    mock_response = Mock()

    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "message": "Request successful"
    }

    with patch("europe_pmc.requests.get") as mock_get:
        mock_get.return_value = mock_response

        results = fetch_papers(
            "drug solubility",
            page_size=2
        )

    assert results is None

def test_fetch_papers_invalid_json():
    mock_response = Mock()

    # HTTP request succeeds
    mock_response.raise_for_status.return_value = None

    # JSON parsing fails
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
        "Invalid JSON",
        "invalid response",
        0,
    )

    with patch("europe_pmc.requests.get") as mock_get:
        mock_get.return_value = mock_response

        results = fetch_papers(
            "drug solubility",
            page_size=2,
        )

    assert results is None


def test_fetch_papers_empty_results():
    mock_response = Mock()

    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "resultList": {
            "result": []
        }
    }

    with patch("europe_pmc.requests.get") as mock_get:
        mock_get.return_value = mock_response

        results = fetch_papers(
            "drug solubility",
            page_size=2
        )

    assert results == []
    assert results is not None
