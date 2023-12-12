"""test_odcs_fetcher.py - test odcs_fetcher"""
from pathlib import Path

import responses

from generate_compose.odcs_fetcher import ODCSFetcher
from generate_compose.odcs_requester import ODCSRequestReference


def test_odcs_fetcher(tmp_path: Path) -> None:
    """test ODCSFetcher.__call__"""
    expected_content: str = """
    [odcs-2222222]
    name=ODCS repository for compose odcs-2222222
    baseurl=http://download.eng.bos.redhat.com/odcs/prod/odcs-2222222/compose/Temporary/$basearch/os
    type=rpm-md
    skip_if_unavailable=False
    gpgcheck=0
    repo_gpgcheck=0
    enabled=1
    enabled_metadata=1
    """
    mock_compose_url: str = (
        "http://download.eng.bos.redhat.com/odcs/prod/odcs-222222"
        "/compose/Temporary/odcs-2222222.repo"
    )
    odcs_ref = ODCSRequestReference(compose_url=mock_compose_url)

    compose_path = tmp_path / "downloaded_file_dir" / "odcs-2222222.repo"
    odcs_fetcher = ODCSFetcher(compose_file_path=compose_path)

    with responses.RequestsMock() as req_mock:
        req_mock.add(responses.GET, mock_compose_url, body=expected_content)
        odcs_result_ref = odcs_fetcher(request_reference=odcs_ref)

    assert odcs_result_ref.compose_file_path.exists()
    odcs_result_ref_content = odcs_result_ref.compose_file_path.read_text(
        encoding="utf-8"
    )
    assert odcs_result_ref_content == expected_content
