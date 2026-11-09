"""create_transdata_view が DEFINER を固定しないことを確認する（接続は行わない）。

root 以外の MySQL ユーザーで実行すると DEFINER=`root`@`%` が 1449 エラーになるため、
DEFINER 句は省いて MySQL の既定（実行ユーザー）に任せる。
"""
from VC_BC02_baseUtils import DatabaseManager


def test_view_has_no_fixed_definer(monkeypatch):
    sent = []
    monkeypatch.setattr(DatabaseManager, "execute_query", lambda self, q, values=None: sent.append(q))
    db = object.__new__(DatabaseManager)  # __init__ を呼ばず、DB に接続しない
    db.create_transdata_view("v", "m", "c")
    assert "DEFINER=`root`" not in sent[0]
    assert "CREATE OR REPLACE" in sent[0]
