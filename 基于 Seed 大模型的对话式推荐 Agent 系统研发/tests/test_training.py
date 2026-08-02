from seed_rec_agent.models import UserProfile
from seed_rec_agent.sample_data import sample_catalog
from seed_rec_agent.training import JointTokenDatasetBuilder, joint_loss_formula


def test_joint_dataset_contains_item_and_language_tokens():
    example = JointTokenDatasetBuilder().build(UserProfile("u1"), sample_catalog()[:2], "想看历史")
    assert "<COLD_START>" in example.prompt
    assert "<ITEM_i1>" in example.prompt
    assert example.recommendation_tokens
    assert "推荐结果" in example.target


def test_joint_loss():
    assert joint_loss_formula(1, 2, 3) == 1.55

