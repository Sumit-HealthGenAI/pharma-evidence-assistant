import requests


def fetch_papers(query, page_size=5):
    """
    Retrieve papers from Europe PMC.

    Returns:
        list: Paper records on success.
        None: If the request or JSON parsing fails.
    """
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()

        return data["resultList"]["result"]

    except requests.exceptions.JSONDecodeError:
        print("The server returned an invalid response.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def normalize_title(title):
    """
    Normalize a title for duplicate detection.

    Note:
    Assumes title is a string. The caller is currently
    responsible for providing a valid string value.
    """
    return title.lower().strip().rstrip(".")


def process_metadata(papers):
    """
    Extract and normalize relevant metadata fields.
    """
    processed_papers = []

    for paper in papers:
        doi = paper.get("doi")
        pmid = paper.get("pmid")

        if doi is not None:
            doi = doi.strip().lower()

            if not doi:
                doi = None

        if pmid is not None:
            pmid = str(pmid).strip()

            if not pmid:
                pmid = None

        processed_papers.append(
            {
                "title": paper.get("title"),
                "authors": paper.get("authorString"),
                "journal": paper.get("journalTitle"),
                "year": paper.get("pubYear"),
                "doi": doi,
                "pmid": pmid,
            }
        )

    return processed_papers


def duplicate_papers(papers):
    """
    Categorize records as:
    - unique_papers
    - confirmed_duplicates
    - possible_duplicates
    - identifier_conflicts

    Limitation:
    DOI/PMID conflict detection uses first-seen mappings.
    Complex chains of conflicting records may not be
    classified perfectly.
    """

    unique_papers = []
    confirmed_duplicates = []
    possible_duplicates = []
    identifier_conflicts = []

    seen_dois = set()
    seen_pmids = set()
    seen_titles = set()

    doi_to_pmid = {}
    pmid_to_doi = {}

    for paper in papers:
        doi = paper.get("doi")
        pmid = paper.get("pmid")
        title = normalize_title(paper.get("title") or "")

        # DOI already seen
        if doi and doi in seen_dois:
            existing_pmid = doi_to_pmid.get(doi)

            if (
                existing_pmid is not None
                and pmid is not None
                and existing_pmid != pmid
            ):
                identifier_conflicts.append(paper)
            else:
                confirmed_duplicates.append(paper)

            continue

        # PMID already seen
        if pmid and pmid in seen_pmids:
            existing_doi = pmid_to_doi.get(pmid)

            if (
                existing_doi is not None
                and doi is not None
                and existing_doi != doi
            ):
                identifier_conflicts.append(paper)
            else:
                confirmed_duplicates.append(paper)

            continue

        # Store new identifiers
        if doi:
            seen_dois.add(doi)
            doi_to_pmid[doi] = pmid

        if pmid:
            seen_pmids.add(pmid)
            pmid_to_doi[pmid] = doi

        # Missing DOI -> title matching
        if not doi:
            if title:
                if title in seen_titles:
                    possible_duplicates.append(paper)
                    continue

                seen_titles.add(title)

            unique_papers.append(paper)
            continue

        # DOI-bearing records remain unique
        # even if titles match.
        if title:
            seen_titles.add(title)

        unique_papers.append(paper)

    return (
        unique_papers,
        confirmed_duplicates,
        possible_duplicates,
        identifier_conflicts,
    )


if __name__ == "__main__":
    papers = [
    {
        "title": "Drug Solubility Research",
        "authorString": "Author A",
        "journalTitle": "Pharma Journal",
        "pubYear": "2026",
        "doi": "10.1000/abc",
        "pmid": "101"
    },
    {
        "title": "Drug Solubility Research Copy",
        "authorString": "Author B",
        "journalTitle": "Pharma Journal",
        "pubYear": "2026",
        "doi": "10.1000/abc",
        "pmid": "101"
    },
    {
        "title": "Another Research Paper",
        "authorString": "Author C",
        "journalTitle": "Pharma Journal",
        "pubYear": "2026",
        "doi": None,
        "pmid": None
    }
]

    if papers is None:
        print("Failed to retrieve papers.")

    else:
        processed_papers = process_metadata(papers)

        (
            unique_papers,
            confirmed_duplicates,
            possible_duplicates,
            identifier_conflicts,
        ) = duplicate_papers(processed_papers)

        print("Original records:", len(processed_papers))
        print("Unique records:", len(unique_papers))
        print("Confirmed duplicates:", len(confirmed_duplicates))
        print("Possible duplicates:", len(possible_duplicates))
        print("Identifier conflicts:", len(identifier_conflicts))