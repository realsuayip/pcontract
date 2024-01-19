import datetime
import unittest

from pcontract.data import Contract, utc


class TestContract(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime.datetime(2022, 10, 10, tzinfo=utc)
        self.end = self.start + datetime.timedelta(days=365)

    def test_contract_init(self):
        data = {"Hello": "world"}
        contract = Contract.init(
            start_at=self.start,
            end_at=self.end,
            data=data,
        )
        self.assertEqual(1, len(contract))
        branch = contract[0]

        self.assertEqual(datetime.timedelta(days=365), branch.span)
        self.assertEqual(data, branch.data)
        self.assertTrue(contract.contains(branch))

    def test_contract_branch_linear(self):
        contract = Contract.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        initial_branch = contract[0]
        branch = contract.branch(
            start_at=self.end,
            data={"key": "venus"},
            end_at=self.end + datetime.timedelta(days=51),
        )

        self.assertEqual(2, len(contract))
        self.assertEqual(datetime.timedelta(days=51), branch.span)
        self.assertTrue(contract.contains(branch))
        self.assertEqual([], initial_branch.replaced_by)
        self.assertEqual([], branch.replaced_by)
        self.assertEqual(contract[1], branch)
        self.assertEqual(
            datetime.timedelta(days=365 + 51),
            branch.span + initial_branch.span,
        )
        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"key": "venus"}, branch.data)

    def test_contract_branch_left(self):
        contract = Contract.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=45),
            data={"key": "venus"},
        )
        initial_branch, left_branch, main_branch = contract
        self.assertEqual(3, len(contract))

        self.assertIn(left_branch.uuid, initial_branch.replaced_by)
        self.assertIn(main_branch.uuid, initial_branch.replaced_by)

        self.assertEqual([], left_branch.replaced_by)
        self.assertEqual([], main_branch.replaced_by)

        self.assertEqual(datetime.timedelta(days=365), initial_branch.span)
        self.assertEqual(datetime.timedelta(days=45), left_branch.span)
        self.assertEqual(datetime.timedelta(days=365 - 45), main_branch.span)

        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"_ref": initial_branch.uuid}, left_branch.data)
        self.assertEqual({"key": "venus"}, main_branch.data)

    def test_contract_branch_right(self):
        contract = Contract.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        contract.branch(
            start_at=self.start,
            end_at=self.start + datetime.timedelta(days=45),
            data={"key": "venus"},
        )
        initial_branch, main_branch, right_branch = contract
        self.assertEqual(3, len(contract))

        self.assertIn(right_branch.uuid, initial_branch.replaced_by)
        self.assertIn(main_branch.uuid, initial_branch.replaced_by)

        self.assertEqual([], right_branch.replaced_by)
        self.assertEqual([], main_branch.replaced_by)

        self.assertEqual(datetime.timedelta(days=365), initial_branch.span)
        self.assertEqual(datetime.timedelta(days=45), main_branch.span)
        self.assertEqual(datetime.timedelta(days=365 - 45), right_branch.span)

        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"key": "venus"}, main_branch.data)
        self.assertEqual({"_ref": initial_branch.uuid}, right_branch.data)

    def test_contract_branch_left_right(self):
        contract = Contract.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=5),
            end_at=self.start + datetime.timedelta(days=45),
            data={"key": "venus"},
        )
        initial_branch, left_branch, main_branch, right_branch = contract
        self.assertEqual(4, len(contract))

        self.assertIn(left_branch.uuid, initial_branch.replaced_by)
        self.assertIn(main_branch.uuid, initial_branch.replaced_by)
        self.assertIn(right_branch.uuid, initial_branch.replaced_by)

        self.assertEqual([], left_branch.replaced_by)
        self.assertEqual([], main_branch.replaced_by)
        self.assertEqual([], right_branch.replaced_by)

        self.assertEqual(datetime.timedelta(days=365), initial_branch.span)
        self.assertEqual(datetime.timedelta(days=5), left_branch.span)
        self.assertEqual(datetime.timedelta(days=40), main_branch.span)
        self.assertEqual(datetime.timedelta(days=365 - 45), right_branch.span)

        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"_ref": initial_branch.uuid}, left_branch.data)
        self.assertEqual({"key": "venus"}, main_branch.data)
        self.assertEqual({"_ref": initial_branch.uuid}, right_branch.data)

    def test_contract_branch_spans_nothing(self):
        contract = Contract.init(
            start_at=self.start, end_at=self.end, data={"key": "world"}
        )

        with self.assertRaisesRegex(ValueError, r".spans nothing"):
            contract.branch(
                start_at=self.start,
                end_at=self.start,
                data={"key": "venus"},
            )

        with self.assertRaisesRegex(ValueError, r".spans nothing"):
            contract.branch(
                start_at=self.start,
                end_at=self.start - datetime.timedelta(days=1),
                data={"key": "venus"},
            )

    def test_contract_branch_span_date_out_of_bound(self):
        contract = Contract.init(
            start_at=self.start, end_at=self.end, data={"key": "world"}
        )

        with self.assertRaisesRegex(ValueError, r".out of the boundary"):
            contract.branch(
                start_at=self.end + datetime.timedelta(days=52),
                data={"key": "venus"},
            )

        with self.assertRaisesRegex(ValueError, r".out of the boundary"):
            contract.branch(
                start_at=self.start - datetime.timedelta(days=52),
                data={"key": "venus"},
            )

    def test_contract_branch_case_no_overlap(self):
        contract = Contract.init(
            start_at=self.start, end_at=self.end, data={"key": "world"}
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=1),
            data={"key": "venus"},
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=3),
            data={"key": "venus"},
        )

        i, l1, m1, l2, m2 = contract
        self.assertEqual(5, len(contract))
        self.assertEqual(datetime.timedelta(days=364), m1.span)
        self.assertEqual(datetime.timedelta(days=1), l1.span)
        self.assertEqual(datetime.timedelta(days=362), m2.span)
        self.assertEqual(datetime.timedelta(days=2), l2.span)

    def test_dataref(self):
        contract = Contract.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=30),
            end_at=self.start + datetime.timedelta(days=60),
            data={"key": "venus"},
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=35),
            end_at=self.start + datetime.timedelta(days=40),
            data={"key": "jupiter"},
        )
        contract.branch(
            start_at=self.start + datetime.timedelta(days=60),
            data={"key": "mars"},
        )

        m0, l1, m1, r1, l2, m2, r2, m3 = contract

        self.assertEqual({"key": "world"}, m0.data)

        self.assertEqual({"_ref": m0.uuid}, l1.data)
        self.assertEqual({"key": "venus"}, m1.data)
        self.assertEqual({"_ref": m0.uuid}, r1.data)

        self.assertEqual({"_ref": m1.uuid}, l2.data)
        self.assertEqual({"key": "jupiter"}, m2.data)
        self.assertEqual({"_ref": m1.uuid}, r2.data)

        self.assertEqual({"key": "mars"}, m3.data)

    def test_contract_init_spans_nothing(self):
        with self.assertRaisesRegex(ValueError, r".spans nothing"):
            Contract.init(
                start_at=self.start,
                end_at=self.start,
                data={"key": "venus"},
            )

        with self.assertRaisesRegex(ValueError, r".spans nothing"):
            Contract.init(
                start_at=self.start,
                end_at=self.start - datetime.timedelta(days=1),
                data={"key": "venus"},
            )
