import unittest

from app.governance import Actor, Report, Review, Role, Status


class GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.student = Actor("USN001", Role.STUDENT)
        self.faculty = Actor("faculty-1", Role.FACULTY)
        self.review = Review(Report("USN001", 70, ("resume:1",)))

    def test_draft_not_visible_to_student(self):
        with self.assertRaises(ValueError):
            self.review.published(self.student)

    def test_validation_failure_blocks_approval(self):
        for checks in ({}, {"evidence": False}, {"evidence": "true"}):
            with self.assertRaises(ValueError):
                self.review.submit(checks)
        with self.assertRaises(ValueError):
            self.review.approve(self.faculty)

    def test_student_cannot_approve(self):
        self.review.submit({"evidence": True})
        with self.assertRaises(PermissionError):
            self.review.approve(self.student)

    def test_student_cannot_read_other_student(self):
        self.review.submit({"evidence": True})
        self.review.approve(self.faculty)
        with self.assertRaises(PermissionError):
            self.review.published(Actor("USN002", Role.STUDENT))

    def test_revision_requires_revalidation_and_preserves_published_version(self):
        self.review.submit({"evidence": True})
        self.review.approve(self.faculty)
        self.review.revise(self.faculty, Report("USN001", 80, ("assessment:1",)))
        self.assertEqual(self.review.status, Status.DRAFT)
        self.assertEqual(self.review.published(self.student).score, 70)
        with self.assertRaises(ValueError):
            self.review.approve(self.faculty)
        self.review.submit({"evidence": True})
        self.review.approve(self.faculty)
        self.assertEqual(self.review.published(self.student).score, 80)
        self.review.rollback(self.faculty, 1)
        self.assertEqual(self.review.published(self.student).score, 70)
        self.assertEqual(self.review.events[-1]["action"], "rollback")

    def test_duplicate_approval_rejected(self):
        self.review.submit({"evidence": True})
        self.review.approve(self.faculty)
        with self.assertRaises(ValueError):
            self.review.approve(self.faculty)
        self.assertEqual(len(self.review.versions), 1)

    def test_invalid_score_rejected(self):
        for score in (-1, 101, True, "75"):
            with self.assertRaises(ValueError):
                Report("USN001", score, ("source:1",))


if __name__ == "__main__":
    unittest.main()
