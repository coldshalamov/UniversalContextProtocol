"""Tests for the RAFT training data pipeline."""

import pytest
import tempfile
import json
from pathlib import Path

from ucp.config import ToolZooConfig
from ucp.models import ToolSchema
from ucp.tool_zoo import HybridToolZoo
from ucp.raft import RAFTDataGenerator, RAFTTrainer, create_raft_pipeline


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def tool_zoo(temp_dir):
    config = ToolZooConfig(
        persist_directory=str(Path(temp_dir) / "chromadb"),
    )
    zoo = HybridToolZoo(config)
    zoo.initialize()

    # Add sample tools
    tools = [
        ToolSchema(
            name="email.send",
            display_name="send",
            description="Send an email message",
            server_name="email",
        ),
        ToolSchema(
            name="email.read",
            display_name="read",
            description="Read emails from inbox",
            server_name="email",
        ),
        ToolSchema(
            name="github.create_pr",
            display_name="create_pr",
            description="Create a pull request",
            server_name="github",
        ),
        ToolSchema(
            name="calendar.create_event",
            display_name="create_event",
            description="Create calendar event",
            server_name="calendar",
        ),
    ]
    zoo.add_tools(tools)
    return zoo


class TestRAFTDataGenerator:
    """Tests for RAFT data generation."""

    def test_generate_example(self, tool_zoo):
        generator = RAFTDataGenerator(tool_zoo)

        example = generator.generate_example(
            query="Send an email to John",
            candidates=["email.send", "email.read", "github.create_pr"],
            correct=["email.send"],
        )

        assert example["query"] == "Send an email to John"
        assert "email.send" in example["candidates"]
        assert example["correct"] == ["email.send"]
        assert "email.read" in example["distractors"] or "github.create_pr" in example["distractors"]

    def test_generate_negative_example(self, tool_zoo):
        generator = RAFTDataGenerator(tool_zoo)

        example = generator.generate_negative_example(
            query="What is the weather?",
            irrelevant_tools=["email.send", "github.create_pr"],
        )

        assert example["correct"] == []
        assert example["is_negative"] is True
        assert len(example["distractors"]) > 0

    def test_augment_with_paraphrases(self, tool_zoo):
        generator = RAFTDataGenerator(tool_zoo)

        example = generator.generate_example(
            query="send email",
            candidates=["email.send"],
            correct=["email.send"],
        )

        augmented = generator.augment_with_paraphrases(example)

        assert len(augmented) > 0
        # Each augmentation should have different query prefix
        queries = [a["query"] for a in augmented]
        assert len(set(queries)) == len(queries)  # All unique

    def test_export_jsonl(self, tool_zoo, temp_dir):
        generator = RAFTDataGenerator(tool_zoo)

        # Generate some examples
        generator.generate_example(
            query="Send email",
            candidates=["email.send", "email.read"],
            correct=["email.send"],
        )
        generator.generate_example(
            query="Create PR",
            candidates=["github.create_pr"],
            correct=["github.create_pr"],
        )

        output_path = Path(temp_dir) / "training.jsonl"
        count = generator.export_jsonl(output_path)

        assert count == 2
        assert output_path.exists()

        # Verify JSONL format
        with open(output_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            for line in lines:
                data = json.loads(line)
                assert "query" in data
                assert "candidates" in data
                assert "correct" in data

    def test_export_chat_format(self, tool_zoo, temp_dir):
        generator = RAFTDataGenerator(tool_zoo)

        generator.generate_example(
            query="Send email to boss",
            candidates=["email.send", "email.read"],
            correct=["email.send"],
        )

        output_path = Path(temp_dir) / "chat_training.jsonl"
        count = generator.export_chat_format(output_path)

        assert count == 1
        assert output_path.exists()

        # Verify chat format
        with open(output_path) as f:
            line = f.readline()
            data = json.loads(line)
            assert "messages" in data
            assert len(data["messages"]) == 3  # system, user, assistant
            assert data["messages"][0]["role"] == "system"
            assert data["messages"][1]["role"] == "user"
            assert data["messages"][2]["role"] == "assistant"

    def test_get_stats(self, tool_zoo):
        generator = RAFTDataGenerator(tool_zoo)

        # Empty stats
        stats = generator.get_stats()
        assert stats["total"] == 0

        # Add examples
        generator.generate_example(
            query="Send email",
            candidates=["email.send"],
            correct=["email.send"],
        )
        generator.generate_negative_example(
            query="Weather?",
            irrelevant_tools=["email.send"],
        )

        stats = generator.get_stats()
        assert stats["total"] == 2
        assert stats["positive"] == 1
        assert stats["negative"] == 1


class TestRAFTTrainer:
    """Tests for RAFT training pipeline."""

    def test_prepare_dataset(self, tool_zoo, temp_dir):
        generator = RAFTDataGenerator(tool_zoo)
        trainer = RAFTTrainer(generator, output_dir=temp_dir)

        # Create training examples
        training_examples = [
            {
                "query": "Send email",
                "candidates": ["email.send", "email.read"],
                "correct": ["email.send"],
            },
            {
                "query": "Create PR",
                "candidates": ["github.create_pr"],
                "correct": ["github.create_pr"],
            },
            {
                "query": "Schedule meeting",
                "candidates": ["calendar.create_event"],
                "correct": ["calendar.create_event"],
            },
        ]

        train_path, val_path = trainer.prepare_dataset(
            training_examples,
            validation_split=0.2,
            augment=False,  # Disable augmentation for predictable test
        )

        assert train_path.exists()
        assert val_path.exists()

        # Count lines
        with open(train_path) as f:
            train_count = len(f.readlines())
        with open(val_path) as f:
            val_count = len(f.readlines())

        assert train_count + val_count == 3

    def test_generate_training_config(self, tool_zoo, temp_dir):
        generator = RAFTDataGenerator(tool_zoo)
        trainer = RAFTTrainer(generator, output_dir=temp_dir)

        config = trainer.generate_training_config(base_model="test-model")

        assert config["base_model"] == "test-model"
        assert "datasets" in config
        assert "output_dir" in config

        # Check config file was written
        config_path = Path(temp_dir) / "training_config.yaml"
        assert config_path.exists()


class TestCreateRaftPipeline:
    """Test the factory function."""

    def test_create_pipeline(self, tool_zoo):
        generator, trainer = create_raft_pipeline(tool_zoo)

        assert isinstance(generator, RAFTDataGenerator)
        assert isinstance(trainer, RAFTTrainer)
        assert generator.tool_zoo is tool_zoo
