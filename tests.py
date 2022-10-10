import datetime
import unittest

from pcontract.data import Collection, utc


class TestCollection(unittest.TestCase):
    def setUp(self) -> None:
        self.start = datetime.datetime(2022, 10, 10, tzinfo=utc)
        self.end = self.start + datetime.timedelta(days=365)

    def test_collection_init(self):
        data = {"Hello": "world"}
        collection = Collection.init(
            start_at=self.start,
            end_at=self.end,
            data=data,
        )
        self.assertEqual(1, len(collection))
        branch = collection[0]

        self.assertEqual(datetime.timedelta(days=365), branch.span)
        self.assertEqual(data, branch.data)
        self.assertTrue(collection.contains(branch))

    def test_collection_branch_linear(self):
        collection = Collection.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        initial_branch = collection[0]
        branch = collection.branch(
            start_at=self.end,
            data={"key": "venus"},
            end_at=self.end + datetime.timedelta(days=51),
        )

        self.assertEqual(2, len(collection))
        self.assertEqual(datetime.timedelta(days=51), branch.span)
        self.assertTrue(collection.contains(branch))
        self.assertEqual([], initial_branch.replaced_by)
        self.assertEqual([], branch.replaced_by)
        self.assertEqual(collection[1], branch)
        self.assertEqual(
            datetime.timedelta(days=365 + 51),
            branch.span + initial_branch.span,
        )
        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"key": "venus"}, branch.data)

    def test_collection_branch_left(self):
        collection = Collection.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        collection.branch(
            start_at=self.start + datetime.timedelta(days=45),
            data={"key": "venus"},
        )
        initial_branch, left_branch, main_branch = collection
        self.assertEqual(3, len(collection))

        self.assertIn(left_branch, initial_branch.replaced_by)
        self.assertIn(main_branch, initial_branch.replaced_by)

        self.assertEqual([], left_branch.replaced_by)
        self.assertEqual([], main_branch.replaced_by)

        self.assertEqual(datetime.timedelta(days=365), initial_branch.span)
        self.assertEqual(datetime.timedelta(days=45), left_branch.span)
        self.assertEqual(datetime.timedelta(days=365 - 45), main_branch.span)

        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"key": "world"}, left_branch.data)
        self.assertEqual({"key": "venus"}, main_branch.data)

    def collection_branch_right(self):
        collection = Collection.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        collection.branch(
            start_at=self.start,
            end_at=self.start + datetime.timedelta(days=45),
            data={"key": "venus"},
        )
        initial_branch, main_branch, right_branch = collection
        self.assertEqual(3, len(collection))

        self.assertIn(right_branch, initial_branch.replaced_by)
        self.assertIn(main_branch, initial_branch.replaced_by)

        self.assertEqual([], right_branch.replaced_by)
        self.assertEqual([], main_branch.replaced_by)

        self.assertEqual(datetime.timedelta(days=365), initial_branch.span)
        self.assertEqual(datetime.timedelta(days=45), right_branch.span)
        self.assertEqual(datetime.timedelta(days=365 - 45), main_branch.span)

        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"key": "venus"}, right_branch.data)
        self.assertEqual({"key": "venus"}, main_branch.data)

    def test_collection_branch_left_right(self):
        collection = Collection.init(
            start_at=self.start,
            end_at=self.end,
            data={"key": "world"},
        )
        collection.branch(
            start_at=self.start + datetime.timedelta(days=5),
            end_at=self.start + datetime.timedelta(days=45),
            data={"key": "venus"},
        )
        initial_branch, left_branch, main_branch, right_branch = collection
        self.assertEqual(4, len(collection))

        self.assertIn(left_branch, initial_branch.replaced_by)
        self.assertIn(main_branch, initial_branch.replaced_by)
        self.assertIn(right_branch, initial_branch.replaced_by)

        self.assertEqual([], left_branch.replaced_by)
        self.assertEqual([], main_branch.replaced_by)
        self.assertEqual([], right_branch.replaced_by)

        self.assertEqual(datetime.timedelta(days=365), initial_branch.span)
        self.assertEqual(datetime.timedelta(days=5), left_branch.span)
        self.assertEqual(datetime.timedelta(days=40), main_branch.span)
        self.assertEqual(datetime.timedelta(days=365 - 45), right_branch.span)

        self.assertEqual({"key": "world"}, initial_branch.data)
        self.assertEqual({"key": "world"}, left_branch.data)
        self.assertEqual({"key": "venus"}, main_branch.data)
        self.assertEqual({"key": "world"}, right_branch.data)

    def test_collection_branch_spans_nothing(self):
        collection = Collection.init(
            start_at=self.start, end_at=self.end, data={"key": "world"}
        )

        with self.assertRaisesRegex(ValueError, r".spans nothing"):
            collection.branch(
                start_at=self.start,
                end_at=self.start,
                data={"key": "venus"},
            )

        with self.assertRaisesRegex(ValueError, r".spans nothing"):
            collection.branch(
                start_at=self.start,
                end_at=self.start - datetime.timedelta(days=1),
                data={"key": "venus"},
            )

    def test_collection_branch_span_date_out_of_bound(self):
        collection = Collection.init(
            start_at=self.start, end_at=self.end, data={"key": "world"}
        )

        with self.assertRaisesRegex(ValueError, r".out of the boundary"):
            collection.branch(
                start_at=self.end + datetime.timedelta(days=52),
                data={"key": "venus"},
            )

        with self.assertRaisesRegex(ValueError, r".out of the boundary"):
            collection.branch(
                start_at=self.start - datetime.timedelta(days=52),
                data={"key": "venus"},
            )

    def test_collection_branch_case_no_overlap(self):
        collection = Collection.init(
            start_at=self.start, end_at=self.end, data={"key": "world"}
        )
        collection.branch(
            start_at=self.start + datetime.timedelta(days=1),
            data={"key": "venus"},
        )
        collection.branch(
            start_at=self.start + datetime.timedelta(days=3),
            data={"key": "venus"},
        )

        i, l1, m1, l2, m2 = collection
        self.assertEqual(5, len(collection))
        self.assertEqual(datetime.timedelta(days=364), m1.span)
        self.assertEqual(datetime.timedelta(days=1), l1.span)
        self.assertEqual(datetime.timedelta(days=362), m2.span)
        self.assertEqual(datetime.timedelta(days=2), l2.span)
