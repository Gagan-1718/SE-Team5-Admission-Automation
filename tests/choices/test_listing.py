from app.accounts.models import ExamRecord
from app.choices.models import Choice
from app.choices.services import list_choices, preview_choice
from app.extensions import db


def test_list_choices_is_priority_ordered_and_contains_catalogue_preview(app, choice_data):
    candidate_id = choice_data["candidate_ids"][0]
    first_id, second_id = choice_data["branch_ids"][:2]
    with app.app_context():
        record = ExamRecord(exam_type="KCET", rank=1000, category="General", score=185)
        db.session.add(record)
        db.session.flush()
        from app.accounts.models import User
        candidate = db.session.get(User, candidate_id)
        candidate.exam_record_id = record.id
        candidate.rank = record.rank
        candidate.category = record.category
        db.session.add_all([
            Choice(candidate_id=candidate.id, branch_id=second_id, priority=2),
            Choice(candidate_id=candidate.id, branch_id=first_id, priority=1),
        ])
        db.session.commit()

        choices = list_choices(candidate.id)
        assert [choice.branch_id for choice in choices] == [first_id, second_id]
        preview = preview_choice(choices[0], candidate.id)
        assert preview["college"] == "Fictional Institute"
        assert preview["city"] == "Bengaluru"
        assert preview["branch"] == "Computer Science"
        assert preview["seatsAvailable"] == 8
        assert preview["seatCapacity"] == 10


def test_preview_keeps_zero_category_availability_visible(app, choice_data):
    candidate_id = choice_data["candidate_ids"][0]
    branch_id = choice_data["branch_ids"][1]
    with app.app_context():
        db.session.add(Choice(candidate_id=candidate_id, branch_id=branch_id, priority=1))
        db.session.commit()
        preview = preview_choice(list_choices(candidate_id)[0], candidate_id)
        assert preview["seatsAvailable"] == 0
        assert preview["seatCapacity"] == 0


def test_empty_choice_list_is_supported(app, choice_data):
    with app.app_context():
        assert list_choices(choice_data["candidate_ids"][0]) == []
