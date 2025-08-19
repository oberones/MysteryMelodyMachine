from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional
import yaml

class MidiConfig(BaseModel):
    input_port: str = "auto"
    output_port: Optional[str] = None  # Optional MIDI output port
    channel: int = 1

class SequencerConfig(BaseModel):
    steps: int = 8
    bpm: float = 110.0
    swing: float = 0.12
    density: float = 0.85
    quantize_scale_changes: str = Field("bar", pattern=r"^(immediate|bar)$")

class MutationConfig(BaseModel):
    interval_min_s: int = 120
    interval_max_s: int = 240
    max_changes_per_cycle: int = 2

class IdleConfig(BaseModel):
    timeout_ms: int = 30000
    ambient_profile: str = "slow_fade"
    fade_in_ms: int = 4000
    fade_out_ms: int = 800

class SynthConfig(BaseModel):
    backend: str = Field("supercollider", pattern=r"^(supercollider)$")
    voices: int = 8

class LoggingConfig(BaseModel):
    level: str = Field("INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

class ApiConfig(BaseModel):
    enabled: bool = True
    port: int = 8080

class RootConfig(BaseModel):
    midi: MidiConfig = MidiConfig()
    mapping: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    sequencer: SequencerConfig = SequencerConfig()
    scales: List[str] = Field(default_factory=lambda: ["major", "minor", "pentatonic"])
    mutation: MutationConfig = MutationConfig()
    idle: IdleConfig = IdleConfig()
    synth: SynthConfig = SynthConfig()
    logging: LoggingConfig = LoggingConfig()
    api: ApiConfig = ApiConfig()

    @field_validator("scales")
    @classmethod
    def non_empty_scales(cls, v):
        if not v:
            raise ValueError("At least one scale must be defined")
        return v


def load_config(path: str) -> RootConfig:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return RootConfig(**data)

