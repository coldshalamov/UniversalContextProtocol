"""
RAFT (Retrieval-Augmented Fine-Tuning) Pipeline.

This module implements the training data generation and fine-tuning
pipeline for improving UCP's tool selection over time.

Based on the Gorilla RAFT paper: teach the model to distinguish
between relevant and irrelevant retrieved tools.

Training data format:
{
    "query": "User's conversation context",
    "candidates": ["tool1", "tool2", "tool3"],  # Retrieved tools
    "correct": ["tool1"],  # Actually used tools
    "distractors": ["tool2", "tool3"]  # Retrieved but unused
}
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from ucp.models import ToolSchema
from ucp.tool_zoo import ToolZoo

logger = structlog.get_logger(__name__)


class RAFTDataGenerator:
    """
    Generates training data for RAFT fine-tuning.

    The key insight from Gorilla: models need to learn to *ignore*
    irrelevant tools, not just find relevant ones. This requires
    training with distractors.
    """

    def __init__(
        self,
        tool_zoo: ToolZoo,
        distractor_ratio: float = 0.5,
        max_distractors: int = 5,
    ) -> None:
        self.tool_zoo = tool_zoo
        self.distractor_ratio = distractor_ratio
        self.max_distractors = max_distractors
        self._training_examples: list[dict] = []

    def generate_example(
        self,
        query: str,
        candidates: list[str],
        correct: list[str],
    ) -> dict:
        """
        Generate a single training example with distractors.

        Args:
            query: The conversation context
            candidates: Tools that were retrieved
            correct: Tools that were actually used
        """
        # Identify distractors (retrieved but not used)
        distractors = [c for c in candidates if c not in correct]

        # Optionally add more random distractors
        if random.random() < self.distractor_ratio:
            all_tools = self.tool_zoo.get_all_tools()
            random_tools = random.sample(
                [t.name for t in all_tools if t.name not in candidates],
                min(self.max_distractors, len(all_tools) - len(candidates)),
            )
            distractors.extend(random_tools)

        example = {
            "query": query,
            "candidates": candidates + distractors[:self.max_distractors],
            "correct": correct,
            "distractors": distractors[:self.max_distractors],
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._training_examples.append(example)
        return example

    def generate_negative_example(self, query: str, irrelevant_tools: list[str]) -> dict:
        """
        Generate a negative example where no tools should be selected.

        This teaches the model to say "none of these are relevant".
        """
        example = {
            "query": query,
            "candidates": irrelevant_tools,
            "correct": [],  # Empty - no tools should be selected
            "distractors": irrelevant_tools,
            "is_negative": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._training_examples.append(example)
        return example

    def augment_with_paraphrases(self, example: dict) -> list[dict]:
        """
        Augment training data with paraphrased queries.

        This increases diversity without needing more real examples.
        """
        # Simple augmentation patterns
        augmentations = []
        query = example["query"]

        # Add prefix variations
        prefixes = [
            "I need to ",
            "Can you help me ",
            "Please ",
            "I want to ",
            "Help me ",
        ]

        for prefix in prefixes:
            if not query.lower().startswith(prefix.lower()):
                augmented = example.copy()
                augmented["query"] = prefix + query[0].lower() + query[1:]
                augmented["is_augmented"] = True
                augmentations.append(augmented)

        return augmentations

    def export_jsonl(self, output_path: str | Path) -> int:
        """
        Export training data in JSONL format (one JSON per line).

        This format is compatible with most fine-tuning frameworks.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            for example in self._training_examples:
                f.write(json.dumps(example) + "\n")

        logger.info("raft_data_exported", path=str(output_path), count=len(self._training_examples))
        return len(self._training_examples)

    def export_chat_format(self, output_path: str | Path) -> int:
        """
        Export in chat/instruction format for LLM fine-tuning.

        Format:
        System: You are a tool selector. Given a query and list of tools,
                select only the relevant tools.
        User: Query: [query]
              Available tools: [tool1, tool2, ...]
        Assistant: Selected tools: [correct1, correct2]
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        system_prompt = (
            "You are a tool selection assistant. Given a user query and a list "
            "of available tools, select ONLY the tools that are directly relevant "
            "to completing the user's request. If no tools are relevant, respond "
            "with 'None'. Do not select tools just because they are vaguely related."
        )

        chat_examples = []

        for example in self._training_examples:
            # Format tool list with descriptions
            tool_list = []
            for tool_name in example["candidates"]:
                tool = self.tool_zoo.get_tool(tool_name)
                if tool:
                    tool_list.append(f"- {tool_name}: {tool.description}")
                else:
                    tool_list.append(f"- {tool_name}")

            user_content = f"Query: {example['query']}\n\nAvailable tools:\n" + "\n".join(tool_list)

            if example["correct"]:
                assistant_content = "Selected tools: " + ", ".join(example["correct"])
            else:
                assistant_content = "Selected tools: None"

            chat_examples.append({
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content},
                ]
            })

        with open(output_path, "w") as f:
            for example in chat_examples:
                f.write(json.dumps(example) + "\n")

        logger.info("chat_data_exported", path=str(output_path), count=len(chat_examples))
        return len(chat_examples)

    def get_stats(self) -> dict:
        """Get statistics about collected training data."""
        if not self._training_examples:
            return {"total": 0}

        positive = sum(1 for e in self._training_examples if e.get("correct"))
        negative = sum(1 for e in self._training_examples if not e.get("correct"))
        augmented = sum(1 for e in self._training_examples if e.get("is_augmented"))

        avg_candidates = sum(len(e["candidates"]) for e in self._training_examples) / len(self._training_examples)
        avg_correct = sum(len(e["correct"]) for e in self._training_examples) / len(self._training_examples)

        return {
            "total": len(self._training_examples),
            "positive": positive,
            "negative": negative,
            "augmented": augmented,
            "avg_candidates": avg_candidates,
            "avg_correct": avg_correct,
        }

    def clear(self) -> None:
        """Clear collected training data."""
        self._training_examples.clear()


class RAFTTrainer:
    """
    Manages the RAFT training pipeline.

    This is a placeholder for actual fine-tuning integration.
    In practice, you would export data and use an external
    framework (transformers, axolotl, etc.) for training.
    """

    def __init__(
        self,
        data_generator: RAFTDataGenerator,
        output_dir: str = "./data/raft",
    ) -> None:
        self.data_generator = data_generator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_dataset(
        self,
        training_examples: list[dict],
        validation_split: float = 0.1,
        augment: bool = True,
    ) -> tuple[Path, Path]:
        """
        Prepare training and validation datasets.

        Returns paths to the generated files.
        """
        # Add examples to generator
        for example in training_examples:
            self.data_generator.generate_example(
                query=example["query"],
                candidates=example["candidates"],
                correct=example["correct"],
            )

        # Optionally augment
        if augment:
            original_examples = self.data_generator._training_examples.copy()
            for example in original_examples:
                augmented = self.data_generator.augment_with_paraphrases(example)
                self.data_generator._training_examples.extend(augmented)

        # Shuffle
        all_examples = self.data_generator._training_examples.copy()
        random.shuffle(all_examples)

        # Split
        split_idx = int(len(all_examples) * (1 - validation_split))
        train_examples = all_examples[:split_idx]
        val_examples = all_examples[split_idx:]

        # Export
        train_path = self.output_dir / "train.jsonl"
        val_path = self.output_dir / "val.jsonl"

        with open(train_path, "w") as f:
            for example in train_examples:
                f.write(json.dumps(example) + "\n")

        with open(val_path, "w") as f:
            for example in val_examples:
                f.write(json.dumps(example) + "\n")

        logger.info(
            "dataset_prepared",
            train_count=len(train_examples),
            val_count=len(val_examples),
            train_path=str(train_path),
            val_path=str(val_path),
        )

        return train_path, val_path

    def generate_training_config(self, base_model: str = "meta-llama/Llama-3-8B") -> dict:
        """
        Generate a training configuration for use with training frameworks.

        This outputs a config compatible with axolotl or similar.
        """
        config = {
            "base_model": base_model,
            "model_type": "LlamaForCausalLM",
            "tokenizer_type": "LlamaTokenizer",
            "load_in_8bit": True,
            "datasets": [
                {
                    "path": str(self.output_dir / "train.jsonl"),
                    "type": "completion",
                }
            ],
            "val_set_size": 0.1,
            "output_dir": str(self.output_dir / "model"),
            "sequence_len": 2048,
            "lora_r": 8,
            "lora_alpha": 16,
            "lora_dropout": 0.05,
            "gradient_accumulation_steps": 4,
            "micro_batch_size": 2,
            "num_epochs": 3,
            "learning_rate": 2e-4,
            "warmup_ratio": 0.1,
            "optimizer": "adamw_torch",
            "lr_scheduler": "cosine",
            "bf16": True,
            "gradient_checkpointing": True,
        }

        config_path = self.output_dir / "training_config.yaml"

        import yaml
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        logger.info("training_config_generated", path=str(config_path))

        return config


def create_raft_pipeline(tool_zoo: ToolZoo) -> tuple[RAFTDataGenerator, RAFTTrainer]:
    """
    Factory function to create a complete RAFT pipeline.

    Usage:
        generator, trainer = create_raft_pipeline(tool_zoo)

        # Collect data from router
        generator.generate_example(query, candidates, correct)

        # When ready to train
        train_path, val_path = trainer.prepare_dataset(
            router.export_training_data()
        )
    """
    generator = RAFTDataGenerator(tool_zoo)
    trainer = RAFTTrainer(generator)

    return generator, trainer
