人工智能合作项目会费与服务权益清算账本

运行验收：
python3 -m member_settlement run --fixture fixtures/acceptance.json --database /tmp/member_settlement.sqlite3 --output /tmp/member_settlement-output

核验：
python3 -m member_settlement verify --database /tmp/member_settlement.sqlite3 --output /tmp/member_settlement-output

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.settlement_signal.test_settlement_health -v

构建检查：
python3 -m compileall -q member_settlement tests
