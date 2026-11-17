人工智能合作项目会费与服务权益清算账本

运行验收：
python3 -m member_settlement run --fixture fixtures/acceptance.json --database /tmp/member_settlement.sqlite3 --output /tmp/member_settlement-output

核验：
python3 -m member_settlement verify --database /tmp/member_settlement.sqlite3 --output /tmp/member_settlement-output

按账单对账（已收款 / 汇兑差额 / 豁免 / 未结余额）：
python3 -m member_settlement reconcile --database /tmp/member_settlement.sqlite3
python3 -m member_settlement reconcile --database /tmp/member_settlement.sqlite3 --charge charge-001

季度关账（冻结汇率、账单与快照，不可改写）：
python3 -m member_settlement close --database /tmp/member_settlement.sqlite3 --period 2026Q1 --closes-on 2026-03-31

查看期间快照与迟到的更正：
python3 -m member_settlement period --database /tmp/member_settlement.sqlite3 --period 2026Q1

对账口径：
每张账单在结算币下满足
  应收 = 已收款(按账单参考汇率日折算) + 汇兑差额 + 豁免 + 未结余额 - 多收抵扣
缴款保留原币金额、结算币金额、适用汇率与汇率日期；汇兑差额按账单参考汇率日
独立列示，未结余额只包含真正未付的金额。权益按覆盖率比例释放。

迟到更正的约束：
已关闭期间的汇率与账单不可改写；计入已关闭期间的缴款、分配与豁免必须携带
correction_period_id 并登记更正记录；同一缴款对同一账单重复分配不会重复入账。

输出文件：
records.csv、rules.csv、summary.json、decisions.json、audit-events.json、
reconciliation.json、reconciliation.csv、corrections.csv、release-explanations.csv、manifest.json

全量测试：
python3 -m unittest discover -s tests -v

按模块测试：
python3 -m unittest tests.payments.test_reconciliation -v
python3 -m unittest tests.settlement_signal.test_settlement_health -v

构建检查：
python3 -m compileall -q member_settlement tests
