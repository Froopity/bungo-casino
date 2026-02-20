import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from casino.utils import calculate_net_debts, generate_debt_graph_image


def _mock_urlopen(content=b'PNG', status=200):
  response = MagicMock()
  response.status = status
  response.read.return_value = content
  response.__enter__ = MagicMock(return_value=response)
  response.__exit__ = MagicMock(return_value=False)
  return response


class TestCalculateNetDebts:
  def test_empty(self):
    assert calculate_net_debts([]) == []

  def test_simple_single_debt(self):
    result = calculate_net_debts([('Alice', 'Bob', 3)])
    assert result == [('Alice', 'Bob', 3)]

  def test_mutual_debt_nets_down(self):
    result = calculate_net_debts([('Alice', 'Bob', 3), ('Bob', 'Alice', 1)])
    assert len(result) == 1
    debtor, creditor, amount = result[0]
    assert debtor == 'Alice'
    assert creditor == 'Bob'
    assert amount == 2

  def test_mutual_debt_cancels(self):
    result = calculate_net_debts([('Alice', 'Bob', 2), ('Bob', 'Alice', 2)])
    assert result == []

  def test_multiple_independent_pairs(self):
    edges = [('Alice', 'Bob', 3), ('Charlie', 'Bob', 1)]
    result = calculate_net_debts(edges)
    assert len(result) == 2

  def test_accumulates_multiple_edges_same_pair(self):
    edges = [('Alice', 'Bob', 1), ('Alice', 'Bob', 2)]
    result = calculate_net_debts(edges)
    assert result == [('Alice', 'Bob', 3)]


class TestGenerateDebtGraphImage:
  def _decode_mermaid(self, mock_open):
    req = mock_open.call_args[0][0]
    url = req.full_url
    encoded = url.split('/img/')[1].split('?')[0]
    padding = '=' * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding).decode('utf-8')

  def _get_url(self, mock_open):
    return mock_open.call_args[0][0].full_url

  def test_returns_file_path_on_success(self):
    with patch('urllib.request.urlopen', return_value=_mock_urlopen()):
      result = generate_debt_graph_image([('Alice', 'Bob', 3)])

    assert result is not None
    assert os.path.exists(result)
    os.unlink(result)

  def test_returns_none_on_network_failure(self):
    with patch('urllib.request.urlopen', side_effect=Exception('network error')):
      result = generate_debt_graph_image([('Alice', 'Bob', 3)])

    assert result is None

  def test_mermaid_contains_node_names(self):
    with patch('urllib.request.urlopen', return_value=_mock_urlopen()) as mock_open:
      generate_debt_graph_image([('Alice', 'Bob', 3)])

    mermaid = self._decode_mermaid(mock_open)
    print('mermaid code:\n', mermaid)
    assert 'Alice' in mermaid
    assert 'Bob' in mermaid

  def test_mermaid_contains_debt_amount(self):
    with patch('urllib.request.urlopen', return_value=_mock_urlopen()) as mock_open:
      generate_debt_graph_image([('Alice', 'Bob', 3)])

    mermaid = self._decode_mermaid(mock_open)
    print('mermaid code:\n', mermaid)
    assert '$3' in mermaid

  def test_mutual_debt_is_netted_in_graph(self):
    with patch('urllib.request.urlopen', return_value=_mock_urlopen()) as mock_open:
      generate_debt_graph_image([('Alice', 'Bob', 3), ('Bob', 'Alice', 1)])

    mermaid = self._decode_mermaid(mock_open)
    print('mermaid code:\n', mermaid)
    assert '$2' in mermaid
    assert '$3' not in mermaid
    assert '$1' not in mermaid

  def test_url_format(self):
    with patch('urllib.request.urlopen', return_value=_mock_urlopen()) as mock_open:
      generate_debt_graph_image([('Alice', 'Bob', 1)])

    url = self._get_url(mock_open)
    print('request url:', url)
    assert url.startswith('https://mermaid.ink/img/')
    assert 'bgColor=faf0d2' in url

  @pytest.mark.integration
  def test_real_mermaid_ink_request(self, caplog):
    import logging
    with caplog.at_level(logging.DEBUG, logger='casino.utils'):
      result = generate_debt_graph_image([('Alice', 'Bob', 2), ('Charlie', 'Alice', 1)])

    print('logs:\n', caplog.text)
    print('result path:', result)
    if result and os.path.exists(result):
      size = os.path.getsize(result)
      print('file size:', size)
      os.unlink(result)
      assert size > 0, 'image file is empty'
    else:
      pytest.fail('generate_debt_graph_image returned None - check logs above')
